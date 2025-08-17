# Personal Documentation Assistant - Document Processing Scripts Implementation Plan

## 📋 Executive Summary

This document provides a comprehensive implementation plan for three specialized document processing scripts based on thorough analysis of the existing sophisticated codebase. The scripts will leverage the existing three-phase pipeline architecture (Discovery → Processing → Upload) while providing focused, customizable functionality.

## 🏗️ Architecture Analysis

### Current System Strengths

1. **Three-Phase Pipeline Architecture**: Well-established strategy pattern with clear separation of concerns
2. **Document Processing Tracker**: Sophisticated signature-based file tracking for idempotent operations
3. **Azure Cognitive Search Integration**: Comprehensive service class with CRUD operations
4. **Strategy Pattern Implementation**: Extensible processing and discovery strategies
5. **Schema Consistency**: 13-field Azure Search index schema with vector embeddings

### Key Components Available

- **DocumentProcessingPipeline**: Orchestrates all three phases
- **DocumentProcessingTracker**: File signature tracking and idempotency
- **AzureCognitiveSearch**: Complete Azure Search service wrapper
- **Processing Strategies**: PersonalDocumentationAssistantProcessingStrategy
- **Discovery Strategies**: GeneralDocumentDiscoveryStrategy
- **Schema Fields**: `id`, `content`, `content_vector`, `file_path`, `file_name`, `file_type`, `title`, `tags`, `category`, `context_name`, `last_modified`, `chunk_index`, `metadata_json`

## 📊 Script Requirements Analysis

### Script 1: Direct Metadata Upload Script

- **Input**: File/folder path + metadata dictionary
- **Purpose**: Direct upload with custom metadata bypassing ALL auto-generation
- **Key Requirement**: Metadata dictionary must provide ALL required fields (title, tags, category, work_item_id)
- **Processing**: Custom chunking + embedding + direct upload
- **Tracker**: Uses DocumentProcessingTracker for idempotency
- **Note**: Completely bypasses PersonalDocumentationAssistantProcessingStrategy auto-generation for maximum control### Script 2: Full Pipeline Upload Script

- **Input**: File/folder path + optional force reset
- **Purpose**: Complete pipeline execution (Discovery → Processing → Upload)
- **Key Feature**: Force reset option (delete index + reprocess all)
- **Processing**: Uses existing pipeline with strategies
- **Tracker**: Full DocumentProcessingTracker integration

### Script 3: Context-Based Deletion Script

- **Input**: Context name + file name combination
- **Purpose**: Precise document chunk deletion
- **Key Feature**: Multi-match handling and preview mode
- **Processing**: Search + delete + tracker cleanup
- **Tracker**: Remove from DocumentProcessingTracker

## 🛠️ Implementation Plan

### Phase 1: Script 1 - Direct Metadata Upload Script

#### File Location

```
src/document_upload/common_scripts/upload_single_file.py
```

#### Core Architecture

```python
# Key Components:
- Custom metadata injection strategy
- Schema validation against AZURE_SEARCH_INDEX_FIELDS
- Direct document processing (uses discovery but overrides metadata extraction)
- Individual file/folder processing with tracker
- Comprehensive error handling and validation
```

#### Implementation Details

**1. Metadata Validation Module**

```python
def validate_metadata_schema(metadata: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate metadata dictionary matches Azure Search schema

    Note: DirectMetadataProcessingStrategy requires complete metadata
    since it bypasses all auto-generation logic for maximum control.

    Users must provide ALL required fields that process_single_document expects:
    - title: Document title
    - tags: Document tags (string or list)
    - category: Document category
    - work_item_id: Work item ID (used by extract_context_info for context_name)
    - file_type: Optional, auto-detected from extension if not provided
    - last_modified: Optional, auto-generated from file stats if not provided
    """
    required_fields = {'title', 'tags', 'category', 'work_item_id'}  # All required for complete override
    optional_fields = AZURE_SEARCH_INDEX_FIELDS - required_fields - {
        'id', 'content', 'content_vector', 'chunk_index', 'context_name'  # System-generated fields
    }
    # Return validation result and error list
```

