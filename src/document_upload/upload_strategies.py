"""
Document Upload Strategies
=========================

Strategy pattern implementation for document upload operations.
This module provides upload strategies for different vector search services.

Similar to the processing strategies pattern, this allows for:
1. Service-agnostic upload interface
2. Service-specific optimizations and error handling  
3. Easy addition of new vector search services
4. Consistent result reporting across all services
"""

import asyncio
import logging
import os
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from dotenv import load_dotenv

from .processing_strategies import DocumentProcessingStrategy, ProcessedDocument

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


@dataclass
class DocumentUploadResult:
    """Standardized result object for document upload operations."""
    total_search_objects: int
    successfully_uploaded: int
    failed_uploads: int
    upload_time: float
    errors: List[str]
    strategy_name: str
    upload_metadata: Optional[Dict[str, Any]] = None


class DocumentUploadStrategy(ABC):
    """Abstract base class for all document upload strategies."""
    
    @property
    @abstractmethod
    def strategy_name(self) -> str:
        """Return the name of this upload strategy."""
        pass
    
    @abstractmethod
    async def upload_documents(self, processed_documents: List[ProcessedDocument], 
                             tracker=None, **kwargs) -> DocumentUploadResult:
        """
        Upload processed documents using this strategy.
        
        Args:
            processed_documents: List of processed documents from processing phase
            tracker: DocumentProcessingTracker instance for marking files as processed
            **kwargs: Additional strategy-specific parameters
            
        Returns:
            DocumentUploadResult: Upload results with statistics and errors
        """
        pass
    
    @abstractmethod
    async def delete_all_documents_from_service(self) -> int:
        """
        Delete all documents from the search service.
        
        Returns:
            Number of documents deleted from the service
        """
        pass


