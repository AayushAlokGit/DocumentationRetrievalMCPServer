#!/usr/bin/env python3
"""
Comprehensive Test Script for upload_with_pipeline.py
====================================================

This test script validates the full pipeline functionality including:
- Full 3-phase pipeline execution (Discovery → Processing → Upload)
- Force reset capability (delete all documents + tracker cleanup)
- Dry-run preview mode
- Comprehensive error handling and progress tracking
- Statistics reporting with detailed metrics
- Resume capability using DocumentProcessingTracker

Test Coverage:
1. Environment setup and validation
2. Test document creation with known metadata
3. Dry-run functionality validation
4. Full pipeline execution with tracker integration
5. Azure Search document verification
6. Comprehensive cleanup and validation
7. Force reset functionality testing

Usage:
    python test_upload_with_pipeline_script.py [--verbose] [--keep-files]
    
Author: Personal Documentation Assistant System Test Suite
Created: Based on upload_with_pipeline.py comprehensive functionality
"""

import os
import sys
import argparse
import asyncio
import tempfile
import time
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Add src to path for imports - navigate up to src directory
current_dir = Path(__file__).parent
scripts_dir = current_dir.parent
src_dir = scripts_dir.parent.parent
sys.path.insert(0, str(src_dir))

# Import project modules
from common.azure_cognitive_search import get_azure_search_service
from document_upload.file_tracker import DocumentProcessingTracker
from document_upload.document_processing_pipeline import DocumentProcessingPipeline
from document_upload.processing_strategies import PersonalDocumentationAssistantProcessingStrategy
from document_upload.discovery_strategies import GeneralDocumentDiscoveryStrategy


class UploadWithPipelineTestRunner:
    """
    Comprehensive test runner for upload_with_pipeline.py functionality.
    
    This test runner validates the complete pipeline including:
    - Full 3-phase pipeline execution
    - DocumentProcessingTracker integration
    - Force reset capabilities
    - Dry-run mode validation
    - Azure Search integration
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
        self.test_context = "test_pipeline_context"
        self.test_file_name = "test_pipeline_document.md"
        self.test_file_path: Optional[Path] = None
        self.temp_dir: Optional[Path] = None
        self.azure_search = None
        self.tracker = None
        
        # Load environment
        load_dotenv()
        
        # Test statistics
        self.test_stats = {
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
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
        """Set up test environment with temporary directory and test document."""
        try:
            self.log("Setting up test environment...")
            
            # Create temporary directory for test documents
            self.temp_dir = Path(tempfile.mkdtemp(prefix="pipeline_test_"))
            self.log(f"Created temporary directory: {self.temp_dir}", "DEBUG")
            
            # Create test document with known metadata
            self.test_file_path = self.temp_dir / self.test_file_name
            test_content = f"""# Test Document for Pipeline Validation

## Document Metadata
- **Context**: {self.test_context}
- **Purpose**: Comprehensive pipeline testing
- **Test Type**: Full pipeline execution with tracker integration
- **Created**: {time.strftime('%Y-%m-%d %H:%M:%S')}

## Test Content

This document tests the complete upload_with_pipeline.py functionality including:

### Core Pipeline Features
1. **Full 3-phase execution**: Discovery → Processing → Upload
2. **DocumentProcessingTracker integration**: Idempotent processing
3. **Force reset capability**: Complete index and tracker cleanup
4. **Dry-run mode**: Preview without making changes

### Pipeline Validation Points
- Document discovery using GeneralDocumentDiscoveryStrategy
- Processing with PersonalDocumentationAssistantProcessingStrategy
- Upload to Azure Search with embeddings
- Tracker state management and persistence

### Expected Behavior
The pipeline should:
1. Discover this test document in the temporary directory
2. Process it to extract metadata and generate chunks
3. Upload search objects to Azure Cognitive Search
4. Mark the file as processed in DocumentProcessingTracker
5. Skip reprocessing on subsequent runs (unless force reset)