**2. Custom Processing Strategy**

```python
class DirectMetadataProcessingStrategy(PersonalDocumentationAssistantProcessingStrategy):
    """Strategy that injects provided metadata directly into processed documents"""
    def __init__(self, custom_metadata: Dict[str, Any]):
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
        """
        # Start with custom metadata as the base
        metadata = dict(self.custom_metadata)

        # Auto-detect file_type if not provided
        if 'file_type' not in metadata:
            file_extension = file_path.suffix.lower()
            type_mapping = {
                '.md': 'markdown',
                '.txt': 'text',
                '.docx': 'document'
            }
            metadata['file_type'] = type_mapping.get(file_extension, 'unknown')

        # Auto-generate last_modified if not provided
        if 'last_modified' not in metadata:
            from datetime import datetime
            file_stat = file_path.stat()
            last_modified_dt = datetime.fromtimestamp(file_stat.st_mtime)
            metadata['last_modified'] = last_modified_dt.isoformat() + 'Z'

        # Ensure tags is a list (convert string to list if needed for internal processing)
        if isinstance(metadata.get('tags'), str):
            metadata['tags'] = [tag.strip() for tag in metadata['tags'].split(',')]
        elif not isinstance(metadata.get('tags'), list):
            metadata['tags'] = []

        return metadata
```

**3. File/Folder Processing Logic**

```python
def process_target_path(target_path: Path, metadata: Dict[str, Any]):
    """Process target path (file or directory) using GeneralDocumentDiscoveryStrategy

    Note: GeneralDocumentDiscoveryStrategy automatically handles both files and directories,
    so no manual path type checking is needed. It will:
    - For files: Return the file if it has a supported extension
    - For directories: Discover all supported files within the directory
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
```

**4. Command-Line Interface**

```python
def main():
    parser = argparse.ArgumentParser(description="Upload documents with custom metadata")
    parser.add_argument("path", help="File or folder path to upload")
    parser.add_argument("--metadata", required=True, help="JSON string of metadata")
    parser.add_argument("--validate-only", action="store_true", help="Only validate metadata")
```

**5. Main Processing Flow with Tracker Integration**

```python
async def process_and_upload(target_path: Path, metadata: Dict[str, Any], validate_only: bool = False):
    """Main processing flow with tracker integration"""

    # Initialize tracker
    from document_upload.file_tracker import DocumentProcessingTracker
    tracker = DocumentProcessingTracker()

    # Discover files to process
    files_to_process = process_target_path(target_path, metadata)

    if validate_only:
        print(f"✅ Validation complete: {len(files_to_process)} files ready for processing")
        return

    # Process each discovered file
    successfully_uploaded_files = []
    failed_files = []

    for file_path in files_to_process:
        try:
            print(f"📄 Processing: {file_path}")

            # Create DirectMetadataProcessingStrategy with custom metadata
            processing_strategy = DirectMetadataProcessingStrategy(metadata)

            # Process the single file through the processing strategy (creates chunks of the file)
            processing_result = processing_strategy.process_documents([file_path])

            if processing_result.processed_documents:
                # Upload processed document to Azure Search
                upload_result = await upload_document_to_azure(
                    processing_result.processed_documents[0],
                    processing_strategy
                )

                if upload_result.successfully_uploaded > 0:
                    # Mark file as processed in tracker
                    tracker.mark_processed(file_path)
                    successfully_uploaded_files.append(file_path)
                    print(f"   ✅ Successfully uploaded and marked as processed")
                else:
                    failed_files.append(file_path)
                    print(f"   ❌ Upload failed")
            else:
                failed_files.append(file_path)
                print(f"   ❌ Processing failed")

        except Exception as e:
            failed_files.append(file_path)
            print(f"   ❌ Error: {str(e)}")

    # Save tracker after all processing
    if successfully_uploaded_files:
        tracker.save()
        print(f"📋 Saved tracker with {len(successfully_uploaded_files)} successfully processed files")

    # Summary
    print(f"\n📊 Processing Summary:")
    print(f"   Total files: {len(files_to_process)}")
    print(f"   Successfully uploaded: {len(successfully_uploaded_files)}")
    print(f"   Failed: {len(failed_files)}")
```

