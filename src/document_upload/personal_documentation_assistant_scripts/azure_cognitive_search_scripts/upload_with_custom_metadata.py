#!/usr/bin/env python3
"""
Direct Metadata Upload Script
=============================

A specialized script for uploading documents with custom metadata directly to Azure Cognitive Search,
bypassing all auto-generation logic for maximum user control.

This script provides:
- Direct metadata injection with complete user control
- Schema validation against Azure Search index fields
- File and directory support via GeneralDocumentDiscoveryStrategy
- Document Processing Tracker integration for idempotent operations
- Individual file processing with comprehensive error handling

Usage:
    python upload_with_custom_metadata.py /path/to/file --metadata '{"title": "My Doc", "tags": "important,api", "category": "tutorial", "work_item_id": "PROJ-123"}'
    python upload_with_custom_metadata.py /path/to/directory --metadata '{"title": "Batch Upload", "tags": "docs", "category": "reference", "work_item_id": "PROJ-456"}'
"""

import os
import sys
import json
import argparse
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dotenv import load_dotenv

# Add src to path for imports - navigate up to src directory
current_dir = Path(__file__).parent
src_dir = current_dir.parent.parent
sys.path.insert(0, str(src_dir))

# Import project modules
from src.common.vector_search_services.azure_cognitive_search import get_azure_search_service
from src.document_upload.document_processing_tracker import DocumentProcessingTracker
from document_upload.processing_strategies import (
    PersonalDocumentationAssistantAzureCognitiveSearchProcessingStrategy, 
    AZURE_SEARCH_INDEX_FIELDS
)
from document_upload.discovery_strategies import GeneralDocumentDiscoveryStrategy

# Load environment variables
load_dotenv()


