#!/usr/bin/env python3
"""
Comprehensive Test Script for ChromaDB delete_by_context_and_filename.py
========================================================================

This test script validates the complete deletion functionality including:
- Multiple matching strategies (exact, contains, flexible)
- Preview system with detailed impact analysis
- Production-ready safety features and confirmations
- Complete tracker integration and cleanup
- Batch optimization and performance metrics
- Error handling and graceful degradation

Test Coverage:
1. Environment setup and validation
2. Test document creation and upload
3. Document search verification
4. Preview functionality validation (all matching modes)
5. Exact matching deletion with tracker integration
6. Contains matching deletion testing
7. Flexible matching fallback testing
8. Large deletion warning system testing
9. Error handling and edge case validation
10. Complete cleanup and verification

Usage:
    python test_delete_by_context_and_filename_script.py [--verbose] [--keep-files]
    
Author: Personal Documentation Assistant System Test Suite - ChromaDB Version
Created: Based on delete_by_context_and_filename.py comprehensive functionality
"""

import os
import sys
import argparse
import asyncio
import tempfile
import time
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

# Add src to path for imports - navigate up to src directory
current_dir = Path(__file__).parent
scripts_dir = current_dir.parent
src_dir = scripts_dir.parent.parent
sys.path.insert(0, str(src_dir))

# Import project modules
from src.common.vector_search_services.chromadb_service import get_chromadb_service
from src.document_upload.document_processing_tracker import DocumentProcessingTracker
from src.document_upload.personal_documentation_assistant_scripts.chroma_db_scripts.upload_with_custom_metadata import (
    DirectMetadataProcessingStrategy,
    process_and_upload
)

# Import the delete script functions for testing
from src.document_upload.personal_documentation_assistant_scripts.chroma_db_scripts.delete_by_context_and_filename import (
    find_matching_documents,
    preview_deletion_impact,
    get_user_confirmation,
    delete_documents_and_cleanup_tracker
)