#### Key Features

- **Schema Validation**: Pre-validate metadata before processing
- **Flexible Input**: Support both single files and directories
- **Custom Metadata Control**: Direct metadata injection bypassing auto-generation
- **Tracker Integration**: Mark successfully uploaded files as processed to prevent duplicates
- **Comprehensive Logging**: Detailed processing feedback
- **Error Recovery**: Continue processing on individual file failures

---

### Phase 2: Script 2 - Full Pipeline Upload Script ✅ ENHANCED

#### File Location

```
src/document_upload/common_scripts/upload_with_pipeline.py
```

#### Core Architecture

```python
# Enhanced Key Components (Based on Script 1 Learnings):
- Full DocumentProcessingPipeline integration with run_complete_pipeline()
- Force reset functionality using Azure Search delete_all_documents()
- Comprehensive CLI with path validation and environment setup
- Real-time progress feedback and detailed error handling
- Statistics reporting with processing metrics
- Robust error recovery and graceful failure handling
```

#### Implementation Details

**1. Enhanced Force Reset Implementation**

````python
async def force_reset_index_and_tracker():
    """Complete index reset and tracker cleanup with comprehensive validation"""
    print("🗑️  Performing complete force reset...")

    # Load environment and initialize services (using existing patterns)
    load_dotenv()

    try:
        # Initialize Azure Search service using existing factory function
        azure_search = get_azure_search_service()
        tracker = DocumentProcessingTracker()

        # 1. Delete all documents from index using existing method
        print("   🔄 Deleting all documents from search index...")
        deleted_count = azure_search.delete_all_documents()
        print(f"   ✅ Successfully deleted {deleted_count} documents from index")

        # 2. Clear tracker state completely using existing method
        print("   🔄 Clearing document processing tracker...")
        tracker.clear()  # Complete cleanup (clears data and deletes file)
        tracker.save()
        print(f"   ✅ Document tracker cleared and saved")

        # 3. Verification step using existing method
        remaining_docs = azure_search.get_document_count()
        if remaining_docs == 0:
            print("   ✅ Force reset completed successfully")
            return True
        else:
            print(f"   ⚠️  Warning: {remaining_docs} documents still remain in index")
            return False

    except Exception as e:
        print(f"   ❌ Error during force reset: {str(e)}")
        print("   💡 Try running the script again or check Azure Search connectivity")
        return False
```**2. Enhanced Pipeline Configuration and Integration**

```python
def create_configured_pipeline(force_reprocess: bool = False) -> DocumentProcessingPipeline:
    """Create fully configured pipeline with proper strategy integration"""

    # Use GeneralDocumentDiscoveryStrategy for unified file/directory handling
    # (eliminates need for manual path type checking like in Script 1)
    discovery_strategy = GeneralDocumentDiscoveryStrategy()

    # Use PersonalDocumentationAssistantProcessingStrategy for auto metadata generation
    processing_strategy = PersonalDocumentationAssistantProcessingStrategy()

    # Initialize tracker for idempotent operations
    tracker = DocumentProcessingTracker()

    # Create pipeline with force reprocess flag
    pipeline = DocumentProcessingPipeline(
        discovery_strategy=discovery_strategy,
        processing_strategy=processing_strategy,
        tracker=tracker,
        force_reprocess=force_reprocess
    )

    return pipeline

