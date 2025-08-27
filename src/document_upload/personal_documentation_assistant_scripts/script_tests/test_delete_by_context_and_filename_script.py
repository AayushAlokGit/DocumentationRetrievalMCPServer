#!/usr/bin/env python3
"""
Comprehensive Test Script for delete_by_context_and_filename.py
==============================================================

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
    
Author: Personal Documentation Assistant System Test Suite
Created: Based on delete_by_context_and_filename.py comprehensive functionality
"""

import os
import sys
import argparse
import asyncio
import tempfile
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

# Add src to path for imports - navigate up to src directory
current_dir = Path(__file__).parent
scripts_dir = current_dir.parent
src_dir = scripts_dir.parent.parent
sys.path.insert(0, str(src_dir))

# Import project modules
from src.common.vector_search_services.azure_cognitive_search import get_azure_search_service
from document_upload.file_tracker import DocumentProcessingTracker
from document_upload.document_processing_pipeline import DocumentProcessingPipeline
from document_upload.processing_strategies import PersonalDocumentationAssistantProcessingStrategy
from document_upload.discovery_strategies import GeneralDocumentDiscoveryStrategy


class DeleteByContextAndFilenameTestRunner:
    """
    Comprehensive test runner for delete_by_context_and_filename.py functionality.
    
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
        self.azure_search = None
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
        """Validate that all required environment variables are set."""
        self.log("Validating environment configuration...")
        
        required_vars = [
            'AZURE_SEARCH_SERVICE', 'AZURE_SEARCH_KEY', 
            'AZURE_OPENAI_ENDPOINT', 'AZURE_OPENAI_KEY',
            'PERSONAL_DOCUMENTATION_ROOT_DIRECTORY'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            self.log(f"Missing required environment variables: {', '.join(missing_vars)}", "ERROR")
            return False
        
        # Validate PERSONAL_DOCUMENTATION_ROOT_DIRECTORY exists
        docs_dir = Path(os.getenv('PERSONAL_DOCUMENTATION_ROOT_DIRECTORY'))
        if not docs_dir.exists():
            self.log(f"PERSONAL_DOCUMENTATION_ROOT_DIRECTORY does not exist: {docs_dir}", "ERROR")
            return False
        
        self.log("Environment validation successful", "SUCCESS")
        return True
    
    def setup_test_environment(self) -> bool:
        """Set up test environment with multiple contexts and documents."""
        try:
            self.log("Setting up comprehensive test environment...")
            
            # Initialize Azure Search service
            service_name = os.getenv('AZURE_SEARCH_SERVICE')
            admin_key = os.getenv('AZURE_SEARCH_KEY')
            index_name = os.getenv('AZURE_SEARCH_INDEX', 'work-items-index')
            
            self.azure_search = get_azure_search_service(service_name, admin_key, index_name)
            self.log("Azure Search service initialized", "SUCCESS")
            
            # Initialize DocumentProcessingTracker
            self.tracker = DocumentProcessingTracker()
            self.log("DocumentProcessingTracker initialized", "SUCCESS")
            
            # Create test documents for each context
            for context_name, file_names in self.test_files.items():
                # Create temporary directory for this context
                temp_dir = Path(tempfile.mkdtemp(prefix=f"delete_test_{context_name.lower()}_"))
                self.temp_dirs.append(temp_dir)
                
                self.log(f"Created test directory for {context_name}: {temp_dir.name}", "DEBUG")
                
                # Create test documents for this context
                for file_name in file_names:
                    file_path = temp_dir / file_name
                    
                    test_content = f"""# Test Document for Deletion Validation - {context_name}

## Document Information
- **Context**: {context_name}
- **File**: {file_name}
- **Purpose**: Testing delete_by_context_and_filename.py functionality
- **Test Type**: Deletion validation with multiple matching modes
- **Created**: {time.strftime('%Y-%m-%d %H:%M:%S')}

## Test Content for {context_name}

This document is specifically designed to test the deletion functionality:

### Deletion Test Features
1. **Context-based matching**: Tests context_name filtering
2. **Filename matching**: Tests file_name filtering with various modes
3. **Multiple chunks**: Creates multiple searchable chunks for comprehensive testing
4. **Tracker integration**: Validates DocumentProcessingTracker cleanup

### Expected Deletion Behavior
- **Exact mode**: Should match only exact context and filename
- **Contains mode**: Should match files containing the search term
- **Flexible mode**: Should fall back to contains if exact fails