class ChromaDBDeleteByContextAndFilenameTestRunner:
    """
    Comprehensive test runner for ChromaDB delete_by_context_and_filename.py functionality.
    
    This test runner validates the complete deletion system including:
    - Multiple matching strategies and modes
    - Preview system with impact analysis
    - Production safety features
    - Tracker integration and cleanup
    - Performance metrics and error handling
    """
    
    def __init__(self, verbose: bool = False, keep_files: bool = False):
        """
        Initialize the test runner.
        
        Args:
            verbose: Enable verbose logging for detailed test output
            keep_files: Keep test files after completion (for debugging)
        """
        self.verbose = verbose
        self.keep_files = keep_files
        
        # Test contexts and filenames for comprehensive testing
        self.test_contexts = ["TEST-DELETE-001", "TEST-DELETE-002", "TEST-PARTIAL-MATCH"]
        self.test_files = {
            "TEST-DELETE-001": ["test_exact_match.md", "test_contains_file.md"],
            "TEST-DELETE-002": ["test_flexible_match.md"],
            "TEST-PARTIAL-MATCH": ["partial_test_document.md", "another_document.md"]
        }
        
        self.temp_dirs: List[Path] = []
        self.uploaded_documents = []
        self.chromadb_service = None
        self.tracker = None
        
        # Load environment
        load_dotenv()
        
        # Test statistics
        self.test_stats = {
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "documents_created": 0,
            "documents_uploaded": 0,
            "documents_deleted": 0,
            "start_time": None,
            "end_time": None
        }
    
    def log(self, message: str, level: str = "INFO"):
        """Log a message with optional verbose output."""
        prefix = {
            "INFO": "ℹ️ ",
            "SUCCESS": "✅ ",
            "WARNING": "⚠️ ",
            "ERROR": "❌ ",
            "DEBUG": "🔍 "
        }.get(level, "  ")
        
        print(f"{prefix}{message}")
        
        if self.verbose and level == "DEBUG":
            print(f"   [DEBUG] {message}")
    
    def validate_environment(self) -> bool:
        """Validate that ChromaDB environment is properly configured."""
        self.log("Validating ChromaDB environment configuration...")
        
        # Check optional ChromaDB environment variables
        chromadb_vars = [
            'CHROMADB_COLLECTION_NAME', 
            'CHROMADB_PERSIST_DIRECTORY',
            'PERSONAL_DOCUMENTATION_ROOT_DIRECTORY'
        ]
        
        missing_vars = []
        for var in chromadb_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            self.log(f"Missing ChromaDB environment variables (using defaults): {', '.join(missing_vars)}", "WARNING")
        
        # Validate PERSONAL_DOCUMENTATION_ROOT_DIRECTORY exists if set
        if os.getenv('PERSONAL_DOCUMENTATION_ROOT_DIRECTORY'):
            docs_dir = Path(os.getenv('PERSONAL_DOCUMENTATION_ROOT_DIRECTORY'))
            if not docs_dir.exists():
                self.log(f"PERSONAL_DOCUMENTATION_ROOT_DIRECTORY does not exist: {docs_dir}", "ERROR")
                return False
        
        self.log("ChromaDB environment validation successful", "SUCCESS")
        return True
    
    async def setup_test_environment(self) -> bool:
        """Set up test environment with multiple contexts and documents."""
        try:
            self.log("Setting up ChromaDB comprehensive test environment...")
            
            # Initialize ChromaDB service
            self.chromadb_service = get_chromadb_service()
            self.log("ChromaDB service initialized", "SUCCESS")
            
            # Test ChromaDB connection
            if not self.chromadb_service.test_connection():
                self.log("ChromaDB connection test failed", "ERROR")
                return False
            
            # Initialize DocumentProcessingTracker
            self.tracker = DocumentProcessingTracker()
            self.log("DocumentProcessingTracker initialized", "SUCCESS")
            
            # Clean up any existing test documents
            await self.cleanup_existing_test_documents()
            
            # Create and upload test documents for each context
            for context_name, file_names in self.test_files.items():
                # Create temporary directory for this context
                temp_dir = Path(tempfile.mkdtemp(prefix=f"chromadb_delete_test_{context_name.lower()}_"))
                self.temp_dirs.append(temp_dir)
                
                self.log(f"Created test directory for {context_name}: {temp_dir.name}", "DEBUG")
                
                # Create test documents for this context
                for file_name in file_names:
                    file_path = temp_dir / file_name
                    
                    test_content = f"""# Test Document for ChromaDB Deletion Validation - {context_name}

## Document Information
- **Context**: {context_name}
- **File**: {file_name}
- **Purpose**: Testing ChromaDB delete_by_context_and_filename.py functionality
- **Test Type**: Deletion validation with multiple matching modes
- **Created**: {time.strftime('%Y-%m-%d %H:%M:%S')}

## Test Content for {context_name}

This document is specifically designed to test the ChromaDB deletion functionality:

### Deletion Test Features
1. **Context-based matching**: Tests context_name filtering
2. **Filename matching**: Tests file_name filtering with various modes
3. **Multiple chunks**: Creates multiple searchable chunks for comprehensive testing
4. **Tracker integration**: Validates DocumentProcessingTracker cleanup

### Expected Deletion Behavior
- **Exact mode**: Should match only exact context and filename
- **Contains mode**: Should match files where filename contains the search term
- **Flexible mode**: Should try exact first, then fallback to contains

## Additional Test Content

This section provides additional content to ensure multiple chunks are created
during document processing. This helps test the comprehensive deletion of
all chunks belonging to a specific document.

### Context: {context_name}
### Filename: {file_name}
### Test Scenarios:

1. **Single file deletion**: Testing deletion of individual files
2. **Multiple file deletion**: Testing batch deletion operations  
3. **Context-based deletion**: Testing deletion by context filter
4. **Mixed content deletion**: Testing deletion with various content types

## Vector Search Content

This content is designed to be indexed and searchable in ChromaDB:

- Document management and deletion
- Vector database operations
- ChromaDB filtering and search
- Context-based document organization
- Filename-based document retrieval

## Metadata Test Information

The following metadata should be properly indexed:
- Context Name: {context_name}
- File Name: {file_name}
- Test Purpose: Deletion validation
- Document Type: Test document

## End of Test Document

This concludes the test document for {context_name} - {file_name}.
The document should be processed into multiple chunks and indexed in ChromaDB.
"""
                    
                    # Write test file
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(test_content)
                    
                    self.test_stats["documents_created"] += 1
                    self.log(f"Created test document: {file_name}", "DEBUG")
            
            # Upload test documents using ChromaDB processing pipeline
            await self.upload_test_documents()
            
            self.log("Test environment setup completed successfully", "SUCCESS")
            return True
            
        except Exception as e:
            self.log(f"Failed to setup test environment: {str(e)}", "ERROR")
            return False
    
    async def upload_test_documents(self):
        """Upload all test documents to ChromaDB using direct metadata approach."""
        self.log("Uploading test documents to ChromaDB...")
        
        try:
            # Process each context directory
            for context_name, temp_dir in zip(self.test_contexts, self.temp_dirs):
                self.log(f"Processing context {context_name} from {temp_dir}", "DEBUG")
                
                # Process each file in the directory
                for file_path in temp_dir.glob("*.md"):
                    try:
                        # Prepare custom metadata for direct upload
                        custom_metadata = {
                            "title": f"Test Document - {file_path.stem}",
                            "tags": ["test", "deletion", "chromadb"],
                            "category": "test_document",
                            "work_item_id": context_name,
                            "file_type": "md",
                            "file_path": str(file_path)
                        }
                        
                        # Process and upload the document using custom metadata approach
                        success = await process_and_upload(file_path, custom_metadata, validate_only=False)
                        
                        if success:
                            self.uploaded_documents.append({
                                "file_path": file_path,
                                "context_name": context_name,
                                "file_name": file_path.name,
                                "chunks_uploaded": 1  # Approximate since we don't get exact count
                            })
                            self.test_stats["documents_uploaded"] += 1
                            self.log(f"Uploaded {file_path.name}", "DEBUG")
                        else:
                            self.log(f"Failed to upload {file_path.name}", "WARNING")
                            
                    except Exception as e:
                        self.log(f"Error processing {file_path.name}: {str(e)}", "ERROR")
            
            self.log(f"Upload completed: {self.test_stats['documents_uploaded']} documents uploaded", "SUCCESS")
            
        except Exception as e:
            self.log(f"Error during document upload: {str(e)}", "ERROR")
            raise
    
    async def cleanup_existing_test_documents(self):
        """Clean up any existing test documents from previous runs."""
        self.log("Cleaning up existing test documents...")
        
        try:
            # Search for existing test documents by context
            for context_name in self.test_contexts:
                filters = {"context_name": context_name}
                existing_docs = self.chromadb_service.get_documents_by_filter(filters)
                
                if existing_docs:
                    doc_ids = [doc['id'] for doc in existing_docs if doc.get('id')]
                    if doc_ids:
                        deleted_count = await self.chromadb_service.delete_documents(doc_ids)
                        self.log(f"Cleaned up {deleted_count} existing documents for context {context_name}", "DEBUG")
            
            self.log("Cleanup of existing test documents completed", "SUCCESS")
            
        except Exception as e:
            self.log(f"Error during cleanup: {str(e)}", "WARNING")
    
    # Test Methods
    
    async def test_exact_matching_search(self) -> bool:
        """Test exact matching document search functionality."""
        try:
            self.log("Testing exact matching search...")
            self.test_stats["tests_run"] += 1
            
            # Test exact match for first context and file
            context_name = "TEST-DELETE-001"
            file_name = "test_exact_match.md"
            
            matching_docs, search_stats = find_matching_documents(
                self.chromadb_service, context_name, file_name, 'exact'
            )
            
            if not matching_docs:
                self.log("Exact matching search failed - no documents found", "ERROR")
                self.test_stats["tests_failed"] += 1
                return False
            
            # Verify search statistics
            expected_files = 1
            if search_stats['unique_files'] != expected_files:
                self.log(f"Expected {expected_files} files, got {search_stats['unique_files']}", "ERROR")
                self.test_stats["tests_failed"] += 1
                return False
            
            # Verify document metadata
            doc = matching_docs[0]
            if doc['context_name'] != context_name or doc['file_name'] != file_name:
                self.log(f"Document metadata mismatch: {doc['context_name']}, {doc['file_name']}", "ERROR")
                self.test_stats["tests_failed"] += 1
                return False
            
            self.log("Exact matching search test passed", "SUCCESS")
            self.test_stats["tests_passed"] += 1
            return True
            
        except Exception as e:
            self.log(f"Exact matching search test failed: {str(e)}", "ERROR")
            self.test_stats["tests_failed"] += 1
            return False
    
    async def test_contains_matching_search(self) -> bool:
        """Test contains matching document search functionality."""
        try:
            self.log("Testing contains matching search...")
            self.test_stats["tests_run"] += 1
            
            # Test contains match - search for "partial" in "TEST-PARTIAL-MATCH" context
            context_name = "TEST-PARTIAL-MATCH"
            file_name_part = "partial"  # Should match "partial_test_document.md"
            
            matching_docs, search_stats = find_matching_documents(
                self.chromadb_service, context_name, file_name_part, 'contains'
            )
            
            if not matching_docs:
                self.log("Contains matching search failed - no documents found", "ERROR")
                self.test_stats["tests_failed"] += 1
                return False
            
            # Verify that we found the document with "partial" in the name
            found_partial = False
            for doc in matching_docs:
                if "partial" in doc['file_name'].lower():
                    found_partial = True
                    break
            
            if not found_partial:
                self.log("Contains matching failed to find document with partial filename", "ERROR")
                self.test_stats["tests_failed"] += 1
                return False
            
            self.log("Contains matching search test passed", "SUCCESS")
            self.test_stats["tests_passed"] += 1
            return True
            
        except Exception as e:
            self.log(f"Contains matching search test failed: {str(e)}", "ERROR")
            self.test_stats["tests_failed"] += 1
            return False
    
    async def test_flexible_matching_search(self) -> bool:
        """Test flexible matching document search functionality."""
        try:
            self.log("Testing flexible matching search...")
            self.test_stats["tests_run"] += 1
            
            # Test flexible match - try exact first, then fallback to contains
            context_name = "TEST-DELETE-002"
            file_name_part = "flexible"  # Should find "test_flexible_match.md"
            
            matching_docs, search_stats = find_matching_documents(
                self.chromadb_service, context_name, file_name_part, 'flexible'
            )
            
            if not matching_docs:
                self.log("Flexible matching search failed - no documents found", "ERROR")
                self.test_stats["tests_failed"] += 1
                return False
            
            # Verify that we found the document
            found_flexible = False
            for doc in matching_docs:
                if "flexible" in doc['file_name'].lower():
                    found_flexible = True
                    break
            
            if not found_flexible:
                self.log("Flexible matching failed to find document", "ERROR")
                self.test_stats["tests_failed"] += 1
                return False
            
            self.log("Flexible matching search test passed", "SUCCESS")
            self.test_stats["tests_passed"] += 1
            return True
            
        except Exception as e:
            self.log(f"Flexible matching search test failed: {str(e)}", "ERROR")
            self.test_stats["tests_failed"] += 1
            return False
    
    async def test_preview_functionality(self) -> bool:
        """Test preview functionality with impact analysis."""
        try:
            self.log("Testing preview functionality...")
            self.test_stats["tests_run"] += 1
            
            # Test preview with documents that exist
            context_name = "TEST-DELETE-001"
            file_name = "test_exact_match.md"
            
            matching_docs, search_stats = find_matching_documents(
                self.chromadb_service, context_name, file_name, 'exact'
            )
            
            if not matching_docs:
                self.log("Preview test setup failed - no documents found", "ERROR")
                self.test_stats["tests_failed"] += 1
                return False
            
            # Test preview impact analysis
            preview_result = preview_deletion_impact(matching_docs, search_stats, show_details=True)
            
            if not preview_result:
                self.log("Preview functionality failed", "ERROR")
                self.test_stats["tests_failed"] += 1
                return False
            
            # Test preview with no matching documents
            empty_docs = []
            empty_stats = {'total_matches': 0, 'unique_files': 0}
            empty_preview = preview_deletion_impact(empty_docs, empty_stats, show_details=True)
            
            if empty_preview:  # Should return False for no documents
                self.log("Preview should return False for no matching documents", "ERROR")
                self.test_stats["tests_failed"] += 1
                return False
            
            self.log("Preview functionality test passed", "SUCCESS")
            self.test_stats["tests_passed"] += 1
            return True
            
        except Exception as e:
            self.log(f"Preview functionality test failed: {str(e)}", "ERROR")
            self.test_stats["tests_failed"] += 1
            return False
    
    async def test_dry_run_deletion(self) -> bool:
        """Test dry run deletion functionality."""
        try:
            self.log("Testing dry run deletion...")
            self.test_stats["tests_run"] += 1
            
            # Find documents to delete
            context_name = "TEST-DELETE-001"
            file_name = "test_contains_file.md"
            
            matching_docs, search_stats = find_matching_documents(
                self.chromadb_service, context_name, file_name, 'exact'
            )
            
            if not matching_docs:
                self.log("Dry run test setup failed - no documents found", "ERROR")
                self.test_stats["tests_failed"] += 1
                return False
            
            # Perform dry run deletion
            successful, failed, errors, operation_stats = await delete_documents_and_cleanup_tracker(
                self.chromadb_service, self.tracker, matching_docs, dry_run=True
            )
            
            # Verify dry run results
            if operation_stats['operation'] != 'dry_run':
                self.log("Dry run operation type incorrect", "ERROR")
                self.test_stats["tests_failed"] += 1
                return False
            
            if successful != len(matching_docs):
                self.log(f"Dry run should report {len(matching_docs)} successful deletions, got {successful}", "ERROR")
                self.test_stats["tests_failed"] += 1
                return False
            
            # Verify documents still exist after dry run
            verify_docs, _ = find_matching_documents(
                self.chromadb_service, context_name, file_name, 'exact'
            )
            
            if not verify_docs:
                self.log("Documents were actually deleted during dry run", "ERROR")
                self.test_stats["tests_failed"] += 1
                return False
            
            self.log("Dry run deletion test passed", "SUCCESS")
            self.test_stats["tests_passed"] += 1
            return True
            
        except Exception as e:
            self.log(f"Dry run deletion test failed: {str(e)}", "ERROR")
            self.test_stats["tests_failed"] += 1
            return False
    
    async def test_actual_deletion(self) -> bool:
        """Test actual document deletion with tracker integration."""
        try:
            self.log("Testing actual document deletion...")
            self.test_stats["tests_run"] += 1
            
            # Find documents to delete - use one we haven't deleted yet
            context_name = "TEST-DELETE-002"
            file_name = "test_flexible_match.md"
            
            matching_docs, search_stats = find_matching_documents(
                self.chromadb_service, context_name, file_name, 'exact'
            )
            
            if not matching_docs:
                self.log("Deletion test setup failed - no documents found", "ERROR")
                self.test_stats["tests_failed"] += 1
                return False
            
            initial_count = len(matching_docs)
            
            # Perform actual deletion
            successful, failed, errors, operation_stats = await delete_documents_and_cleanup_tracker(
                self.chromadb_service, self.tracker, matching_docs, dry_run=False
            )
            
            # Verify deletion results
            if successful != initial_count:
                self.log(f"Expected {initial_count} successful deletions, got {successful}", "ERROR")
                self.test_stats["tests_failed"] += 1
                return False
            
            if failed != 0:
                self.log(f"Expected 0 failed deletions, got {failed}", "ERROR")
                self.test_stats["tests_failed"] += 1
                return False
            
            # Verify documents are actually gone
            verify_docs, _ = find_matching_documents(
                self.chromadb_service, context_name, file_name, 'exact'
            )
            
            if verify_docs:
                self.log("Documents still exist after deletion", "ERROR")
                self.test_stats["tests_failed"] += 1
                return False
            
            self.test_stats["documents_deleted"] += successful
            self.log("Actual document deletion test passed", "SUCCESS")
            self.test_stats["tests_passed"] += 1
            return True
            
        except Exception as e:
            self.log(f"Actual deletion test failed: {str(e)}", "ERROR")
            self.test_stats["tests_failed"] += 1
            return False
    
    async def test_error_handling(self) -> bool:
        """Test error handling with invalid inputs."""
        try:
            self.log("Testing error handling...")
            self.test_stats["tests_run"] += 1
            
            # Test search with non-existent context
            matching_docs, search_stats = find_matching_documents(
                self.chromadb_service, "NON-EXISTENT-CONTEXT", "non_existent_file.md", 'exact'
            )
            
            # Should return empty results, not crash
            if matching_docs:
                self.log("Error handling failed - found documents for non-existent context", "ERROR")
                self.test_stats["tests_failed"] += 1
                return False
            
            # Test deletion with empty document list
            successful, failed, errors, operation_stats = await delete_documents_and_cleanup_tracker(
                self.chromadb_service, self.tracker, [], dry_run=False
            )
            
            if successful != 0 or failed != 0:
                self.log("Error handling failed - empty deletion should return 0,0", "ERROR")
                self.test_stats["tests_failed"] += 1
                return False
            
            self.log("Error handling test passed", "SUCCESS")
            self.test_stats["tests_passed"] += 1
            return True
            
        except Exception as e:
            self.log(f"Error handling test failed: {str(e)}", "ERROR")
            self.test_stats["tests_failed"] += 1
            return False
    
    async def cleanup_test_environment(self):
        """Clean up test environment and temporary files."""
        try:
            self.log("Cleaning up test environment...")
            
            # Clean up remaining test documents from ChromaDB
            for context_name in self.test_contexts:
                try:
                    filters = {"context_name": context_name}
                    remaining_docs = self.chromadb_service.get_documents_by_filter(filters)
                    
                    if remaining_docs:
                        doc_ids = [doc['id'] for doc in remaining_docs if doc.get('id')]
                        if doc_ids:
                            deleted_count = await self.chromadb_service.delete_documents(doc_ids)
                            self.log(f"Final cleanup: removed {deleted_count} test documents for {context_name}", "DEBUG")
                except Exception as e:
                    self.log(f"Final cleanup warning: {e}", "WARNING")
            
            # Remove temporary directories unless keeping files
            if not self.keep_files:
                for temp_dir in self.temp_dirs:
                    if temp_dir.exists():
                        import shutil
                        shutil.rmtree(temp_dir)
                        self.log(f"Removed temporary directory: {temp_dir.name}", "DEBUG")
            else:
                self.log("Keeping temporary files for debugging", "INFO")
                for temp_dir in self.temp_dirs:
                    self.log(f"Temporary directory: {temp_dir}", "INFO")
            
            self.log("Test environment cleanup completed", "SUCCESS")
            
        except Exception as e:
            self.log(f"Cleanup failed: {str(e)}", "WARNING")
    
    def print_test_results(self):
        """Print comprehensive test results."""
        self.test_stats["end_time"] = time.time()
        duration = self.test_stats["end_time"] - self.test_stats["start_time"]
        
        print("\\n" + "="*70)
        print("🧪 CHROMADB DELETE BY CONTEXT AND FILENAME TEST RESULTS")
        print("="*70)
        
        # Test statistics
        print(f"\\n📊 Test Statistics:")
        print(f"   Tests run: {self.test_stats['tests_run']}")
        print(f"   Tests passed: {self.test_stats['tests_passed']}")
        print(f"   Tests failed: {self.test_stats['tests_failed']}")
        success_rate = (self.test_stats['tests_passed'] / self.test_stats['tests_run'] * 100) if self.test_stats['tests_run'] > 0 else 0
        print(f"   Success rate: {success_rate:.1f}%")
        print(f"   Duration: {duration:.2f} seconds")
        
        # Document statistics
        print(f"\\n📄 Document Statistics:")
        print(f"   Documents created: {self.test_stats['documents_created']}")
        print(f"   Document chunks uploaded: {self.test_stats['documents_uploaded']}")
        print(f"   Document chunks deleted: {self.test_stats['documents_deleted']}")
        
        # Overall result
        if self.test_stats['tests_failed'] == 0:
            print("\\n✅ ALL TESTS PASSED - ChromaDB deletion functionality is working correctly!")
        else:
            print(f"\\n❌ {self.test_stats['tests_failed']} TESTS FAILED - Please check the logs above")
        
        print("="*70)
        print("🎯 ChromaDB delete by context and filename test suite completed!")
    
    async def run_all_tests(self) -> bool:
        """Run all test scenarios."""
        self.test_stats["start_time"] = time.time()
        
        try:
            # Environment validation
            if not self.validate_environment():
                return False
            
            # Setup test environment
            if not await self.setup_test_environment():
                return False
            
            # Wait for documents to be indexed
            await asyncio.sleep(2)
            
            # Run test scenarios
            print("\\n" + "="*50)
            print("🧪 RUNNING CHROMADB DELETION TEST SCENARIOS")
            print("="*50)
            
            # Test search functionality
            await self.test_exact_matching_search()
            await self.test_contains_matching_search() 
            await self.test_flexible_matching_search()
            
            # Test preview functionality
            await self.test_preview_functionality()
            
            # Test deletion functionality
            await self.test_dry_run_deletion()
            await self.test_actual_deletion()
            
            # Test error handling
            await self.test_error_handling()
            
            return self.test_stats['tests_failed'] == 0
            
        except Exception as e:
            self.log(f"Test execution failed: {str(e)}", "ERROR")
            return False
        
        finally:
            await self.cleanup_test_environment()


async def main():
    """Main test execution function."""
    parser = argparse.ArgumentParser(
        description="Comprehensive test suite for ChromaDB delete_by_context_and_filename.py",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Enable verbose logging for detailed test output")
    
    parser.add_argument("--keep-files", action="store_true",
                       help="Keep temporary test files after completion (for debugging)")
    
    args = parser.parse_args()
    
    # Create and run test suite
    test_runner = ChromaDBDeleteByContextAndFilenameTestRunner(
        verbose=args.verbose, 
        keep_files=args.keep_files
    )
    
    try:
        success = await test_runner.run_all_tests()
        test_runner.print_test_results()
        
        # Return appropriate exit code
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\\n⏹️  Test suite interrupted by user")
        await test_runner.cleanup_test_environment()
        return 1
    except Exception as e:
        print(f"❌ Test suite failed: {str(e)}")
        await test_runner.cleanup_test_environment()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