async def process_path_with_pipeline(target_path: str, force_reprocess: bool = False,
                                   dry_run: bool = False) -> bool:
    """Process path using complete pipeline with comprehensive error handling"""

    # Validate path exists
    target_path_obj = Path(target_path)
    if not target_path_obj.exists():
        print(f"❌ Error: Path does not exist: {target_path}")
        return False

    # Load environment and validate (using existing pattern from create_index.py)
    load_dotenv()

    # Validate environment variables (using existing pattern)
    required_vars = ['AZURE_SEARCH_SERVICE', 'AZURE_SEARCH_KEY', 'AZURE_OPENAI_ENDPOINT', 'AZURE_OPENAI_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        return False

    # Create configured pipeline
    pipeline = create_configured_pipeline(force_reprocess)

    try:
        # Get Azure credentials from environment (matching existing patterns)
        service_name = os.getenv('AZURE_SEARCH_SERVICE')
        admin_key = os.getenv('AZURE_SEARCH_KEY')
        index_name = os.getenv('AZURE_SEARCH_INDEX', 'work-items-index')  # Default value like existing scripts

        print(f"🚀 Starting full pipeline processing...")
        print(f"   📍 Target path: {target_path}")
        print(f"   🔄 Force reprocess: {force_reprocess}")
        print(f"   👁️  Dry run: {dry_run}")

        if dry_run:
            # Show discovery preview without processing
            discovery_result = pipeline.discovery_phase.discover_documents(str(target_path_obj))
            pipeline.discovery_phase.print_discovery_summary(discovery_result)

            # Show what would be processed
            if discovery_result.discovered_files:
                unprocessed_files, total_discovered, already_processed = pipeline.filter_unprocessed_files(
                    discovery_result.discovered_files
                )

                print(f"\n📊 Processing Preview:")
                print(f"   📁 Total files found: {total_discovered}")
                print(f"   ⏭️  Already processed: {already_processed}")
                print(f"   🔄 Would process: {len(unprocessed_files)}")
                print(f"\n💡 Run without --dry-run to perform actual processing")

            return True

        # Execute complete pipeline
        discovery_result, processing_result, upload_result = await pipeline.run_complete_pipeline(
            root_directory=str(target_path_obj),
            service_name=service_name,
            admin_key=admin_key,
            index_name=index_name
        )

        # Show comprehensive results
        print_pipeline_statistics(discovery_result, processing_result, upload_result)

        # Return success if any documents were processed
        return upload_result.successfully_uploaded > 0 or processing_result.successfully_processed == 0

    except Exception as e:
        print(f"❌ Pipeline execution failed: {str(e)}")
        print("💡 Check your environment configuration and Azure connectivity")
        return False
````

**3. Enhanced Command-Line Interface with Comprehensive Options**

```python
def main():
    """Enhanced CLI with comprehensive options and validation"""
    parser = argparse.ArgumentParser(
        description="Upload documents using full DocumentProcessingPipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process single file
  python upload_with_pipeline.py "C:/docs/readme.md"

  # Process entire directory
  python upload_with_pipeline.py "C:/Work Items"

  # Force reprocess all files (ignores tracker)
  python upload_with_pipeline.py "C:/docs" --force-reprocess

  # Complete reset: delete all + reprocess all
  python upload_with_pipeline.py "C:/docs" --force-reset

  # Preview what would be processed
  python upload_with_pipeline.py "C:/docs" --dry-run
        """)

    parser.add_argument("path",
                       help="Root directory or file path to process")

    parser.add_argument("--force-reset", action="store_true",
                       help="Delete all documents from index and tracker, then reprocess all")

    parser.add_argument("--force-reprocess", action="store_true",
                       help="Reprocess files ignoring tracker state (keeps existing docs)")

    parser.add_argument("--dry-run", action="store_true",
                       help="Show what would be processed without making changes")

    parser.add_argument("--stats", action="store_true",
                       help="Show detailed processing statistics after completion")

    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Enable verbose logging for debugging")

    args = parser.parse_args()

    # Configure logging
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    # Validate mutually exclusive options
    if args.force_reset and args.force_reprocess:
        print("❌ Error: Cannot use both --force-reset and --force-reprocess")
        print("💡 Use --force-reset for complete reset, or --force-reprocess to ignore tracker")
        return 1

    try:
        success = False

        if args.force_reset:
            # Handle complete reset
            print("⚠️  WARNING: This will delete ALL documents and tracker data!")
            if not args.dry_run:
                confirm = input("Continue? (y/N): ").lower().strip()
                if confirm != 'y':
                    print("Operation cancelled.")
                    return 0

            # Perform reset (unless dry run)
            if not args.dry_run:
                reset_success = await force_reset_index_and_tracker()
                if not reset_success:
                    return 1
            else:
                print("🔍 DRY RUN: Would delete all documents and tracker data")

            # Process with force reprocess after reset
            success = await process_path_with_pipeline(
                args.path,
                force_reprocess=True,
                dry_run=args.dry_run
            )

        else:
            # Regular processing
            success = await process_path_with_pipeline(
                args.path,
                force_reprocess=args.force_reprocess,
                dry_run=args.dry_run
            )

        if success:
            print("✅ Pipeline processing completed successfully")
            return 0
        else:
            print("❌ Pipeline processing failed")
            return 1

    except KeyboardInterrupt:
        print("\n⏹️  Processing interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

if __name__ == "__main__":
    import asyncio
    exit_code = asyncio.run(main())
    exit(exit_code)
```

**4. Enhanced Statistics and Progress Reporting**

```python
def print_pipeline_statistics(discovery_result, processing_result, upload_result):
    """Enhanced statistics reporting based on Script 1 patterns"""
    print("\n" + "="*60)
    print("📊 PIPELINE EXECUTION STATISTICS")
    print("="*60)

    # Discovery Phase Stats
    print(f"\n📁 Discovery Phase:")
    print(f"   Total files discovered: {discovery_result.total_files}")
    print(f"   Files by type: {discovery_result.files_by_type}")
    if hasattr(discovery_result, 'skipped_files'):
        print(f"   Files skipped: {len(discovery_result.skipped_files)}")

    # Processing Phase Stats
    print(f"\n⚙️  Processing Phase:")
    print(f"   Successfully processed: {processing_result.successfully_processed}")
    print(f"   Failed processing: {processing_result.failed_documents}")
    print(f"   Processing time: {processing_result.processing_time:.2f}s")
    print(f"   Strategy used: {processing_result.strategy_name}")

    # Upload Phase Stats
    print(f"\n📤 Upload Phase:")
    print(f"   Documents uploaded: {upload_result.successfully_uploaded}")
    print(f"   Failed uploads: {upload_result.failed_uploads}")
    print(f"   Upload time: {upload_result.upload_time:.2f}s")

    # Overall Pipeline Stats
    total_time = getattr(discovery_result, 'discovery_time', 0) + processing_result.processing_time + upload_result.upload_time
    print(f"\n🎯 Overall Results:")
    print(f"   Total execution time: {total_time:.2f}s")

    if discovery_result.total_files > 0:
        success_rate = (upload_result.successfully_uploaded / discovery_result.total_files) * 100
        print(f"   Success rate: {success_rate:.1f}%")

    # Error Summary
    all_errors = []
    if discovery_result.errors:
        all_errors.extend(discovery_result.errors)
    if processing_result.errors:
        all_errors.extend(processing_result.errors)
    if upload_result.errors:
        all_errors.extend(upload_result.errors)

    if all_errors:
        print(f"\n⚠️  Errors encountered: {len(all_errors)}")
        for i, error in enumerate(all_errors[:5], 1):  # Show first 5 errors
            print(f"   {i}. {error}")
        if len(all_errors) > 5:
            print(f"   ... and {len(all_errors) - 5} more errors")
```

#### Enhanced Key Features

- **🔄 Complete Pipeline Integration**: Uses DocumentProcessingPipeline.run_complete_pipeline() for full 3-phase processing
- **🗑️ Advanced Force Reset**: Complete index and tracker cleanup with verification
- **📊 Comprehensive Progress Tracking**: Real-time feedback with detailed statistics
- **🛡️ Robust Error Handling**: Graceful failure recovery with helpful guidance
- **🔍 Dry Run Capability**: Preview processing without making changes
- **⚡ Resume Support**: Can restart interrupted processing using tracker
- **📈 Enhanced Statistics**: Detailed metrics for all pipeline phases
- **🎯 Path Flexibility**: Unified file and directory handling via GeneralDocumentDiscoveryStrategy

---

### Phase 3: Script 3 - Context-Based Deletion Script

#### File Location

```
src/document_upload/common_scripts/delete_by_file_path.py
```

#### Core Architecture

```python
# Key Components:
- Context + filename precise matching
- Multiple match resolution
- Preview mode for safety
- Tracker cleanup integration
- Comprehensive deletion reporting
```

#### Implementation Details

**1. Document Search and Matching**

```python
def find_matching_documents(search_service: AzureCognitiveSearch,
                          context_name: str,
                          file_name: str) -> List[Dict[str, Any]]:
    """Find all document chunks matching context + filename"""

    # Use FilterBuilder for precise matching
    filters = {
        'context_name': context_name,
        'file_name': file_name
    }

    # Search for all matching chunks
    results = search_service.search_client.search(
        search_text="*",
        filter=FilterBuilder.build_filter(filters),
        select="id,file_name,context_name,chunk_index,title,file_path",
        top=1000  # Get all chunks
    )

    return list(results)
```

**2. Preview and Confirmation System**

```python
def preview_deletion_impact(matching_docs: List[Dict[str, Any]]):
    """Show detailed preview of what will be deleted"""

    if not matching_docs:
        print("🔍 No matching documents found.")
        return False

    print(f"📋 Found {len(matching_docs)} document chunks to delete:")
    print(f"   📄 File: {matching_docs[0]['file_name']}")
    print(f"   🏷️  Context: {matching_docs[0]['context_name']}")
    print(f"   📍 Path: {matching_docs[0].get('file_path', 'Unknown')}")
    print(f"   🧩 Chunks: {len(matching_docs)}")

    # Show chunk breakdown
    for i, doc in enumerate(matching_docs, 1):
        print(f"      {i}. Chunk {doc.get('chunk_index', 'N/A')} - {doc.get('title', 'No title')}")

    return True
```

**3. Atomic Deletion with Tracker Cleanup**

```python
async def delete_documents_and_cleanup_tracker(search_service: AzureCognitiveSearch,
                                              tracker: DocumentProcessingTracker,
                                              matching_docs: List[Dict[str, Any]]) -> Tuple[int, int, List[str]]:
    """Delete documents and clean up tracker atomically"""

    deleted_count = 0
    failed_count = 0
    errors = []
    file_paths_to_untrack = set()

    # Delete each document
    for doc in matching_docs:
        try:
            success = search_service.delete_document(doc['id'])
            if success:
                deleted_count += 1
                # Collect file paths for tracker cleanup
                if 'file_path' in doc:
                    file_paths_to_untrack.add(Path(doc['file_path']))
            else:
                failed_count += 1
        except Exception as e:
            failed_count += 1
            errors.append(f"Failed to delete {doc['id']}: {e}")

    # Clean up tracker for successfully deleted file paths
    for file_path in file_paths_to_untrack:
        tracker.mark_unprocessed(file_path)

    if file_paths_to_untrack:
        tracker.save()
        print(f"   📋 Cleaned up tracker for {len(file_paths_to_untrack)} file(s)")

    return deleted_count, failed_count, errors
```

**4. Command-Line Interface**

```python
def main():
    parser = argparse.ArgumentParser(description="Delete documents by context and filename")
    parser.add_argument("context_name", help="Context name to match")
    parser.add_argument("file_name", help="File name to match")
    parser.add_argument("--preview", action="store_true",
                       help="Preview what would be deleted without deleting")
    parser.add_argument("--force", action="store_true",
                       help="Delete without confirmation prompt")
    parser.add_argument("--stats", action="store_true",
                       help="Show deletion statistics")
```

#### Key Features

- **Precise Matching**: Context + filename combination
- **Safety Preview**: Show what will be deleted before deletion
- **Atomic Operations**: Delete documents and clean tracker together
- **Multi-Chunk Handling**: Handle all chunks for a file
- **Comprehensive Reporting**: Detailed deletion feedback

## 📋 Integration Considerations

### 1. Shared Dependencies

All scripts will share:

- Environment variable loading (`.env` file)
- Azure Cognitive Search service instance
- Document Processing Tracker instance
- Common error handling patterns
- Logging configuration

### 2. Error Handling Strategy

- **Graceful Degradation**: Continue processing on individual failures
- **Detailed Logging**: Comprehensive error reporting with context
- **Recovery Guidance**: Provide next steps for common errors
- **State Consistency**: Ensure tracker and index remain synchronized

### 3. Testing Strategy

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test end-to-end workflows
- **Edge Case Testing**: Handle missing files, invalid metadata, network failures
- **Performance Testing**: Validate with large document collections

### 4. Documentation Requirements

Each script needs:

- **Usage Examples**: Common use cases with sample commands
- **Metadata Schema Documentation**: Required and optional fields
- **Error Resolution Guide**: Common errors and solutions
- **Best Practices**: Recommended workflows and patterns

## 🚀 Implementation Timeline

### Week 1: Script 1 - Direct Metadata Upload

- Day 1-2: Core architecture and metadata validation
- Day 3-4: Processing strategy and file handling
- Day 5: Testing and documentation

### Week 2: Script 2 - Full Pipeline Upload

- Day 1-2: Pipeline integration and force reset
- Day 3-4: Command-line interface and error handling
- Day 5: Testing and documentation

### Week 3: Script 3 - Context-Based Deletion

- Day 1-2: Search and matching logic
- Day 3-4: Preview system and atomic deletion
- Day 5: Testing and documentation

### Week 4: Integration and Testing

- Day 1-2: End-to-end testing of all scripts
- Day 3-4: Documentation finalization
- Day 5: Performance optimization and deployment

## ✅ Success Criteria

1. **Functional Requirements Met**: All three scripts implement required functionality
2. **Schema Compliance**: Metadata validation ensures Azure Search schema compatibility
3. **Tracker Integration**: All scripts properly use DocumentProcessingTracker
4. **Error Recovery**: Robust error handling with helpful error messages
5. **Performance**: Efficient processing of large document collections
6. **Documentation**: Complete usage guides and examples
7. **Testing Coverage**: Comprehensive test suite with edge cases

## 🔧 Technical Implementation Notes

### Environment Setup

```bash
# Required environment variables (matching actual .env.example file)
AZURE_SEARCH_SERVICE=your-service-name
AZURE_SEARCH_KEY=your-search-admin-key
AZURE_SEARCH_INDEX=work-items-index
AZURE_OPENAI_ENDPOINT=https://your-service.openai.azure.com/
AZURE_OPENAI_KEY=your-openai-key
EMBEDDING_DEPLOYMENT=text-embedding-ada-002
PERSONAL_DOCUMENTATION_ROOT_DIRECTORY=path-to-docs

# Note: PERSONAL_DOCUMENTATION_ROOT_DIRECTORY is used by DocumentProcessingTracker
# for determining tracker file location. All other variables are required for
# Azure Cognitive Search and Azure OpenAI services integration.
```

### Common Imports Pattern

```python
# Standard pattern for all scripts
import os
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# Add src to path for imports
current_dir = Path(__file__).parent
src_dir = current_dir.parent.parent
sys.path.insert(0, str(src_dir))

# Import project modules
from common.azure_cognitive_search import get_azure_search_service
from document_upload.file_tracker import DocumentProcessingTracker
from document_upload.document_processing_pipeline import DocumentProcessingPipeline
```

This implementation plan provides a comprehensive roadmap for creating the three specialized document processing scripts while leveraging the existing sophisticated architecture and maintaining consistency with established patterns.
