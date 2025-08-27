"""
Document Processing Pipeline
===========================

A comprehensive pipeline for processing documents into Azure Cognitive Search objects.
The pipeline consists of three main phases:

1. Document Discovery Phase - Find and gather all relevant document files
2. Document Processing Phase - Extract metadata and prepare search objects  
3. Search Index Upload Phase - Upload processed documents to Azure Cognitive Search

This modular approach allows for better separation of concerns and easier maintenance.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Iterator, Any
from dataclasses import dataclass

# Import our helper modules
import sys
sys.path.append(str(Path(__file__).parent.parent))

from document_upload.discovery_strategies import DocumentDiscoveryStrategy, DocumentDiscoveryResult
from document_upload.processing_strategies import DocumentProcessingStrategy, ProcessedDocument, DocumentProcessingResult
from document_upload.upload_strategies import DocumentUploadStrategy, DocumentUploadResult

# Import Azure search service for upload phase
from src.common.vector_search_services.azure_cognitive_search import get_azure_search_service


class DocumentDiscoveryPhase:
    """
    Phase 1: Document Discovery
    
    Responsible for finding and gathering all relevant document files
    from the specified directory structure using configurable discovery strategies.
    """
    
    def __init__(self, discovery_strategy: DocumentDiscoveryStrategy = None):
        """
        Initialize the document discovery phase.
        
        Args:
            discovery_strategy: Strategy to use for document discovery (default: PersonalDocumentationDiscoveryStrategy)
        """
        if discovery_strategy is not None:
            self.discovery_strategy = discovery_strategy
        else:
            # Use PersonalDocumentationDiscoveryStrategy as default
            from document_upload.discovery_strategies import PersonalDocumentationDiscoveryStrategy
            self.discovery_strategy = PersonalDocumentationDiscoveryStrategy()
    
    def discover_documents(self, root_directory: str, **kwargs) -> DocumentDiscoveryResult:
        """
        Discover all documents in the specified directory using the configured strategy.
        
        Args:
            root_directory: Root directory to search
            **kwargs: Additional strategy-specific parameters (recursive, max_files, etc.)
            
        Returns:
            DocumentDiscoveryResult: Discovery results with file list and statistics
        """
        start_time = datetime.now()
        errors = []
        
        try:
            # Standard discovery using the strategy
            raw_result = self.discovery_strategy.discover_documents(root_directory, **kwargs)
            discovery_time = (datetime.now() - start_time).total_seconds()
            
            # Parse the result using the strategy
            parsed_result = self.discovery_strategy.parse_result(
                discovery_result=raw_result,
                discovery_time=discovery_time,
                errors=errors,
                **kwargs
            )
            
            return parsed_result
            
        except Exception as e:
            discovery_time = (datetime.now() - start_time).total_seconds()
            errors.append(f"Discovery failed: {str(e)}")
            
            # Create a default empty result
            return DocumentDiscoveryResult(
                total_files=0,
                files_by_type={},
                discovered_files=[],
                discovery_time=discovery_time,
                errors=errors,
                strategy_name=self.discovery_strategy.get_strategy_name(),
                strategy_metadata=None
            )
    
    def print_discovery_summary(self, result: DocumentDiscoveryResult):
        """Print a summary of the discovery phase results."""
        print(f"\n📁 Document Discovery Phase Complete")
        print(f"   Strategy: {result.strategy_name}")
        print(f"   Total files found: {result.total_files}")
        print(f"   Discovery time: {result.discovery_time:.2f} seconds")
        
        if result.files_by_type:
            print(f"   File types:")
            for file_type, count in result.files_by_type.items():
                print(f"     {file_type}: {count} files")
        
        # Show strategy-specific metadata for Personal Documentation Assistant
        if result.strategy_metadata and result.strategy_name == "PersonalDocumentationAssistant":
            metadata = result.strategy_metadata
            
            if metadata.get('targeted_discovery'):
                requested_work_items = metadata.get('work_items_requested', [])
                found_work_items = metadata.get('work_items_found', [])
                file_count = metadata.get('work_items_file_count', {})
                
                print(f"   🎯 Targeted Work Item Discovery:")
                print(f"     Requested: {len(requested_work_items)} work items")
                if requested_work_items:
                    print(f"     Work items: {', '.join(requested_work_items)}")
                
                print(f"     Found: {len(found_work_items)} work items with files")
                if found_work_items:
                    print(f"     Work items with files:")
                    for work_item in found_work_items:
                        count = file_count.get(work_item, 0)
                        print(f"       • {work_item}: {count} files")
            else:
                found_work_items = metadata.get('work_items_found', [])
                if found_work_items:
                    print(f"   📋 Work Items Discovered: {len(found_work_items)} work items")
                    # Show first few work items
                    sample_items = found_work_items[:5]
                    print(f"     Sample: {', '.join(sample_items)}")
                    if len(found_work_items) > 5:
                        print(f"     ... and {len(found_work_items) - 5} more")
        
        if result.errors:
            print(f"   Errors: {len(result.errors)}")
            for error in result.errors:
                print(f"     - {error}")


class DocumentProcessingPhase:
    """
    Phase 2: Document Processing
    
    Responsible for processing documents using configurable processing strategies.
    Different strategies can create different types of processed documents and
    Azure Cognitive Search index objects.
    """
    
    def __init__(self, processing_strategy: DocumentProcessingStrategy = None):
        """
        Initialize the document processing phase.
        
        Args:
            processing_strategy: Strategy to use for document processing (default: PersonalDocumentationAssistantAzureCognitiveSearchProcessingStrategy)
        """
        if processing_strategy is not None:
            self.strategy = processing_strategy
        else:
            # Use PersonalDocumentationAssistantAzureCognitiveSearchProcessingStrategy as default
            from document_upload.processing_strategies import PersonalDocumentationAssistantAzureCognitiveSearchProcessingStrategy
            self.strategy = PersonalDocumentationAssistantAzureCognitiveSearchProcessingStrategy()

    def process_documents(self, discovered_files: List[Path]) -> DocumentProcessingResult:
        """
        Process all discovered documents using the configured strategy.
        
        Each document from the discovery phase is individually processed to extract
        metadata, generate chunks, and prepare for search index upload.
        
        Args:
            discovered_files: List of file paths from discovery phase
            
        Returns:
            DocumentProcessingResult: Processing results with processed documents
        """
        print(f"   📋 Processing {len(discovered_files)} discovered documents...")
        
        # Process each discovered document individually
        result = self.strategy.process_documents(discovered_files)
        
        # Log per-document processing results
        if result.processed_documents:
            print(f"   📄 Document processing breakdown:")
            for i, doc in enumerate(result.processed_documents, 1):
                print(f"      {i:2d}. {doc.file_name}")
                print(f"          └─ Chunks: {doc.chunk_count}, Context: {doc.context_name}")
        
        return result
    
    def create_search_index_objects(self, processed_documents: List[ProcessedDocument]) -> Iterator[Dict]:
        """
        Create Azure Cognitive Search index objects using the configured strategy.
        
        Args:
            processed_documents: List of processed documents
            
        Yields:
            Dict: Search index object for Azure Cognitive Search
        """
        # IMPORTANT: Using yield here implements a generator pattern for memory efficiency
        # 
        # Why yield is crucial for this pipeline:
        # 1. MEMORY EFFICIENCY: Instead of creating all search objects in memory at once
        #    (which could be 100+ documents × 3-5 objects each = 300-500+ objects),
        #    yield returns objects one at a time, keeping memory usage minimal
        #
        # 2. STREAMING PROCESSING: The upload phase can process and upload objects
        #    immediately as they're generated, rather than waiting for all objects
        #    to be created first. This enables true streaming document processing.
        #
        # 3. SCALABILITY: For large document collections, this prevents memory overflow
        #    and allows the pipeline to handle thousands of documents efficiently
        #
        # 4. EARLY TERMINATION: If an error occurs during upload, processing can
        #    stop immediately without wasting resources on remaining objects
        #
        # Example flow:
        # for search_object in create_search_index_objects(docs):  # One at a time
        #     upload_to_azure(search_object)  # Process immediately
        #     # Only 1 object in memory at any time vs 300+ without yield
        
        return self.strategy.create_search_index_objects(processed_documents)
    
    def print_processing_summary(self, result: DocumentProcessingResult):
        """Print a summary of the processing phase results."""
        print(f"\n⚙️  Document Processing Phase Complete")
        print(f"   Strategy: {result.strategy_name}")
        print(f"   Total documents: {result.total_documents}")
        print(f"   Successfully processed: {result.successfully_processed}")
        print(f"   Failed: {result.failed_documents}")
        print(f"   Processing time: {result.processing_time:.2f} seconds")
        
        if result.processed_documents:
            total_chunks = sum(doc.chunk_count for doc in result.processed_documents)
            print(f"   Total chunks created: {total_chunks}")
        
        # Print strategy-specific metadata
        if result.strategy_metadata:
            print(f"   Strategy-specific metrics:")
            for key, value in result.strategy_metadata.items():
                if isinstance(value, (list, dict)) and len(str(value)) > 100:
                    # For long lists/dicts, just show count
                    if isinstance(value, list):
                        print(f"     {key}: {len(value)} items")
                    elif isinstance(value, dict):
                        print(f"     {key}: {len(value)} entries")
                else:
                    print(f"     {key}: {value}")
        
        if result.errors:
            print(f"   Errors: {len(result.errors)}")
            for error in result.errors[:5]:  # Show first 5 errors
                print(f"     - {error}")
            if len(result.errors) > 5:
                print(f"     ... and {len(result.errors) - 5} more errors")


class DocumentUploadPhase:
    """
    Phase 3: Document Upload
    
    Responsible for uploading processed documents using configurable upload strategies.
    Different strategies can handle different vector search services (Azure, ChromaDB, etc.).
    """
    
    def __init__(self, upload_strategy: DocumentUploadStrategy = None):
        """
        Initialize the document upload phase.
        
        Args:
            upload_strategy: Strategy to use for document upload (default: AzureCognitiveSearchDocumentUploadStrategy)
        """
        if upload_strategy is None:
            raise ValueError("Document Upload Strategy should be provided for the Document Upload Phase")
        self.upload_strategy = upload_strategy
    
    async def upload_documents(self, processed_documents: List[ProcessedDocument], 
                             tracker=None, **kwargs) -> DocumentUploadResult:
        """
        Upload processed documents using the configured strategy.
        
        Args:
            processed_documents: List of processed documents from Processing Phase 
            tracker: DocumentProcessingTracker instance for marking files as processed
            **kwargs: Additional strategy-specific parameters
            
        Returns:
            DocumentUploadResult: Upload results with statistics and errors
        """
        return await self.upload_strategy.upload_documents(processed_documents, tracker, **kwargs)
    
    def print_upload_summary(self, result: DocumentUploadResult):
        """Print a summary of the upload phase results."""
        print(f"\n� Document Upload Phase Complete")
        print(f"   Strategy: {result.strategy_name}")
        print(f"   Total search objects: {result.total_search_objects}")
        print(f"   Successfully uploaded: {result.successfully_uploaded}")
        print(f"   Failed uploads: {result.failed_uploads}")
        print(f"   Upload time: {result.upload_time:.2f} seconds")
        
        if result.upload_metadata:
            print(f"   Upload metadata:")
            for key, value in result.upload_metadata.items():
                print(f"     {key}: {value}")
        
        if result.errors:
            print(f"   Upload errors: {len(result.errors)}")
            for error in result.errors[:3]:  # Show first 3 errors
                print(f"     - {error}")
            if len(result.errors) > 3:
                print(f"     ... and {len(result.errors) - 3} more errors")


class DocumentProcessingPipeline:
    """
    Complete document processing pipeline that orchestrates all three phases:
    1. Document Discovery - Find relevant documents
    2. Document Processing - Extract metadata, chunk, and prepare for search
    3. Document Upload - Upload to Azure Cognitive Search with embeddings
    
    Includes document tracking to avoid reprocessing unchanged files.
    """
    
    def __init__(self, 
                 discovery_strategy: DocumentDiscoveryStrategy = None,
                 processing_strategy: DocumentProcessingStrategy = None,
                 upload_strategy: DocumentUploadStrategy = None,
                 tracker=None,
                 force_reprocess: bool = False):
        """
        Initialize the document processing pipeline.
        
        Args:
            discovery_strategy: Strategy for document discovery (default: PersonalDocumentationDiscoveryStrategy)
            processing_strategy: Strategy for document processing (default: PersonalDocumentationAssistantAzureCognitiveSearchProcessingStrategy)
            upload_strategy: Strategy for document upload (default: AzureCognitiveSearchDocumentUploadStrategy)
            tracker: DocumentProcessingTracker instance (default: create new tracker)
            force_reprocess: If True, force reprocessing of already processed files
        """
        self.discovery_phase = DocumentDiscoveryPhase(discovery_strategy)
        self.processing_phase = DocumentProcessingPhase(processing_strategy)
        self.upload_phase = DocumentUploadPhase(upload_strategy)
        
        # Initialize document tracker
        if tracker is not None:
            self.tracker = tracker
        else:
            from .document_processing_tracker import DocumentProcessingTracker
            self.tracker = DocumentProcessingTracker()
        
        self.force_reprocess = force_reprocess
    
    def filter_unprocessed_files(self, discovered_files: List[Path]) -> tuple[List[Path], int, int]:
        """
        Filter discovered files to only include unprocessed ones.
        
        Args:
            discovered_files: List of discovered file paths
            
        Returns:
            Tuple of (unprocessed_files, total_discovered, already_processed_count)
        """
        unprocessed_files = []
        already_processed = 0
        
        for file_path in discovered_files:
            if self.tracker.is_processed(file_path):
                already_processed += 1
            else:
                unprocessed_files.append(file_path)
        
        print(f"   📊 File tracking analysis:")
        print(f"      Total discovered: {len(discovered_files)}")
        print(f"      Already processed: {already_processed}")
        print(f"      Need processing: {len(unprocessed_files)}")
        
        return unprocessed_files, len(discovered_files), already_processed
    
    def force_cleanup_files(self):
        """
        Clean up files when force reprocess is enabled.
        
        This method:
        1. Removes All files from the document tracker
        2. Removes All documents from the search service
        
        """
        if not self.force_reprocess:
            return
        
        print(f"\n🧹 Force Cleanup Phase (Force Reprocess Enabled)")
        
        # Step 1: Clean the document tracker
        files_removed_from_tracker = self.tracker.get_stats()['total_processed']
        self.tracker.reset()
        # Save tracker changes
        self.tracker.save()
        print(f"   📋 Removed {files_removed_from_tracker} files from document tracker")
        
        # Step 2: Remove all documents from search service
        self.upload_phase.upload_strategy.delete_all_documents_from_service()

        print(f"   ✅ Force cleanup completed - ready for reprocessing")
    
    async def run_complete_pipeline(self, root_directory: str, **kwargs) -> tuple[DocumentDiscoveryResult, DocumentProcessingResult, DocumentUploadResult]:
        """
        Run the complete 3-phase document processing pipeline.
        
        Args:
            root_directory: Root directory to process
            service_name: Azure Search service name
            admin_key: Azure Search admin key
            index_name: Azure Search index name
            **kwargs: Additional strategy-specific parameters (recursive, max_files, work_items, etc.)
            
        Returns:
            Tuple of (discovery_result, processing_result, upload_result)
        """
        print("🚀 Starting Complete Document Processing Pipeline")
        print("=" * 60)

                
        # Force Cleanup (Emtpy the search service of all documents and clean up the tracker)
        if self.force_reprocess:
            self.force_cleanup_files()
        
        # Phase 1: Discovery
        print("\n📁 Phase 1: Document Discovery")
        discovery_result = self.discovery_phase.discover_documents(root_directory, **kwargs)
        self.discovery_phase.print_discovery_summary(discovery_result)
        
        # Phase 1.6: Filter files using tracker (unless force reprocess)
        if discovery_result.discovered_files:
            print(f"\n📋 Phase 1.6: Document Tracking Filter")
            unprocessed_files, total_discovered, already_processed = self.filter_unprocessed_files(discovery_result.discovered_files)
            
            # Update discovery result to only include unprocessed files
            if not self.force_reprocess and already_processed > 0:
                print(f"   ⏭️  Skipping {already_processed} already processed files")
                
                # Update discovery result with filtered files
                discovery_result.discovered_files = unprocessed_files
                discovery_result.total_files = len(unprocessed_files)
                
                # Update file type counts
                files_by_type = {}
                for file_path in unprocessed_files:
                    file_type = file_path.suffix.lower()
                    files_by_type[file_type] = files_by_type.get(file_type, 0) + 1
                discovery_result.files_by_type = files_by_type
                
                print(f"   📊 Updated discovery result: {len(unprocessed_files)} files to process")
        
        # Phase 2: Processing (process each unprocessed document)
        if discovery_result.discovered_files:
            print(f"\n⚙️  Phase 2: Document Processing")
            print(f"   🔄 Processing {len(discovery_result.discovered_files)} unprocessed documents...")
            
            # Process the unprocessed documents through the processing strategy
            processing_result = self.processing_phase.process_documents(discovery_result.discovered_files)
            self.processing_phase.print_processing_summary(processing_result)
            
            # Phase 3: Upload (upload processed documents)
            if processing_result.processed_documents:
                print(f"\n📤 Phase 3: Document Upload")
                print(f"   🔄 Uploading {len(processing_result.processed_documents)} processed documents Search service...")
                
                upload_result = await self.upload_phase.upload_documents(
                    processing_result.processed_documents,
                    tracker=self.tracker  # Pass tracker for immediate file marking
                )
                self.upload_phase.print_upload_summary(upload_result)
                
                # Show the complete pipeline connection
                print(f"\n🔗 Complete Pipeline Flow:")
                print(f"   📁 Phase 1 - Files discovered: {discovery_result.total_files}")
                print(f"   ⚙️  Phase 2 - Files processed: {processing_result.successfully_processed}")
                print(f"   📤 Phase 3 - Search objects uploaded: {upload_result.successfully_uploaded}")
                print(f"   📋 Tracker - Files marked as processed: {upload_result.upload_metadata.get('documents_successfully_uploaded', 0)}")
                print(f"   ✅ End-to-end success rate: {(upload_result.successfully_uploaded / upload_result.total_search_objects * 100):.1f}%" if upload_result.total_search_objects > 0 else "   ✅ No files to process")
                
            else:
                print(f"\n⚠️  Skipping upload phase - no documents successfully processed")
                upload_result = DocumentUploadResult(
                    total_search_objects=0,
                    successfully_uploaded=0,
                    failed_uploads=0,
                    upload_time=0.0,
                    errors=["No processed documents to upload"],
                    upload_metadata=None
                )
            
        else:
            print(f"\n⚠️  Skipping processing and upload phases - no documents discovered")
            processing_result = DocumentProcessingResult(
                total_documents=0,
                successfully_processed=0,
                failed_documents=0,
                processed_documents=[],
                processing_time=0.0,
                errors=["No documents to process"],
                strategy_name="None",
                strategy_metadata=None
            )
            upload_result = DocumentUploadResult(
                total_search_objects=0,
                successfully_uploaded=0,
                failed_uploads=0,
                upload_time=0.0,
                errors=["No documents to upload"],
                upload_metadata=None
            )
        
        print("\n✅ Complete Pipeline Finished")
        return discovery_result, processing_result, upload_result