def validate_metadata_schema(metadata: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate metadata dictionary matches Azure Search schema requirements
    
    Note: DirectMetadataProcessingStrategy requires complete metadata
    since it bypasses all auto-generation logic for maximum control.
    
    Users must provide ALL required fields that process_single_document expects:
    - title: Document title
    - tags: Document tags (string or list)
    - category: Document category
    - work_item_id: Work item ID (used by extract_context_info for context_name)
    - file_type: Optional, auto-detected from extension if not provided
    - last_modified: Optional, auto-generated from file stats if not provided
    
    Args:
        metadata: User-provided metadata dictionary
        
    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []
    
    # Required fields for complete override
    required_fields = {'title', 'tags', 'category', 'work_item_id'}
    
    # System-generated fields (should not be provided by user)
    system_generated = {'id', 'content', 'content_vector', 'chunk_index', 'context_name'}
    
    # Optional fields that can be provided or auto-generated
    optional_fields = AZURE_SEARCH_INDEX_FIELDS - required_fields - system_generated
    
    # Check for missing required fields
    missing_required = required_fields - set(metadata.keys())
    if missing_required:
        errors.append(f"Missing required fields: {', '.join(sorted(missing_required))}")
    
    # Check for invalid fields (system-generated fields provided by user)
    invalid_fields = set(metadata.keys()) & system_generated
    if invalid_fields:
        errors.append(f"Cannot provide system-generated fields: {', '.join(sorted(invalid_fields))}")
    
    # Check for unknown fields
    all_valid_fields = required_fields | optional_fields
    unknown_fields = set(metadata.keys()) - all_valid_fields
    if unknown_fields:
        errors.append(f"Unknown fields (not in Azure Search schema): {', '.join(sorted(unknown_fields))}")
    
    # Validate specific field types and values
    if 'tags' in metadata:
        tags = metadata['tags']
        if not isinstance(tags, (str, list)):
            errors.append("'tags' must be a string or list of strings")
        elif isinstance(tags, list) and not all(isinstance(tag, str) for tag in tags):
            errors.append("'tags' list must contain only strings")
    
    if 'work_item_id' in metadata and not isinstance(metadata['work_item_id'], str):
        errors.append("'work_item_id' must be a string")
    
    if 'title' in metadata and not isinstance(metadata['title'], str):
        errors.append("'title' must be a string")
        
    if 'category' in metadata and not isinstance(metadata['category'], str):
        errors.append("'category' must be a string")
    
    # Optional field validation
    if 'file_type' in metadata and not isinstance(metadata['file_type'], str):
        errors.append("'file_type' must be a string")
        
    if 'last_modified' in metadata and not isinstance(metadata['last_modified'], str):
        errors.append("'last_modified' must be a string in ISO format")
    
    is_valid = len(errors) == 0
    return is_valid, errors


class DirectMetadataProcessingStrategy(PersonalDocumentationAssistantAzureCognitiveSearchProcessingStrategy):
    """Strategy that injects provided metadata directly into processed documents
    
    This strategy completely overrides metadata extraction to provide maximum
    user control over document metadata, bypassing all auto-generation logic.
    """
    
    def __init__(self, custom_metadata: Dict[str, Any]):
        """Initialize with custom metadata dictionary
        
        Args:
            custom_metadata: User-provided metadata dictionary
        """
        super().__init__()
        self.custom_metadata = custom_metadata
    
    def extract_metadata(self, content: str, file_path: Path) -> Dict[str, Any]:
        """Completely override metadata extraction with custom metadata
        
        This script provides maximum control by bypassing all parent
        auto-generation logic. Users must provide ALL required fields
        in their custom metadata dictionary.
        
        Required fields in custom_metadata (based on process_single_document usage):
        - title: Document title
        - tags: Document tags (string or list)
        - category: Document category
        - work_item_id: Work item ID (used by extract_context_info for context_name)
        - file_type: File type (optional, auto-detected from extension if not provided)
        - last_modified: Last modified timestamp (optional, auto-generated if not provided)
        
        Args:
            content: Document content (unused in this strategy)
            file_path: Path to the document file
            
        Returns:
            Dict containing the custom metadata with auto-generated optional fields
        """
        # Start with custom metadata as the base
        metadata = dict(self.custom_metadata)
        
        # Auto-detect file_type if not provided
        if 'file_type' not in metadata:
            file_extension = file_path.suffix.lower()
            type_mapping = {
                '.md': 'markdown',
                '.txt': 'text',
                '.docx': 'document',
                '.pdf': 'pdf'
            }
            metadata['file_type'] = type_mapping.get(file_extension, 'unknown')
        
        # Auto-generate last_modified if not provided
        if 'last_modified' not in metadata:
            file_stat = file_path.stat()
            last_modified_dt = datetime.fromtimestamp(file_stat.st_mtime)
            metadata['last_modified'] = last_modified_dt.isoformat() + 'Z'
        
        # Ensure tags is a list (convert string to list if needed for internal processing)
        if isinstance(metadata.get('tags'), str):
            metadata['tags'] = [tag.strip() for tag in metadata['tags'].split(',')]
        elif not isinstance(metadata.get('tags'), list):
            metadata['tags'] = []
        
        return metadata


def process_target_path(target_path: Path, metadata: Dict[str, Any]) -> List[Path]:
    """Process target path (file or directory) using GeneralDocumentDiscoveryStrategy
    
    Note: GeneralDocumentDiscoveryStrategy automatically handles both files and directories,
    so no manual path type checking is needed. It will:
    - For files: Return the file if it has a supported extension
    - For directories: Discover all supported files within the directory
    
    Args:
        target_path: Path to file or directory to process
        metadata: Custom metadata dictionary (passed for context, not used in discovery)
        
    Returns:
        List of discovered file paths to process
        
    Raises:
        ValueError: If no supported documents are found
    """
    # Use GeneralDocumentDiscoveryStrategy for unified file/directory handling
    discovery_strategy = GeneralDocumentDiscoveryStrategy()
    files_to_process = discovery_strategy.discover_documents(str(target_path))
    
    if not files_to_process:
        if target_path.is_file():
            raise ValueError(f"File type not supported: {target_path}")
        else:
            raise ValueError(f"No supported documents found in directory: {target_path}")
    
    return files_to_process


async def upload_document_to_azure(processed_document, processing_strategy, 
                                 azure_search_service) -> Dict[str, Any]:
    """Upload a single processed document to Azure Cognitive Search
    
    Args:
        processed_document: ProcessedDocument instance
        processing_strategy: Processing strategy instance
        azure_search_service: Azure Cognitive Search service instance
        
    Returns:
        Dictionary with upload results
    """
    try:
        # Create search index objects for this document
        print(f"      🔄 Creating search objects with embeddings...")
        
        # Collect search objects for this document
        doc_search_objects = []
        async for search_object in processing_strategy.create_search_index_objects([processed_document]):
            doc_search_objects.append(search_object)
        
        doc_total_objects = len(doc_search_objects)
        print(f"      📊 Generated {doc_total_objects} search objects")
        
        if doc_search_objects:
            # Upload this document's search objects to Azure Search
            print(f"      📤 Uploading {doc_total_objects} objects to Azure Search...", end=" ")
            
            successful, failed = azure_search_service.upload_search_objects_batch(doc_search_objects)
            
            if failed > 0:
                print(f"⚠️  ({successful} succeeded, {failed} failed)")
                return {
                    'success': False,
                    'uploaded': successful,
                    'failed': failed,
                    'total': doc_total_objects,
                    'error': f"{failed}/{doc_total_objects} objects failed to upload"
                }
            else:
                print("✅")
                return {
                    'success': True,
                    'uploaded': successful,
                    'failed': failed,
                    'total': doc_total_objects,
                    'error': None
                }
        else:
            print(f"      ❌ No search objects generated")
            return {
                'success': False,
                'uploaded': 0,
                'failed': 0,
                'total': 0,
                'error': "No search objects generated"
            }
            
    except Exception as e:
        error_msg = f"Upload error - {str(e)}"
        print(f"      ❌ {error_msg}")
        return {
            'success': False,
            'uploaded': 0,
            'failed': 1,  # Estimate
            'total': 1,
            'error': error_msg
        }


async def process_and_upload(target_path: Path, metadata: Dict[str, Any], 
                           validate_only: bool = False) -> None:
    """Main processing flow with tracker integration
    
    Args:
        target_path: Path to file or directory to process
        metadata: Custom metadata dictionary
        validate_only: If True, only validate metadata without processing
    """
    
    # Validate metadata first
    print("🔍 Validating metadata schema...")
    is_valid, errors = validate_metadata_schema(metadata)
    
    if not is_valid:
        print("❌ Metadata validation failed:")
        for error in errors:
            print(f"   - {error}")
        print("\nRequired fields: title, tags, category, work_item_id")
        print("Optional fields: file_type, last_modified, metadata_json")
        return
    
    print("✅ Metadata validation passed")
    
    # Discover files to process
    print(f"📁 Discovering files at: {target_path}")
    try:
        files_to_process = process_target_path(target_path, metadata)
        print(f"   Found {len(files_to_process)} supported files")
        
        # Show discovered files
        for i, file_path in enumerate(files_to_process, 1):
            print(f"   {i:2d}. {file_path.name}")
    
    except Exception as e:
        print(f"❌ File discovery failed: {str(e)}")
        return
    
    if validate_only:
        print(f"✅ Validation complete: {len(files_to_process)} files ready for processing")
        return
    
    # Initialize Azure Search service
    print("🔗 Initializing Azure Cognitive Search connection...")
    try:
        azure_search_service = get_azure_search_service()
        print("✅ Azure Search connection established")
        
    except Exception as e:
        print(f"❌ Failed to initialize Azure Search service: {str(e)}")
        return
    
    # Initialize tracker
    print("📋 Initializing Document Processing Tracker...")
    tracker = DocumentProcessingTracker()
    print("✅ Tracker initialized")
    
    # Process each discovered file
    print(f"\n⚙️  Processing {len(files_to_process)} files with custom metadata...")
    successfully_uploaded_files = []
    failed_files = []
    
    for i, file_path in enumerate(files_to_process, 1):
        try:
            print(f"\n📄 File {i}/{len(files_to_process)}: {file_path.name}")
            
            # Create DirectMetadataProcessingStrategy with custom metadata
            processing_strategy = DirectMetadataProcessingStrategy(metadata)
            
            # Process the single file through the processing strategy
            print(f"   🔄 Processing document...")
            processing_result = processing_strategy.process_documents([file_path])
            
            if processing_result.processed_documents:
                processed_doc = processing_result.processed_documents[0]
                print(f"   ✅ Document processed: {processed_doc.chunk_count} chunks created")
                
                # Upload processed document to Azure Search
                upload_result = await upload_document_to_azure(
                    processed_doc, 
                    processing_strategy,
                    azure_search_service
                )
                
                if upload_result['success']:
                    # Mark file as processed in tracker
                    tracker.mark_processed(file_path, metadata)
                    successfully_uploaded_files.append(file_path)
                    print(f"   📋 Marked as processed in tracker")
                else:
                    failed_files.append(file_path)
                    print(f"   ❌ Upload failed: {upload_result['error']}")
            else:
                failed_files.append(file_path)
                print(f"   ❌ Document processing failed")
                
        except Exception as e:
            failed_files.append(file_path)
            print(f"   ❌ Error processing {file_path.name}: {str(e)}")
    
    # Save tracker after all processing
    if successfully_uploaded_files:
        tracker.save()
        print(f"\n📋 Saved tracker with {len(successfully_uploaded_files)} successfully processed files")
    
    # Final summary
    print(f"\n📊 Processing Summary:")
    print(f"   Total files discovered: {len(files_to_process)}")
    print(f"   Successfully uploaded: {len(successfully_uploaded_files)}")
    print(f"   Failed uploads: {len(failed_files)}")
    
    if successfully_uploaded_files:
        print(f"\n✅ Successfully uploaded files:")
        for file_path in successfully_uploaded_files:
            print(f"   - {file_path.name}")
    
    if failed_files:
        print(f"\n❌ Failed files:")
        for file_path in failed_files:
            print(f"   - {file_path.name}")
    
    success_rate = (len(successfully_uploaded_files) / len(files_to_process) * 100) if files_to_process else 0
    print(f"\n🎯 Success rate: {success_rate:.1f}%")
    
    # Return True if all files were successfully uploaded
    return len(failed_files) == 0


def main():
    """Main entry point for the direct metadata upload script"""
    parser = argparse.ArgumentParser(
        description="Upload documents with custom metadata to Azure Cognitive Search",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Upload single file with custom metadata
  python upload_with_custom_metadata.py /path/to/document.md \\
    --metadata '{"title": "API Guide", "tags": "api,documentation", "category": "tutorial", "work_item_id": "PROJ-123"}'
  
  # Upload all files in directory with shared metadata
  python upload_with_custom_metadata.py /path/to/docs \\
    --metadata '{"title": "Project Documentation", "tags": "project,docs", "category": "reference", "work_item_id": "PROJ-456"}'
  
  # Validate metadata without uploading
  python upload_with_custom_metadata.py /path/to/docs \\
    --metadata '{"title": "Test", "tags": "test", "category": "test", "work_item_id": "TEST-1"}' \\
    --validate-only

Required metadata fields:
  - title: Document title (string)
  - tags: Document tags (string or list)
  - category: Document category (string)
  - work_item_id: Work item identifier (string)

Optional metadata fields:
  - file_type: File type (auto-detected if not provided)
  - last_modified: Last modified timestamp (auto-generated if not provided)
  - metadata_json: Additional metadata as JSON string
        """
    )
    
    parser.add_argument(
        "path", 
        help="File or folder path to upload"
    )
    parser.add_argument(
        "--metadata", 
        required=True, 
        help="JSON string containing custom metadata (must include: title, tags, category, work_item_id)"
    )
    parser.add_argument(
        "--validate-only", 
        action="store_true", 
        help="Only validate metadata and discover files without uploading"
    )
    
    args = parser.parse_args()
    
    # Parse target path
    target_path = Path(args.path).resolve()
    if not target_path.exists():
        print(f"❌ Error: Path does not exist: {target_path}")
        return 1
    
    # Parse metadata JSON
    try:
        metadata = json.loads(args.metadata)
        if not isinstance(metadata, dict):
            print("❌ Error: Metadata must be a JSON object")
            return 1
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in metadata: {str(e)}")
        return 1
    
    # Show configuration
    print("🚀 Direct Metadata Upload Script")
    print("=" * 50)
    print(f"Target path: {target_path}")
    print(f"Metadata fields: {', '.join(metadata.keys())}")
    if args.validate_only:
        print("Mode: Validation only (no upload)")
    else:
        print("Mode: Process and upload")
    
    # Run the processing
    try:
        asyncio.run(process_and_upload(target_path, metadata, args.validate_only))
        return 0
    except KeyboardInterrupt:
        print("\n⚠️  Process interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        return 1


if __name__ == "__main__":
    exit(main())
