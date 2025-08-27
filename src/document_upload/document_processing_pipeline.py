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

# Import Azure search service for upload phase
from src.common.vector_search_services.azure_cognitive_search import get_azure_search_service


@dataclass
class DocumentUploadResult:
    """Result of the document upload phase."""
    total_search_objects: int
    successfully_uploaded: int
    failed_uploads: int
    upload_time: float
    errors: List[str]
    upload_metadata: Optional[Dict[str, Any]] = None


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
    
    Responsible for uploading processed documents to Azure Cognitive Search.
    This phase takes the processed documents, creates search index objects with embeddings,
    and uploads them to the Azure search service.
    """
    
    def __init__(self, azure_search_service=None, processing_strategy=None):
        """
        Initialize the document upload phase.
        
        Args:
            azure_search_service: Azure search service instance (default: from environment config)
            processing_strategy: Processing strategy to create search objects (default: PersonalDocumentationAssistantAzureCognitiveSearchProcessingStrategy)
        """
        self.azure_search_service = azure_search_service
        if processing_strategy is not None:
            self.processing_strategy = processing_strategy
        else:
            # Use PersonalDocumentationAssistantAzureCognitiveSearchProcessingStrategy as default
            from document_upload.processing_strategies import PersonalDocumentationAssistantAzureCognitiveSearchProcessingStrategy
            self.processing_strategy = PersonalDocumentationAssistantAzureCognitiveSearchProcessingStrategy()
    
    async def upload_documents(self, processed_documents: List[ProcessedDocument], 
                        service_name: str, admin_key: str, index_name: str, 
                        tracker=None) -> DocumentUploadResult:
        """
        Upload processed documents to Azure Cognitive Search.
        
        This method processes each document individually:
        1. Creates search index objects with embeddings for each document
        2. Uploads the objects to Azure Cognitive Search immediately
        3. Marks successfully uploaded files as processed in the tracker immediately
        
        Args:
            processed_documents: List of processed documents from Phase 2
            service_name: Azure Search service name
            admin_key: Azure Search admin key
            index_name: Azure Search index name
            tracker: DocumentProcessingTracker instance for marking files as processed
            
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
        
        print(f"   📤 Uploading {len(processed_documents)} processed documents to Azure Search...")
        
        # Initialize Azure search service if not provided
        if self.azure_search_service is None:
            self.azure_search_service = get_azure_search_service(service_name, admin_key, index_name)
        
        # Process each document individually
        for doc_idx, processed_doc in enumerate(processed_documents, 1):
            try:
                print(f"   📄 Document {doc_idx}/{len(processed_documents)}: {processed_doc.file_name}")
                
                # Create search index objects for this document
                print(f"      🔄 Creating search objects with embeddings...")
                
                # Collect search objects for this document
                doc_search_objects = []
                async for search_object in self.processing_strategy.create_search_index_objects([processed_doc]):
                    doc_search_objects.append(search_object)
                
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
            "individual_document_processing": True,
            "average_objects_per_document": total_search_objects / len(processed_documents) if processed_documents else 0,
            "processing_mode": "individual_document_upload_with_immediate_tracking"
        }
        
        return DocumentUploadResult(
            total_search_objects=total_search_objects,
            successfully_uploaded=successfully_uploaded,
            failed_uploads=failed_uploads,
            upload_time=upload_time,
            errors=errors,
            upload_metadata=upload_metadata
        )
    
    def print_upload_summary(self, result: DocumentUploadResult):
        """Print a summary of the upload phase results."""
        print(f"\n📤 Document Upload Phase Complete")
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
                 azure_search_service=None,
                 tracker=None,
                 force_reprocess: bool = False):
        """
        Initialize the document processing pipeline.
        
        Args:
            discovery_strategy: Strategy for document discovery (default: PersonalDocumentationDiscoveryStrategy)
            processing_strategy: Strategy for document processing (default: PersonalDocumentationAssistantAzureCognitiveSearchProcessingStrategy)
            azure_search_service: Azure search service instance (default: from environment config)
            tracker: DocumentProcessingTracker instance (default: create new tracker)
            force_reprocess: If True, force reprocessing of already processed files
        """
        self.discovery_phase = DocumentDiscoveryPhase(discovery_strategy)
        self.processing_phase = DocumentProcessingPhase(processing_strategy)
        self.upload_phase = DocumentUploadPhase(azure_search_service, processing_strategy)
        
        # Initialize document tracker
        if tracker is not None:
            self.tracker = tracker
        else:
            from document_upload.file_tracker import DocumentProcessingTracker
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
        if self.force_reprocess:
            print(f"   🔄 Force reprocess enabled - processing all {len(discovered_files)} files")
            return discovered_files, len(discovered_files), 0
        
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
    
    def force_cleanup_files(self, discovered_files: List[Path], service_name: str, admin_key: str, index_name: str):
        """
        Clean up files when force reprocess is enabled.
        
        This method:
        1. Removes files from the document tracker
        2. Removes corresponding documents from the search index
        
        Args:
            discovered_files: List of file paths that will be reprocessed
            service_name: Azure Search service name
            admin_key: Azure Search admin key  
            index_name: Azure Search index name
        """
        if not self.force_reprocess:
            return
        
        print(f"\n🧹 Force Cleanup Phase (Force Reprocess Enabled)")
        print(f"   🔄 Cleaning up {len(discovered_files)} files from tracker and search index...")
        
        # Step 1: Remove files from document tracker
        files_removed_from_tracker = 0
        for file_path in discovered_files:
            if self.tracker.is_processed(file_path):
                self.tracker.mark_unprocessed(file_path)
                files_removed_from_tracker += 1
        
        # Save tracker changes
        self.tracker.save()
        print(f"   📋 Removed {files_removed_from_tracker} files from document tracker")
        
        # Step 2: Remove corresponding documents from search index
        try:
            # Initialize Azure search service if not already done
            if self.upload_phase.azure_search_service is None:
                from src.common.vector_search_services.azure_cognitive_search import get_azure_search_service
                self.upload_phase.azure_search_service = get_azure_search_service(service_name, admin_key, index_name)
            
            # Delete documents from search index based on file paths
            print(f"   🗑️  Removing documents from search index...")
            total_deleted_count = 0
            
            for file_path in discovered_files:
                try:
                    # Use the filename to delete documents using the filter method
                    file_name = file_path.name
                    deleted_count = self.upload_phase.azure_search_service.delete_documents_by_filter({"file_name": file_name})
                    total_deleted_count += deleted_count
                    
                    if deleted_count > 0:
                        print(f"      ✅ Deleted {deleted_count} documents for {file_name}")
                    else:
                        print(f"      ℹ️  No documents found for {file_name}")
                        
                except Exception as e:
                    print(f"      ⚠️  Error deleting documents for {file_path.name}: {str(e)}")
            
            print(f"   🗑️  Removed {total_deleted_count} total documents from search index")
            
        except Exception as e:
            print(f"   ❌ Error during search index cleanup: {str(e)}")
            print(f"   ⚠️  Continuing with reprocessing despite cleanup errors...")
        
        print(f"   ✅ Force cleanup completed - ready for reprocessing")
    
    async def run_complete_pipeline(self, root_directory: str, 
                             service_name: str, admin_key: str, index_name: str, 
                             **kwargs) -> tuple[DocumentDiscoveryResult, DocumentProcessingResult, DocumentUploadResult]:
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
        
        # Phase 1: Discovery
        print("\n📁 Phase 1: Document Discovery")
        discovery_result = self.discovery_phase.discover_documents(root_directory, **kwargs)
        self.discovery_phase.print_discovery_summary(discovery_result)
        
        # Phase 1.5: Force Cleanup (if force reprocess is enabled)
        if discovery_result.discovered_files and self.force_reprocess:
            self.force_cleanup_files(discovery_result.discovered_files, service_name, admin_key, index_name)
        
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
            
            # Phase 3: Upload (upload processed documents to Azure Search)
            if processing_result.processed_documents:
                print(f"\n📤 Phase 3: Document Upload")
                print(f"   🔄 Uploading {len(processing_result.processed_documents)} processed documents to Azure Search...")
                
                upload_result = await self.upload_phase.upload_documents(
                    processing_result.processed_documents,
                    service_name, admin_key, index_name,
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