class AzureCognitiveSearchUploadStrategy(DocumentUploadStrategy):
    """Upload strategy for Azure Cognitive Search."""
    
    def __init__(self, processing_strategy: DocumentProcessingStrategy=None):
        """
        Initialize the Azure Cognitive Search upload strategy.
        
        Automatically loads configuration from environment variables:
        - AZURE_SEARCH_SERVICE_NAME
        - AZURE_SEARCH_ADMIN_KEY  
        - AZURE_SEARCH_INDEX_NAME
        
        Args:
            processing_strategy: Processing strategy to use for creating search objects
        """
        # Load configuration from environment variables
        self.service_name = os.getenv('AZURE_SEARCH_SERVICE_NAME')
        self.admin_key = os.getenv('AZURE_SEARCH_ADMIN_KEY')
        self.index_name = os.getenv('AZURE_SEARCH_INDEX_NAME')
        
        # Validate required environment variables
        if not all([self.service_name, self.admin_key, self.index_name]):
            missing_vars = []
            if not self.service_name:
                missing_vars.append('AZURE_SEARCH_SERVICE_NAME')
            if not self.admin_key:
                missing_vars.append('AZURE_SEARCH_ADMIN_KEY')
            if not self.index_name:
                missing_vars.append('AZURE_SEARCH_INDEX_NAME')
            
            raise ValueError(f"Missing required Azure Search environment variables: {', '.join(missing_vars)}")
        
        self.processing_strategy = processing_strategy
        self._azure_search_service = None
        
        logger.info(f"Azure Cognitive Search Upload Strategy initialized:")
        logger.info(f"   - Service Name: {self.service_name}")
        logger.info(f"   - Index Name: {self.index_name}")
        logger.info(f"   - Processing Strategy: {self.processing_strategy.__class__.__name__ if self.processing_strategy else 'None'}")
        
    @property
    def strategy_name(self) -> str:
        return "Azure Cognitive Search Upload Strategy"
    
    @property
    def azure_search_service(self):
        """Lazy initialization of Azure Search service."""
        if self._azure_search_service is None:
            from src.common.vector_search_services.azure_cognitive_search import get_azure_search_service
            self._azure_search_service = get_azure_search_service(
                self.service_name, self.admin_key, self.index_name
            )
        return self._azure_search_service
    
    async def upload_documents(self, processed_documents: List[ProcessedDocument], 
                             tracker=None, **kwargs) -> DocumentUploadResult:
        """
        Upload processed documents to Azure Cognitive Search.
        
        This method processes each document individually:
        1. Creates search index objects with embeddings for each document
        2. Uploads the objects to Azure Cognitive Search immediately
        3. Marks successfully uploaded files as processed in the tracker immediately
        
        Args:
            processed_documents: List of processed documents from processing phase
            tracker: DocumentProcessingTracker instance for marking files as processed
            **kwargs: Additional parameters (unused for Azure strategy)
            
        Returns:
            DocumentUploadResult: Upload results with statistics and errors
        """
        start_time = datetime.now()
        total_search_objects = 0
        successfully_uploaded = 0
        failed_uploads = 0
        errors = []
        successfully_uploaded_files = []
        failed_upload_files = []
        
        logger.info(f"Uploading {len(processed_documents)} processed documents to Azure Search...")
        print(f"📤 Uploading {len(processed_documents)} processed documents to Azure Search...")
        
        # Process each document individually
        for doc_idx, processed_doc in enumerate(processed_documents, 1):
            try:
                print(f"📄 Document {doc_idx}/{len(processed_documents)}: {processed_doc.file_name}")
                
                # Create search index objects for this document
                print(f"🔄 Creating search objects with embeddings...")
                
                # Collect search objects for this document
                doc_search_objects = []
                if self.processing_strategy:
                    async for search_object in self.processing_strategy.create_search_index_objects([processed_doc]):
                        doc_search_objects.append(search_object)
                else:
                    logger.error("No processing strategy provided for creating search objects")
                    errors.append(f"Document {doc_idx} ({processed_doc.file_name}): No processing strategy available")
                    failed_upload_files.append(Path(processed_doc.file_path))
                    continue
                
                doc_total_objects = len(doc_search_objects)
                total_search_objects += doc_total_objects
                
                print(f"      📊 Generated {doc_total_objects} search objects")
                
                if doc_search_objects:
                    # Upload this document's search objects to Azure Search
                    print(f"      📤 Uploading {doc_total_objects} objects to Azure Search...", end=" ")
                    
                    successful, failed = self.azure_search_service.upload_search_objects_batch(doc_search_objects)
                    
                    successfully_uploaded += successful
                    failed_uploads += failed
                    
                    if failed > 0:
                        error_msg = f"Document {doc_idx} ({processed_doc.file_name}): {failed}/{doc_total_objects} objects failed to upload"
                        errors.append(error_msg)
                        print(f"⚠️  ({successful} succeeded, {failed} failed)")
                        failed_upload_files.append(Path(processed_doc.file_path))
                    else:
                        print("✅")
                        successfully_uploaded_files.append(Path(processed_doc.file_path))
                        
                        # Mark file as processed immediately after successful upload
                        if tracker is not None:
                            tracker.mark_processed(Path(processed_doc.file_path), processed_doc.metadata)
                            print(f"      📋 Marked as processed in tracker")
                else:
                    error_msg = f"Document {doc_idx} ({processed_doc.file_name}): No search objects generated"
                    errors.append(error_msg)
                    print(f"      ❌ No search objects generated")
                    failed_upload_files.append(Path(processed_doc.file_path))
                    
            except Exception as e:
                error_msg = f"Document {doc_idx} ({processed_doc.file_name}): Upload error - {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)
                print(f"      ❌ Error: {str(e)}")
                # Count all potential objects from this document as failed
                failed_uploads += processed_doc.chunk_count  # Estimate based on chunk count
                failed_upload_files.append(Path(processed_doc.file_path))
        
        # Save tracker after all uploads are complete
        if tracker is not None and successfully_uploaded_files:
            tracker.save()
            print(f"   📋 Saved tracker with {len(successfully_uploaded_files)} successfully processed files")
        
        upload_time = (datetime.now() - start_time).total_seconds()
        
        # Create upload metadata
        upload_metadata = {
            "documents_processed": len(processed_documents),
            "documents_successfully_uploaded": len(successfully_uploaded_files),
            "documents_failed_upload": len(failed_upload_files),
            "azure_service_name": self.service_name,
            "azure_index_name": self.index_name
        }
        
        logger.info(f"Upload completed: {successfully_uploaded}/{total_search_objects} objects uploaded successfully")
        
        return DocumentUploadResult(
            total_search_objects=total_search_objects,
            successfully_uploaded=successfully_uploaded,
            failed_uploads=failed_uploads,
            upload_time=upload_time,
            errors=errors,
            strategy_name=self.strategy_name,
            upload_metadata=upload_metadata
        )
    
    async def delete_all_documents_from_service(self) -> int:
        """
        Delete all documents from Azure Cognitive Search service.
        
        Returns:
            Number of documents deleted from the service
        """
        try:
            logger.info("Deleting all documents from Azure Cognitive Search service...")
            print(f"   🗑️  Deleting all documents from Azure Search service...")
            
            deleted_count = self.azure_search_service.delete_all_documents()
            
            if deleted_count > 0:
                logger.info(f"Successfully deleted {deleted_count} documents from Azure Search")
                print(f"   ✅ Deleted {deleted_count} documents from Azure Search")
            else:
                logger.info("No documents found to delete from Azure Search")
                print(f"   ℹ️  No documents found to delete from Azure Search")
            
            return deleted_count
            
        except Exception as e:
            error_msg = f"Error deleting documents from Azure Search: {str(e)}"
            logger.error(error_msg)
            print(f"   ❌ {error_msg}")
            return 0