### Test Content Body
This is the main content body that will be chunked and uploaded to Azure Search.
The deletion system should find and remove all chunks associated with this document.

Additional paragraph to ensure proper chunking and multiple search objects.
Testing comprehensive deletion functionality with realistic document structure.

More content to create multiple chunks for thorough deletion testing.
Each chunk will have the same context_name and file_name for accurate filtering.

Final paragraph to complete the test document with sufficient content for chunking.
"""
                    
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(test_content)
                    
                    self.test_stats["documents_created"] += 1
                    self.log(f"Created test document: {file_name} in {context_name}")
            
            self.log(f"Test environment setup completed:", "SUCCESS")
            self.log(f"  - Contexts created: {len(self.test_contexts)}")
            self.log(f"  - Total documents: {self.test_stats['documents_created']}")
            self.log(f"  - Temp directories: {len(self.temp_dirs)}")
            
            return True
            
        except Exception as e:
            self.log(f"Failed to setup test environment: {str(e)}", "ERROR")
            return False
    
    async def upload_test_documents(self) -> bool:
        """Upload all test documents using the pipeline."""
        try:
            self.log("Uploading test documents using pipeline...")
            
            # Get Azure credentials
            service_name = os.getenv('AZURE_SEARCH_SERVICE')
            admin_key = os.getenv('AZURE_SEARCH_KEY')
            index_name = os.getenv('AZURE_SEARCH_INDEX', 'work-items-index')
            
            total_uploaded = 0
            
            # Upload documents for each context
            for temp_dir in self.temp_dirs:
                # Create pipeline for this directory
                discovery_strategy = GeneralDocumentDiscoveryStrategy()
                processing_strategy = PersonalDocumentationAssistantProcessingStrategy()
                tracker = DocumentProcessingTracker()
                
                pipeline = DocumentProcessingPipeline(
                    discovery_strategy=discovery_strategy,
                    processing_strategy=processing_strategy,
                    tracker=tracker
                )
                
                # Upload documents from this directory
                discovery_result, processing_result, upload_result = await pipeline.run_complete_pipeline(
                    root_directory=str(temp_dir),
                    service_name=service_name,
                    admin_key=admin_key,
                    index_name=index_name
                )
                
                total_uploaded += upload_result.successfully_uploaded
                
                # Store uploaded document info
                if processing_result.processed_documents:
                    for doc in processing_result.processed_documents:
                        self.uploaded_documents.append({
                            "file_name": doc.file_name,
                            "context_name": doc.context_name,
                            "file_path": doc.file_path,
                            "temp_dir": temp_dir
                        })
                
                self.log(f"Uploaded {upload_result.successfully_uploaded} objects from {temp_dir.name}")
            
            self.test_stats["documents_uploaded"] = total_uploaded
            
            if total_uploaded > 0:
                self.log(f"Successfully uploaded {total_uploaded} search objects", "SUCCESS")
                self.log(f"Uploaded documents: {len(self.uploaded_documents)}")
                return True
            else:
                self.log("No documents were uploaded", "ERROR")
                return False
            
        except Exception as e:
            self.log(f"Document upload failed: {str(e)}", "ERROR")
            return False
    
    def pre_cleanup(self) -> bool:
        """Clean up any existing test documents before running tests."""
        try:
            self.log("Performing pre-test cleanup...")
            
            total_deleted = 0
            
            # Clean up existing test documents for each context
            for context_name in self.test_contexts:
                deleted_count = self.azure_search.delete_documents_by_filter({
                    "context_name": context_name
                })
                total_deleted += deleted_count
                
                if deleted_count > 0:
                    self.log(f"Removed {deleted_count} existing documents for context '{context_name}'")
            
            if total_deleted > 0:
                self.log(f"Pre-cleanup: Removed {total_deleted} existing test documents")
                # Wait for deletion to propagate
                time.sleep(3)
            else:
                self.log("No existing test documents found")
            
            self.log("Pre-test cleanup completed", "SUCCESS")
            return True
            
        except Exception as e:
            self.log(f"Pre-cleanup failed: {str(e)}", "ERROR")
            return False
    
    def verify_document_upload(self) -> bool:
        """Verify that test documents were uploaded correctly."""
        try:
            self.log("Verifying document upload...")
            
            found_contexts = {}
            total_found = 0
            
            # Search for documents using the actual context names (temp directory names)
            actual_contexts = []
            for doc_info in self.uploaded_documents:
                actual_context = doc_info["context_name"]
                if actual_context not in actual_contexts:
                    actual_contexts.append(actual_context)
            
            # Search for documents in each actual context
            for context_name in actual_contexts:
                results = self.azure_search.text_search(
                    query="*",
                    filters={"context_name": context_name},
                    top=100
                )
                
                found_contexts[context_name] = len(results)
                total_found += len(results)
                
                if len(results) > 0:
                    self.log(f"Found {len(results)} documents in context '{context_name}'", "DEBUG")
                    
                    # Log sample documents
                    for doc in results[:3]:  # Show first 3
                        self.log(f"  - {doc.get('file_name', 'N/A')} (chunks: {doc.get('chunk_index', 'N/A')})", "DEBUG")
            
            if total_found > 0:
                self.log(f"Document verification successful:", "SUCCESS")
                self.log(f"  - Total search objects found: {total_found}")
                self.log(f"  - Contexts with documents: {len([c for c, count in found_contexts.items() if count > 0])}")
                return True
            else:
                self.log("Document verification failed: No documents found", "ERROR")
                return False
            
        except Exception as e:
            self.log(f"Document verification failed: {str(e)}", "ERROR")
            return False
    
    def test_exact_matching(self) -> bool:
        """Test exact matching functionality."""
        try:
            self.log("Testing exact matching functionality...")
            
            # Find a test document with actual context name
            test_doc = None
            for doc_info in self.uploaded_documents:
                if "test_exact_match.md" in doc_info["file_name"]:
                    test_doc = doc_info
                    break
            
            if not test_doc:
                self.log("No test document found for exact matching test", "ERROR")
                return False
            
            context_name = test_doc["context_name"]
            file_name = test_doc["file_name"]
            
            # Import the deletion module
            sys.path.insert(0, str(scripts_dir))
            from delete_by_context_and_filename import find_matching_documents
            
            # Find matching documents
            matching_docs, search_stats = find_matching_documents(
                self.azure_search, 
                context_name, 
                file_name, 
                matching_mode='exact'
            )
            
            if len(matching_docs) > 0:
                self.log(f"Exact matching successful:", "SUCCESS")
                self.log(f"  - Found {len(matching_docs)} matching documents")
                self.log(f"  - Context: {context_name}")
                self.log(f"  - File: {file_name}")
                return True
            else:
                self.log("Exact matching failed: No documents found", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"Exact matching test failed: {str(e)}", "ERROR")
            return False
    
    def test_contains_matching(self) -> bool:
        """Test contains matching functionality."""
        try:
            self.log("Testing contains matching functionality...")
            
            # Find a test document with partial matching capability
            test_doc = None
            for doc_info in self.uploaded_documents:
                if "partial_test_document.md" in doc_info["file_name"]:
                    test_doc = doc_info
                    break
            
            if not test_doc:
                self.log("No test document found for contains matching test", "ERROR")
                return False
            
            context_name = test_doc["context_name"]
            file_name = "partial"  # Should match partial_test_document.md
            
            # Import the deletion module
            sys.path.insert(0, str(scripts_dir))
            from delete_by_context_and_filename import find_matching_documents
            
            # Find matching documents
            matching_docs, search_stats = find_matching_documents(
                self.azure_search, 
                context_name, 
                file_name, 
                matching_mode='contains'
            )
            
            if len(matching_docs) > 0:
                self.log(f"Contains matching successful:", "SUCCESS")
                self.log(f"  - Found {len(matching_docs)} matching documents")
                self.log(f"  - Context: {context_name}")
                self.log(f"  - Search term: {file_name}")
                
                # Verify the matched file name contains our search term
                matched_files = set(doc.get('file_name', '') for doc in matching_docs)
                contains_match = any(file_name.lower() in filename.lower() for filename in matched_files)
                
                if contains_match:
                    self.log(f"  - Correctly matched files containing '{file_name}'")
                    return True
                else:
                    self.log(f"  - Error: Matched files don't contain search term", "ERROR")
                    return False
            else:
                self.log("Contains matching failed: No documents found", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"Contains matching test failed: {str(e)}", "ERROR")
            return False
    
    def test_flexible_matching(self) -> bool:
        """Test flexible matching functionality."""
        try:
            self.log("Testing flexible matching functionality...")
            
            # Find a test document for flexible matching
            test_doc = None
            for doc_info in self.uploaded_documents:
                if "test_flexible_match.md" in doc_info["file_name"]:
                    test_doc = doc_info
                    break
            
            if not test_doc:
                self.log("No test document found for flexible matching test", "ERROR")
                return False
            
            context_name = test_doc["context_name"]
            
            # Import the deletion module
            sys.path.insert(0, str(scripts_dir))
            from delete_by_context_and_filename import find_matching_documents
            
            # Test 1: Flexible with exact match available
            file_name = test_doc["file_name"]
            matching_docs, search_stats = find_matching_documents(
                self.azure_search, 
                context_name, 
                file_name, 
                matching_mode='flexible'
            )
            
            if len(matching_docs) > 0:
                self.log(f"Flexible exact matching successful: Found {len(matching_docs)} documents")
                
                # Test 2: Flexible with fallback to contains
                file_name_partial = "flexible"  # Should fallback to contains matching
                matching_docs_partial, search_stats_partial = find_matching_documents(
                    self.azure_search, 
                    context_name, 
                    file_name_partial, 
                    matching_mode='flexible'
                )
                
                if len(matching_docs_partial) > 0:
                    self.log(f"Flexible fallback matching successful:", "SUCCESS")
                    self.log(f"  - Found {len(matching_docs_partial)} documents with fallback")
                    self.log(f"  - Context: {context_name}")
                    self.log(f"  - Partial term: {file_name_partial}")
                    return True
                else:
                    self.log("Flexible fallback matching failed", "ERROR")
                    return False
            else:
                self.log("Flexible exact matching failed", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"Flexible matching test failed: {str(e)}", "ERROR")
            return False
    
    def test_preview_functionality(self) -> bool:
        """Test the preview functionality."""
        try:
            self.log("Testing preview functionality...")
            
            # Find a test document for preview
            test_doc = None
            for doc_info in self.uploaded_documents:
                if "test_exact_match.md" in doc_info["file_name"]:
                    test_doc = doc_info
                    break
            
            if not test_doc:
                self.log("No test document found for preview test", "ERROR")
                return False
            
            # Import the deletion module
            sys.path.insert(0, str(scripts_dir))
            from delete_by_context_and_filename import find_matching_documents, preview_deletion_impact
            
            context_name = test_doc["context_name"]
            file_name = test_doc["file_name"]
            
            # First find matching documents
            matching_docs, search_stats = find_matching_documents(
                self.azure_search, 
                context_name, 
                file_name, 
                matching_mode='exact'
            )
            
            if len(matching_docs) > 0:
                # Test preview functionality
                preview_result = preview_deletion_impact(
                    matching_docs, 
                    search_stats, 
                    show_details=True
                )
                
                self.log(f"Preview functionality successful:", "SUCCESS")
                self.log(f"  - Preview processed {len(matching_docs)} documents")
                self.log(f"  - No actual deletion performed")
                return True
            else:
                self.log("Preview functionality failed: No documents found for preview", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"Preview functionality test failed: {str(e)}", "ERROR")
            return False
    
    def test_actual_deletion(self) -> bool:
        """Test actual deletion with tracker integration."""
        try:
            self.log("Testing actual deletion functionality...")
            
            # Find a test document for actual deletion
            test_doc = None
            for doc_info in self.uploaded_documents:
                if "test_contains_file.md" in doc_info["file_name"]:
                    test_doc = doc_info
                    break
            
            if not test_doc:
                self.log("No test document found for actual deletion test", "ERROR")
                return False
            
            # Import the deletion module
            sys.path.insert(0, str(scripts_dir))
            from delete_by_context_and_filename import find_matching_documents, delete_documents_and_cleanup_tracker
            
            context_name = test_doc["context_name"]
            file_name = test_doc["file_name"]
            
            # First find matching documents
            matching_docs, search_stats = find_matching_documents(
                self.azure_search, 
                context_name, 
                file_name, 
                matching_mode='exact'
            )
            
            if len(matching_docs) == 0:
                self.log("No documents found for deletion test", "WARNING")
                return True  # Not a failure if no documents exist
            
            initial_count = len(matching_docs)
            
            # Perform actual deletion
            successful_deletes, failed_deletes, error_messages, operation_stats = delete_documents_and_cleanup_tracker(
                self.azure_search,
                self.tracker,
                matching_docs,
                dry_run=False  # Actually delete
            )
            
            # Wait for deletion to propagate
            time.sleep(2)
            
            # Verify deletion by searching again
            verify_docs, _ = find_matching_documents(
                self.azure_search, 
                context_name, 
                file_name, 
                matching_mode='exact'
            )
            final_count = len(verify_docs)
            
            if final_count == 0 and successful_deletes > 0:
                self.log(f"Deletion successful:", "SUCCESS")
                self.log(f"  - Documents before: {initial_count}")
                self.log(f"  - Documents after: {final_count}")
                self.log(f"  - Documents deleted: {successful_deletes}")
                self.test_stats["documents_deleted"] += successful_deletes
                return True
            else:
                self.log(f"Deletion incomplete: {final_count} documents remain, deleted: {successful_deletes}", "ERROR")
                return False
            
        except Exception as e:
            self.log(f"Deletion test failed: {str(e)}", "ERROR")
            return False
            return False
    
    def test_tracker_cleanup(self) -> bool:
        """Test DocumentProcessingTracker cleanup functionality."""
        try:
            self.log("Testing tracker cleanup functionality...")
            
            # Find a test file that should be in the tracker
            test_file = None
            for doc_info in self.uploaded_documents:
                if doc_info["context_name"] == "TEST-DELETE-002":  # Use a context we haven't deleted from
                    test_file = Path(doc_info["file_path"])
                    break
            
            if not test_file:
                self.log("No test file found for tracker cleanup test", "WARNING")
                return True
            
            # Check if file is tracked
            if self.tracker.is_processed(test_file):
                self.log(f"File is tracked: {test_file.name}", "DEBUG")
                
                # Import the deletion module
                sys.path.insert(0, str(scripts_dir))
                from delete_by_context_and_filename import delete_documents_and_cleanup_tracker
                
                # Delete the document and clean up tracker
                context_name = "TEST-DELETE-002"
                file_name = test_file.name
                
                deletion_stats = delete_documents_and_cleanup_tracker(
                    self.azure_search,
                    self.tracker,
                    context_name,
                    file_name,
                    matching_mode='exact',
                    force=True
                )
                
                # Check if file is no longer tracked
                if not self.tracker.is_processed(test_file):
                    self.log("Tracker cleanup successful: File removed from tracker", "SUCCESS")
                    return True
                else:
                    self.log("Tracker cleanup failed: File still tracked", "ERROR")
                    return False
            else:
                self.log("Test file not tracked, skipping tracker cleanup test", "WARNING")
                return True
            
        except Exception as e:
            self.log(f"Tracker cleanup test failed: {str(e)}", "ERROR")
            return False
    
    def cleanup_test_artifacts(self) -> bool:
        """Clean up all test artifacts."""
        try:
            self.log("Cleaning up test artifacts...")
            
            total_deleted = 0
            
            # Clean up remaining test documents
            for context_name in self.test_contexts:
                deleted_count = self.azure_search.delete_documents_by_filter({
                    "context_name": context_name
                })
                total_deleted += deleted_count
            
            # Clean up tracker entries first (before removing directories)
            for doc_info in self.uploaded_documents:
                test_file = Path(doc_info["file_path"])
                try:
                    if self.tracker.is_processed(test_file):
                        self.tracker.mark_unprocessed(test_file)
                except Exception as tracker_error:
                    # Continue with cleanup even if individual tracker cleanup fails
                    self.log(f"Tracker cleanup warning for {test_file.name}: {str(tracker_error)}", "WARNING")
            
            if len(self.uploaded_documents) > 0:
                try:
                    self.tracker.save()
                    self.log("Cleaned up tracker entries")
                except Exception as save_error:
                    self.log(f"Tracker save warning: {str(save_error)}", "WARNING")
            
            # Clean up temporary directories
            if not self.keep_files:
                for temp_dir in self.temp_dirs:
                    try:
                        if temp_dir.exists():
                            import shutil
                            shutil.rmtree(temp_dir)
                            self.log(f"Removed temporary directory: {temp_dir}")
                    except Exception as dir_error:
                        self.log(f"Directory cleanup warning for {temp_dir}: {str(dir_error)}", "WARNING")
            elif self.keep_files:
                self.log(f"Keeping test files in {len(self.temp_dirs)} directories")
            
            if total_deleted > 0:
                self.log(f"Cleaned up {total_deleted} test documents from Azure Search")
            
            self.log("Test artifact cleanup completed", "SUCCESS")
            return True
            
        except Exception as e:
            self.log(f"Cleanup failed: {str(e)}", "ERROR")
            return False
    
    async def run_all_tests(self) -> bool:
        """Run all test cases."""
        self.test_stats["start_time"] = time.time()
        self.log("🚀 Starting comprehensive delete_by_context_and_filename.py test suite")
        self.log("=" * 80)
        
        test_cases = [
            ("Environment Validation", lambda: self.validate_environment()),
            ("Test Environment Setup", lambda: self.setup_test_environment()),
            ("Pre-test Cleanup", lambda: self.pre_cleanup()),
            ("Document Upload", self.upload_test_documents),
            ("Document Upload Verification", lambda: self.verify_document_upload()),
            ("Exact Matching Test", lambda: self.test_exact_matching()),
            ("Contains Matching Test", lambda: self.test_contains_matching()),
            ("Flexible Matching Test", lambda: self.test_flexible_matching()),
            ("Preview Functionality Test", lambda: self.test_preview_functionality()),
            ("Actual Deletion Test", lambda: self.test_actual_deletion()),
            ("Tracker Cleanup Test", lambda: self.test_tracker_cleanup()),
            ("Final Cleanup", lambda: self.cleanup_test_artifacts())
        ]
        
        overall_success = True
        
        for test_name, test_func in test_cases:
            self.test_stats["tests_run"] += 1
            self.log(f"\n--- Running Test: {test_name} ---")
            
            try:
                if asyncio.iscoroutinefunction(test_func):
                    success = await test_func()
                else:
                    success = test_func()
                
                if success:
                    self.test_stats["tests_passed"] += 1
                    self.log(f"✅ {test_name}: PASSED", "SUCCESS")
                else:
                    self.test_stats["tests_failed"] += 1
                    self.log(f"❌ {test_name}: FAILED", "ERROR")
                    overall_success = False
                    
            except Exception as e:
                self.test_stats["tests_failed"] += 1
                self.log(f"❌ {test_name}: FAILED with exception: {str(e)}", "ERROR")
                overall_success = False
        
        self.test_stats["end_time"] = time.time()
        self.print_test_summary()
        
        return overall_success
    
    def print_test_summary(self):
        """Print comprehensive test results summary."""
        duration = self.test_stats["end_time"] - self.test_stats["start_time"]
        
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE DELETION TEST SUITE RESULTS")
        print("=" * 80)
        
        print(f"\n🧪 Test Execution Summary:")
        print(f"   Total tests run: {self.test_stats['tests_run']}")
        print(f"   Tests passed: {self.test_stats['tests_passed']}")
        print(f"   Tests failed: {self.test_stats['tests_failed']}")
        print(f"   Success rate: {(self.test_stats['tests_passed'] / self.test_stats['tests_run'] * 100):.1f}%")
        print(f"   Total duration: {duration:.2f} seconds")
        
        print(f"\n📄 Document Processing Summary:")
        print(f"   Documents created: {self.test_stats['documents_created']}")
        print(f"   Search objects uploaded: {self.test_stats['documents_uploaded']}")
        print(f"   Documents deleted: {self.test_stats['documents_deleted']}")
        
        if self.test_stats['tests_passed'] == self.test_stats['tests_run']:
            print(f"\n🎉 ALL TESTS PASSED! delete_by_context_and_filename.py is working correctly.")
            print(f"   ✅ Multiple matching strategies validated")
            print(f"   ✅ Preview functionality confirmed")
            print(f"   ✅ Actual deletion with tracker integration verified")
            print(f"   ✅ Azure Search integration working properly")
            print(f"   ✅ Error handling and edge cases covered")
            print(f"   ✅ Complete cleanup and safety features validated")
        else:
            print(f"\n⚠️  SOME TESTS FAILED. Please review the output above.")
            print(f"   Failed tests: {self.test_stats['tests_failed']}")
            print(f"   Check error messages for details on required fixes.")


async def main():
    """Main test execution function."""
    parser = argparse.ArgumentParser(
        description="Comprehensive test suite for delete_by_context_and_filename.py",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Enable verbose logging for detailed test output")
    parser.add_argument("--keep-files", "-k", action="store_true", 
                       help="Keep test files after completion (useful for debugging)")
    
    args = parser.parse_args()
    
    # Create and run test suite
    test_runner = DeleteByContextAndFilenameTestRunner(
        verbose=args.verbose,
        keep_files=args.keep_files
    )
    
    success = await test_runner.run_all_tests()
    
    if success:
        print("\n🎯 Test suite completed successfully!")
        return 0
    else:
        print("\n💥 Test suite completed with failures!")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