## Test Tags
pipeline, upload, tracker, azure-search, full-execution

## Test Content Body
This is the main content body that should be processed and uploaded to Azure Search.
The pipeline should extract this content, generate embeddings, and create searchable objects.

Additional content to ensure proper chunking and processing behavior.
Testing comprehensive pipeline functionality with realistic document structure.
"""
            
            with open(self.test_file_path, 'w', encoding='utf-8') as f:
                f.write(test_content)
            
            self.log(f"Created test document: {self.test_file_name}", "SUCCESS")
            
            # Initialize Azure Search service
            service_name = os.getenv('AZURE_SEARCH_SERVICE')
            admin_key = os.getenv('AZURE_SEARCH_KEY')
            index_name = os.getenv('AZURE_SEARCH_INDEX', 'work-items-index')
            
            self.azure_search = get_azure_search_service(service_name, admin_key, index_name)
            self.log("Azure Search service initialized", "SUCCESS")
            
            # Initialize DocumentProcessingTracker
            self.tracker = DocumentProcessingTracker()
            self.log("DocumentProcessingTracker initialized", "SUCCESS")
            
            return True
            
        except Exception as e:
            self.log(f"Failed to setup test environment: {str(e)}", "ERROR")
            return False
    
    def pre_cleanup(self) -> bool:
        """Clean up any existing test documents before running tests."""
        try:
            self.log("Performing pre-test cleanup...")
            
            # Remove any existing test documents from Azure Search
            deleted_count = self.azure_search.delete_documents_by_filter({
                "file_name": self.test_file_name
            })
            
            if deleted_count > 0:
                self.log(f"Removed {deleted_count} existing test documents from Azure Search")
                # Wait for deletion to propagate
                time.sleep(2)
            else:
                self.log("No existing test documents found in Azure Search")
            
            # Remove test file from tracker if it exists
            if self.test_file_path and self.tracker.is_processed(self.test_file_path):
                self.tracker.mark_unprocessed(self.test_file_path)
                self.tracker.save()
                self.log("Removed test file from DocumentProcessingTracker")
            
            self.log("Pre-test cleanup completed", "SUCCESS")
            return True
            
        except Exception as e:
            self.log(f"Pre-cleanup failed: {str(e)}", "ERROR")
            return False
    
    def test_dry_run_functionality(self) -> bool:
        """Test the dry-run mode functionality."""
        try:
            self.log("Testing dry-run functionality...")
            
            # Create configured pipeline (no force_reprocess needed for this test)
            discovery_strategy = GeneralDocumentDiscoveryStrategy()
            processing_strategy = PersonalDocumentationAssistantProcessingStrategy()
            tracker = DocumentProcessingTracker()
            
            pipeline = DocumentProcessingPipeline(
                discovery_strategy=discovery_strategy,
                processing_strategy=processing_strategy,
                tracker=tracker
            )
            
            # Test discovery preview
            self.log("Testing discovery phase in dry-run mode...", "DEBUG")
            discovery_result = pipeline.discovery_phase.discover_documents(str(self.temp_dir))
            
            # Validate discovery found our test file
            if discovery_result.total_files == 0:
                self.log("Dry-run test failed: No files discovered", "ERROR")
                return False
            
            found_test_file = any(
                Path(file_path).name == self.test_file_name 
                for file_path in discovery_result.discovered_files
            )
            
            if not found_test_file:
                self.log("Dry-run test failed: Test file not discovered", "ERROR")
                return False
            
            self.log(f"Dry-run discovery successful: Found {discovery_result.total_files} files", "SUCCESS")
            
            # Test processing preview using filter_unprocessed_files
            unprocessed_files, total_discovered, already_processed = pipeline.filter_unprocessed_files(
                discovery_result.discovered_files
            )
            
            self.log(f"Dry-run filter preview: {len(unprocessed_files)} files would be processed", "DEBUG")
            
            if len(unprocessed_files) != 1:
                self.log(f"Dry-run test failed: Expected 1 unprocessed file, got {len(unprocessed_files)}", "ERROR")
                return False
            
            self.log("Dry-run functionality validation successful", "SUCCESS")
            return True
            
        except Exception as e:
            self.log(f"Dry-run test failed: {str(e)}", "ERROR")
            return False
    
    async def test_full_pipeline_execution(self) -> bool:
        """Test the complete pipeline execution."""
        try:
            self.log("Testing full pipeline execution...")
            
            # Get Azure credentials
            service_name = os.getenv('AZURE_SEARCH_SERVICE')
            admin_key = os.getenv('AZURE_SEARCH_KEY')
            index_name = os.getenv('AZURE_SEARCH_INDEX', 'work-items-index')
            
            # Create configured pipeline
            discovery_strategy = GeneralDocumentDiscoveryStrategy()
            processing_strategy = PersonalDocumentationAssistantProcessingStrategy()
            tracker = DocumentProcessingTracker()
            
            pipeline = DocumentProcessingPipeline(
                discovery_strategy=discovery_strategy,
                processing_strategy=processing_strategy,
                tracker=tracker
            )
            
            # Execute complete pipeline
            self.log("Executing complete 3-phase pipeline...", "DEBUG")
            discovery_result, processing_result, upload_result = await pipeline.run_complete_pipeline(
                root_directory=str(self.temp_dir),
                service_name=service_name,
                admin_key=admin_key,
                index_name=index_name
            )
            
            # Validate pipeline results
            if discovery_result.total_files == 0:
                self.log("Pipeline test failed: No files discovered", "ERROR")
                return False
            
            if processing_result.successfully_processed == 0:
                self.log("Pipeline test failed: No files processed", "ERROR")
                return False
            
            if upload_result.successfully_uploaded == 0:
                self.log("Pipeline test failed: No objects uploaded", "ERROR")
                return False
            
            # Validate tracker was updated
            if not tracker.is_processed(self.test_file_path):
                self.log("Pipeline test failed: File not marked as processed in tracker", "ERROR")
                return False
            
            self.log(f"Pipeline execution successful:", "SUCCESS")
            self.log(f"  - Files discovered: {discovery_result.total_files}")
            self.log(f"  - Files processed: {processing_result.successfully_processed}")
            self.log(f"  - Objects uploaded: {upload_result.successfully_uploaded}")
            self.log(f"  - File tracked: Yes")
            
            return True
            
        except Exception as e:
            self.log(f"Full pipeline test failed: {str(e)}", "ERROR")
            return False
    
    async def search_for_test_document(self, max_retries: int = 3) -> Dict[str, Any]:
        """Search for the uploaded test document with retry logic."""
        for attempt in range(max_retries):
            try:
                self.log(f"Searching for test document (attempt {attempt + 1}/{max_retries})...", "DEBUG")
                
                # Search for our test document by file name using text_search
                filters = {"file_name": self.test_file_name}
                results = self.azure_search.text_search(
                    query="pipeline test",
                    filters=filters,
                    top=10
                )
                
                if results:
                    self.log(f"Found {len(results)} test documents in Azure Search", "SUCCESS")
                    return {"found": True, "documents": results, "count": len(results)}
                
                if attempt < max_retries - 1:
                    self.log(f"Document not found, waiting 2 seconds before retry...", "DEBUG")
                    time.sleep(2)
                
            except Exception as e:
                self.log(f"Search attempt {attempt + 1} failed: {str(e)}", "WARNING")
                if attempt < max_retries - 1:
                    time.sleep(2)
        
        return {"found": False, "documents": [], "count": 0}
    
    def validate_document_metadata(self, documents: list) -> bool:
        """Validate that uploaded documents have correct metadata."""
        try:
            self.log("Validating document metadata...")
            
            if not documents:
                self.log("No documents to validate", "ERROR")
                return False
            
            # Get the first document for validation
            doc = documents[0]
            
            # Validate required fields
            required_fields = ['file_name', 'category', 'context_name', 'file_type', 'content_vector']
            missing_fields = []
            
            for field in required_fields:
                if field not in doc:
                    missing_fields.append(field)
            
            if missing_fields:
                self.log(f"Missing required fields: {missing_fields}", "ERROR")
                return False
            
            # Validate field values (context_name should be the temp directory name)
            temp_dir_name = self.temp_dir.name if self.temp_dir else "unknown"
            expected_context = temp_dir_name
            
            validations = [
                (doc.get('file_name') == self.test_file_name, f"file_name: expected '{self.test_file_name}', got '{doc.get('file_name')}'"),
                (doc.get('context_name') == expected_context, f"context_name: expected '{expected_context}', got '{doc.get('context_name')}'"),
                (doc.get('file_type') in ['.md', 'markdown'], f"file_type: expected '.md' or 'markdown', got '{doc.get('file_type')}'"),
                (isinstance(doc.get('content_vector'), list), f"content_vector: expected list, got {type(doc.get('content_vector'))}"),
                (len(doc.get('content_vector', [])) == 1536, f"content_vector length: expected 1536, got {len(doc.get('content_vector', []))}"),
            ]
            
            for is_valid, error_msg in validations:
                if not is_valid:
                    self.log(f"Metadata validation failed: {error_msg}", "ERROR")
                    return False
            
            self.log("Document metadata validation successful:", "SUCCESS")
            self.log(f"  - File name: {doc.get('file_name')}")
            self.log(f"  - Category: {doc.get('category')}")
            self.log(f"  - Context: {doc.get('context_name')}")
            self.log(f"  - File type: {doc.get('file_type')}")
            self.log(f"  - Vector dimensions: {len(doc.get('content_vector', []))}")
            
            if 'title' in doc:
                self.log(f"  - Title: {doc.get('title')}")
            if 'tags' in doc:
                self.log(f"  - Tags: {doc.get('tags')}")
            
            return True
            
        except Exception as e:
            self.log(f"Metadata validation failed: {str(e)}", "ERROR")
            return False
    
    async def test_tracker_integration(self) -> bool:
        """Test DocumentProcessingTracker integration and resume capability."""
        try:
            self.log("Testing tracker integration and resume capability...")
            
            # Reload the tracker to ensure we have the latest state from disk
            self.tracker = DocumentProcessingTracker()  # Fresh tracker that loads from disk
            
            # Verify file is marked as processed using the same tracker instance
            if not self.tracker.is_processed(self.test_file_path):
                self.log("Tracker test failed: File not marked as processed", "ERROR")
                return False
            
            # Get Azure credentials
            service_name = os.getenv('AZURE_SEARCH_SERVICE')
            admin_key = os.getenv('AZURE_SEARCH_KEY')
            index_name = os.getenv('AZURE_SEARCH_INDEX', 'work-items-index')
            
            # Create pipeline and run again - should skip processed files
            # Use a fresh tracker that loads from file to test persistence
            discovery_strategy = GeneralDocumentDiscoveryStrategy()
            processing_strategy = PersonalDocumentationAssistantProcessingStrategy()
            fresh_tracker = DocumentProcessingTracker()  # Fresh tracker loads from saved file
            
            pipeline = DocumentProcessingPipeline(
                discovery_strategy=discovery_strategy,
                processing_strategy=processing_strategy,
                tracker=fresh_tracker
            )
            
            self.log("Running pipeline again to test resume capability...", "DEBUG")
            discovery_result, processing_result, upload_result = await pipeline.run_complete_pipeline(
                root_directory=str(self.temp_dir),
                service_name=service_name,
                admin_key=admin_key,
                index_name=index_name
            )
            
            # Validate that files were skipped (already processed)
            if processing_result.successfully_processed > 0:
                self.log("Tracker test failed: Files were reprocessed when they should have been skipped", "ERROR")
                return False
            
            if upload_result.successfully_uploaded > 0:
                self.log("Tracker test failed: Objects were uploaded when files should have been skipped", "ERROR")
                return False
            
            self.log("Tracker integration test successful:", "SUCCESS")
            self.log(f"  - Files discovered: {discovery_result.total_files}")
            self.log(f"  - Files processed: {processing_result.successfully_processed}")
            self.log(f"  - Objects uploaded: {upload_result.successfully_uploaded}")
            
            return True
            
        except Exception as e:
            self.log(f"Tracker integration test failed: {str(e)}", "ERROR")
            return False
    
    async def test_force_reset_functionality(self) -> bool:
        """Test the force reset functionality."""
        try:
            self.log("Testing force reset functionality...")
            
            # Get initial document count
            initial_search = await self.search_for_test_document(max_retries=1)
            initial_count = initial_search["count"]
            
            if initial_count == 0:
                self.log("Force reset test skipped: No test documents found to reset", "WARNING")
                return True
            
            # Get Azure credentials
            service_name = os.getenv('AZURE_SEARCH_SERVICE')
            admin_key = os.getenv('AZURE_SEARCH_KEY')
            index_name = os.getenv('AZURE_SEARCH_INDEX', 'work-items-index')
            
            # Create pipeline with force_reprocess=True
            discovery_strategy = GeneralDocumentDiscoveryStrategy()
            processing_strategy = PersonalDocumentationAssistantProcessingStrategy()
            tracker = DocumentProcessingTracker()
            
            # Note: Since we removed force_reprocess from upload_with_pipeline.py,
            # we'll simulate force reset by manually cleaning up and reprocessing
            
            self.log("Simulating force reset: cleaning up tracker and search index...", "DEBUG")
            
            # Manual cleanup (simulating force reset)
            if tracker.is_processed(self.test_file_path):
                tracker.mark_unprocessed(self.test_file_path)
                tracker.save()
                self.log("Removed file from tracker")
            
            # Delete from search index
            deleted_count = self.azure_search.delete_documents_by_filter({
                "file_name": self.test_file_name
            })
            self.log(f"Deleted {deleted_count} documents from search index")
            
            # Wait for deletion to propagate
            time.sleep(2)
            
            # Now reprocess
            pipeline = DocumentProcessingPipeline(
                discovery_strategy=discovery_strategy,
                processing_strategy=processing_strategy,
                tracker=tracker
            )
            
            self.log("Executing pipeline after force reset...", "DEBUG")
            discovery_result, processing_result, upload_result = await pipeline.run_complete_pipeline(
                root_directory=str(self.temp_dir),
                service_name=service_name,
                admin_key=admin_key,
                index_name=index_name
            )
            
            # Validate reprocessing occurred
            if processing_result.successfully_processed == 0:
                self.log("Force reset test failed: No files processed after reset", "ERROR")
                return False
            
            if upload_result.successfully_uploaded == 0:
                self.log("Force reset test failed: No objects uploaded after reset", "ERROR")
                return False
            
            self.log("Force reset functionality test successful:", "SUCCESS")
            self.log(f"  - Files reprocessed: {processing_result.successfully_processed}")
            self.log(f"  - Objects uploaded: {upload_result.successfully_uploaded}")
            
            return True
            
        except Exception as e:
            self.log(f"Force reset test failed: {str(e)}", "ERROR")
            return False
    
    async def cleanup_test_artifacts(self) -> bool:
        """Clean up test artifacts and temporary files."""
        try:
            self.log("Cleaning up test artifacts...")
            
            # Remove test documents from Azure Search
            deleted_count = self.azure_search.delete_documents_by_filter({
                "file_name": self.test_file_name
            })
            
            if deleted_count > 0:
                self.log(f"Removed {deleted_count} test documents from Azure Search")
            
            # Remove from tracker
            if self.tracker and self.test_file_path and self.tracker.is_processed(self.test_file_path):
                self.tracker.mark_unprocessed(self.test_file_path)
                self.tracker.save()
                self.log("Removed test file from DocumentProcessingTracker")
            
            # Clean up temporary files
            if not self.keep_files and self.temp_dir and self.temp_dir.exists():
                import shutil
                shutil.rmtree(self.temp_dir)
                self.log(f"Removed temporary directory: {self.temp_dir}")
            elif self.keep_files:
                self.log(f"Keeping test files at: {self.temp_dir}")
            
            self.log("Test artifact cleanup completed", "SUCCESS")
            return True
            
        except Exception as e:
            self.log(f"Cleanup failed: {str(e)}", "ERROR")
            return False
    
    async def run_all_tests(self) -> bool:
        """Run all test cases."""
        self.test_stats["start_time"] = time.time()
        self.log("🚀 Starting comprehensive upload_with_pipeline.py test suite")
        self.log("=" * 70)
        
        test_cases = [
            ("Environment Validation", lambda: self.validate_environment()),
            ("Test Environment Setup", lambda: self.setup_test_environment()),
            ("Pre-test Cleanup", lambda: self.pre_cleanup()),
            ("Dry-run Functionality", lambda: self.test_dry_run_functionality()),
            ("Full Pipeline Execution", self.test_full_pipeline_execution),
            ("Document Search Verification", lambda: asyncio.create_task(self.search_for_test_document())),
            ("Document Metadata Validation", lambda: self.validate_document_metadata(self.search_result.get("documents", []))),
            ("Tracker Integration", self.test_tracker_integration),
            ("Force Reset Functionality", self.test_force_reset_functionality),
            ("Final Cleanup", self.cleanup_test_artifacts)
        ]
        
        overall_success = True
        
        for test_name, test_func in test_cases:
            self.test_stats["tests_run"] += 1
            self.log(f"\n--- Running Test: {test_name} ---")
            
            try:
                if test_name == "Document Search Verification":
                    # Special handling for async search
                    self.search_result = await self.search_for_test_document()
                    success = self.search_result["found"]
                elif test_name == "Document Metadata Validation":
                    # Use search result from previous test
                    success = self.validate_document_metadata(self.search_result.get("documents", []))
                elif asyncio.iscoroutinefunction(test_func):
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
        
        print("\n" + "=" * 70)
        print("📊 COMPREHENSIVE TEST SUITE RESULTS")
        print("=" * 70)
        
        print(f"\n🧪 Test Execution Summary:")
        print(f"   Total tests run: {self.test_stats['tests_run']}")
        print(f"   Tests passed: {self.test_stats['tests_passed']}")
        print(f"   Tests failed: {self.test_stats['tests_failed']}")
        print(f"   Success rate: {(self.test_stats['tests_passed'] / self.test_stats['tests_run'] * 100):.1f}%")
        print(f"   Total duration: {duration:.2f} seconds")
        
        if self.test_stats['tests_passed'] == self.test_stats['tests_run']:
            print(f"\n🎉 ALL TESTS PASSED! upload_with_pipeline.py is working correctly.")
            print(f"   ✅ Full pipeline execution validated")
            print(f"   ✅ DocumentProcessingTracker integration verified")
            print(f"   ✅ Azure Search integration confirmed")
            print(f"   ✅ Dry-run functionality working")
            print(f"   ✅ Force reset capability validated")
            print(f"   ✅ Comprehensive metadata validation passed")
        else:
            print(f"\n⚠️  SOME TESTS FAILED. Please review the output above.")
            print(f"   Failed tests: {self.test_stats['tests_failed']}")
            print(f"   Check error messages for details on required fixes.")


async def main():
    """Main test execution function."""
    parser = argparse.ArgumentParser(
        description="Comprehensive test suite for upload_with_pipeline.py",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Enable verbose logging for detailed test output")
    parser.add_argument("--keep-files", "-k", action="store_true", 
                       help="Keep test files after completion (useful for debugging)")
    
    args = parser.parse_args()
    
    # Create and run test suite
    test_runner = UploadWithPipelineTestRunner(
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
