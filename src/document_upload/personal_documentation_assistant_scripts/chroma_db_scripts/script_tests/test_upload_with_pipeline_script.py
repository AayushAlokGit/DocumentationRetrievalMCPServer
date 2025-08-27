#!/usr/bin/env python3
"""
Comprehensive Test Script for ChromaDB upload_with_pipeline.py
=============================================================

This test script validates the full ChromaDB pipeline functionality including:
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
5. ChromaDB document verification
6. Comprehensive cleanup and validation
7. Force reset functionality testing

Usage:
    python test_upload_with_pipeline_script.py
    
Author: Personal Documentation Assistant System Test Suite - ChromaDB
Created: ChromaDB migration of Azure pipeline test script
"""

import os
import sys
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
from src.common.vector_search_services.chromadb_service import get_chromadb_service
from src.document_upload.upload_strategies import ChromaDBDocumentUploadStrategy
from src.document_upload.document_processing_tracker import DocumentProcessingTracker
from document_upload.document_processing_pipeline import DocumentProcessingPipeline
from document_upload.processing_strategies import PersonalDocumentationAssistantChromaDBProcessingStrategy
from document_upload.discovery_strategies import GeneralDocumentDiscoveryStrategy


class ChromaDBPipelineTestRunner:
    """
    Comprehensive test runner for ChromaDB upload_with_pipeline.py functionality.
    
    This test runner validates the complete ChromaDB pipeline including:
    - Full 3-phase pipeline execution
    - DocumentProcessingTracker integration
    - Force reset capabilities
    - Dry-run mode validation
    - ChromaDB integration
    """
    
    def __init__(self):
        """
        Initialize the test runner.
        """
        self.test_context = "test_chromadb_pipeline_context"
        self.test_file_name = "test_chromadb_pipeline_document.md"
        self.test_file_path: Optional[Path] = None
        self.temp_dir: Optional[Path] = None
        self.chromadb_service = None
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
        """Log a message."""
        prefix = {
            "INFO": "ℹ️ ",
            "SUCCESS": "✅ ",
            "WARNING": "⚠️ ",
            "ERROR": "❌ ",
            "DEBUG": "🔍 "
        }.get(level, "  ")
        
        print(f"{prefix}{message}")
    
    def validate_environment(self) -> bool:
        """Validate ChromaDB environment requirements."""
        self.log("Validating ChromaDB environment configuration...")
        
        # ChromaDB doesn't require as many environment variables as Azure
        # But we still need the personal documentation directory
        if os.getenv('PERSONAL_DOCUMENTATION_ROOT_DIRECTORY'):
            docs_dir = Path(os.getenv('PERSONAL_DOCUMENTATION_ROOT_DIRECTORY'))
            if not docs_dir.exists():
                self.log(f"PERSONAL_DOCUMENTATION_ROOT_DIRECTORY does not exist: {docs_dir}", "ERROR")
                return False
        else:
            self.log("PERSONAL_DOCUMENTATION_ROOT_DIRECTORY not set (using temp directory for test)", "WARNING")
        
        self.log("ChromaDB environment validation successful", "SUCCESS")
        return True
    
    async def setup_test_environment(self) -> bool:
        """Set up test environment with temporary directory and test document."""
        try:
            self.log("Setting up ChromaDB test environment...")
            
            # Create temporary directory for test documents
            self.temp_dir = Path(tempfile.mkdtemp(prefix="chromadb_pipeline_test_"))
            # Create context subdirectory to mimic work item structure
            context_dir = self.temp_dir / self.test_context
            context_dir.mkdir()
            self.log(f"Created temporary directory: {self.temp_dir}", "DEBUG")
            
            # Create test document with known metadata
            self.test_file_path = context_dir / self.test_file_name
            test_content = f"""# Test Document for ChromaDB Pipeline Validation

## Document Metadata
- **Context**: {self.test_context}
- **Purpose**: Comprehensive ChromaDB pipeline testing
- **Test Type**: Full pipeline execution with tracker integration
- **Created**: {time.strftime('%Y-%m-%d %H:%M:%S')}

## Test Content

This document tests the complete ChromaDB upload_with_pipeline.py functionality including:

### Core Pipeline Features
1. **Full 3-phase execution**: Discovery → Processing → Upload
2. **DocumentProcessingTracker integration**: Idempotent processing
3. **Force reset capability**: Complete ChromaDB and tracker cleanup
4. **Dry-run mode**: Preview without making changes

### Pipeline Validation Points
- Document discovery using GeneralDocumentDiscoveryStrategy
- Processing with PersonalDocumentationAssistantChromaDBProcessingStrategy
- Upload to ChromaDB with local embeddings
- Tracker state management and persistence

### Expected Behavior
The ChromaDB pipeline should:
1. Discover this test document in the temporary directory
2. Process it to extract metadata and generate chunks
3. Upload search objects to ChromaDB with local embeddings
4. Mark the file as processed in DocumentProcessingTracker
5. Skip reprocessing on subsequent runs (unless force reset)

## Test Tags
chromadb, pipeline, upload, tracker, local-embeddings, full-execution

## Test Content Body
This is the main content body that should be processed and uploaded to ChromaDB.
The pipeline should extract this content, generate local embeddings, and create searchable objects.

Additional content to ensure proper chunking and processing behavior.
Testing comprehensive ChromaDB pipeline functionality with realistic document structure.

The ChromaDB integration should handle metadata flattening and local embedding generation
seamlessly while maintaining compatibility with the existing pipeline structure.
"""
            
            with open(self.test_file_path, 'w', encoding='utf-8') as f:
                f.write(test_content)
            
            self.log(f"Created test document: {self.test_file_name}", "SUCCESS")
            
            # Initialize ChromaDB service
            self.chromadb_service = await get_chromadb_service()
            if not self.chromadb_service:
                self.log("Failed to initialize ChromaDB service", "ERROR")
                return False
                
            # Test ChromaDB connection
            self.chromadb_service.test_connection()
            self.log("ChromaDB service initialized and tested", "SUCCESS")
            
            # Initialize DocumentProcessingTracker
            self.tracker = DocumentProcessingTracker()
            self.log("DocumentProcessingTracker initialized", "SUCCESS")
            
            return True
            
        except Exception as e:
            self.log(f"Failed to setup test environment: {str(e)}", "ERROR")
            return False
    
    async def pre_cleanup(self) -> bool:
        """Clean up any existing test documents before running tests."""
        try:
            self.log("Performing pre-test cleanup...")
            
            # Remove any existing test documents from ChromaDB
            # Note: For cleanup, we don't need processing strategy
            upload_strategy = ChromaDBDocumentUploadStrategy()
            
            # Search for existing test documents
            try:
                results = await self.chromadb_service.vector_search(
                    query=f"file_name:{self.test_file_name}",
                    top=100
                )
                
                if results and len(results) > 0:
                    # Delete found test documents
                    delete_ids = [doc.get('id') for doc in results if doc.get('id')]
                    if delete_ids:
                        await self.chromadb_service.delete_documents(delete_ids)
                        self.log(f"Removed {len(delete_ids)} existing test documents from ChromaDB")
                    # Wait for deletion to propagate
                    await asyncio.sleep(1)
                else:
                    self.log("No existing test documents found in ChromaDB")
            except Exception as e:
                self.log(f"ChromaDB cleanup warning: {e}", "WARNING")
            
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
            self.test_stats["tests_run"] += 1
            
            # Create configured pipeline
            discovery_strategy = GeneralDocumentDiscoveryStrategy()
            processing_strategy = PersonalDocumentationAssistantChromaDBProcessingStrategy()
            upload_strategy = ChromaDBDocumentUploadStrategy(processing_strategy=processing_strategy)
            
            pipeline = DocumentProcessingPipeline(
                discovery_strategy=discovery_strategy,
                processing_strategy=processing_strategy,
                upload_strategy=upload_strategy,
                tracker=self.tracker
            )
            
            # Test discovery phase in dry-run mode
            discovery_result = pipeline.discovery_phase.discover_documents(str(self.temp_dir))
            
            # Validate discovery results
            if not discovery_result.discovered_files:
                self.log("Dry-run test failed: No files discovered", "ERROR")
                self.test_stats["tests_failed"] += 1
                return False
            
            # Check if our test file was discovered
            test_file_found = any(
                file_path.name == self.test_file_name 
                for file_path in discovery_result.discovered_files
            )
            
            if not test_file_found:
                self.log(f"Dry-run test failed: Test file {self.test_file_name} not discovered", "ERROR")
                self.test_stats["tests_failed"] += 1
                return False
            
            self.log("Dry-run functionality test passed", "SUCCESS")
            self.test_stats["tests_passed"] += 1
            return True
            
        except Exception as e:
            self.log(f"Dry-run test failed: {str(e)}", "ERROR")
            self.test_stats["tests_failed"] += 1
            return False
    
    async def test_full_pipeline_execution(self) -> bool:
        """Test complete pipeline execution with ChromaDB upload."""
        try:
            self.log("Testing full ChromaDB pipeline execution...")
            self.test_stats["tests_run"] += 1
            
            # Create configured pipeline
            discovery_strategy = GeneralDocumentDiscoveryStrategy()
            processing_strategy = PersonalDocumentationAssistantChromaDBProcessingStrategy()
            upload_strategy = ChromaDBDocumentUploadStrategy(processing_strategy=processing_strategy)
            
            pipeline = DocumentProcessingPipeline(
                discovery_strategy=discovery_strategy,
                processing_strategy=processing_strategy,
                upload_strategy=upload_strategy,
                tracker=self.tracker
            )
            
            # Execute complete pipeline
            discovery_result, processing_result, upload_result = await pipeline.run_complete_pipeline(
                root_directory=str(self.temp_dir)
            )
            
            # Validate pipeline results
            if not discovery_result.discovered_files:
                self.log("Pipeline test failed: No files discovered", "ERROR")
                self.test_stats["tests_failed"] += 1
                return False
            
            if processing_result.successfully_processed == 0:
                self.log("Pipeline test failed: No documents processed successfully", "ERROR")
                self.test_stats["tests_failed"] += 1
                return False
            
            if upload_result.successfully_uploaded == 0:
                self.log("Pipeline test failed: No documents uploaded successfully", "ERROR")
                self.test_stats["tests_failed"] += 1
                return False
            
            # Verify document was tracked
            if not self.tracker.is_processed(self.test_file_path):
                self.log("Pipeline test failed: Document not marked as processed in tracker", "ERROR")
                self.test_stats["tests_failed"] += 1
                return False
            
            self.log(f"Pipeline execution successful:", "SUCCESS")
            self.log(f"  - Discovered: {discovery_result.total_files} files")
            self.log(f"  - Processed: {processing_result.successfully_processed} documents")
            self.log(f"  - Uploaded: {upload_result.successfully_uploaded} objects")
            
            self.test_stats["tests_passed"] += 1
            return True
            
        except Exception as e:
            self.log(f"Pipeline execution test failed: {str(e)}", "ERROR")
            self.test_stats["tests_failed"] += 1
            return False
    
    async def test_chromadb_document_verification(self) -> bool:
        """Verify that documents were actually stored in ChromaDB."""
        try:
            self.log("Verifying documents in ChromaDB...")
            self.test_stats["tests_run"] += 1
            
            # Query ChromaDB for our test document
            results = await self.chromadb_service.vector_search(
                query="ChromaDB pipeline testing",
                top=10
            )
            
            if not results:
                self.log("ChromaDB verification failed: No documents found", "ERROR")
                self.test_stats["tests_failed"] += 1
                return False
            
            # Check if we can find our test document in the results
            found_test_doc = False
            for doc in results:
                if doc.get('file_name') == self.test_file_name:
                    found_test_doc = True
                    break
            
            if not found_test_doc:
                self.log("ChromaDB verification failed: Test document not found in search results", "ERROR")
                self.test_stats["tests_failed"] += 1
                return False
            
            self.log(f"ChromaDB verification successful: Found {len(results)} documents", "SUCCESS")
            self.test_stats["tests_passed"] += 1
            return True
            
        except Exception as e:
            self.log(f"ChromaDB verification failed: {str(e)}", "ERROR")
            self.test_stats["tests_failed"] += 1
            return False
    
    async def test_force_reset_functionality(self) -> bool:
        """Test the force reset capability."""
        try:
            self.log("Testing force reset functionality...")
            self.test_stats["tests_run"] += 1
            
            # Perform force reset
            upload_strategy = ChromaDBDocumentUploadStrategy()
            
            # Delete all documents from ChromaDB
            delete_count = await upload_strategy.delete_all_documents_from_service()
            
            if delete_count < 0:
                self.log("Force reset test failed: ChromaDB deletion failed", "ERROR")
                self.test_stats["tests_failed"] += 1
                return False
            
            self.log(f"Deleted {delete_count} documents from ChromaDB")
            
            # Clear tracker
            cleared_files = self.tracker.clear()
            self.log(f"Cleared {cleared_files} files from tracker")
            
            # Verify documents are gone from ChromaDB
            results = await self.chromadb_service.vector_search(
                query="test",
                top=100
            )
            
            # It's OK if there are some documents, but our test document should be gone
            if results:
                found_test_doc = False
                for doc in results:
                    if doc.get('file_name') == self.test_file_name:
                        found_test_doc = True
                        break
                
                if found_test_doc:
                    self.log("Force reset test failed: Test document still found after reset", "ERROR")
                    self.test_stats["tests_failed"] += 1
                    return False
            
            # Verify tracker is clear for our test file
            if self.tracker.is_processed(self.test_file_path):
                self.log("Force reset test failed: Test file still tracked after reset", "ERROR")
                self.test_stats["tests_failed"] += 1
                return False
            
            self.log("Force reset functionality test passed", "SUCCESS")
            self.test_stats["tests_passed"] += 1
            return True
            
        except Exception as e:
            self.log(f"Force reset test failed: {str(e)}", "ERROR")
            self.test_stats["tests_failed"] += 1
            return False
    
    async def cleanup_test_environment(self):
        """Clean up test environment and temporary files."""
        try:
            self.log("Cleaning up test environment...")
            
            # Remove temporary directory and files
            if self.temp_dir and self.temp_dir.exists():
                import shutil
                shutil.rmtree(self.temp_dir)
                self.log(f"Removed temporary directory: {self.temp_dir}")
            
            # Final cleanup of any test documents from ChromaDB
            if self.chromadb_service:
                try:
                    results = await self.chromadb_service.vector_search(
                        query=f"file_name:{self.test_file_name}",
                        top=100
                    )
                    if results:
                        delete_ids = [doc.get('id') for doc in results if doc.get('id')]
                        if delete_ids:
                            await self.chromadb_service.delete_documents(delete_ids)
                            self.log(f"Final cleanup: removed {len(delete_ids)} test documents")
                except Exception as e:
                    self.log(f"Final cleanup warning: {e}", "WARNING")
            
            self.log("Test environment cleanup completed", "SUCCESS")
            
        except Exception as e:
            self.log(f"Cleanup failed: {str(e)}", "WARNING")
    
    def print_test_results(self):
        """Print comprehensive test results."""
        self.test_stats["end_time"] = time.time()
        duration = self.test_stats["end_time"] - self.test_stats["start_time"]
        
        print("\n" + "="*60)
        print("🧪 CHROMADB PIPELINE TEST RESULTS")
        print("="*60)
        
        print(f"\n📊 Test Statistics:")
        print(f"   Tests run: {self.test_stats['tests_run']}")
        print(f"   Tests passed: {self.test_stats['tests_passed']}")
        print(f"   Tests failed: {self.test_stats['tests_failed']}")
        print(f"   Success rate: {(self.test_stats['tests_passed']/max(1,self.test_stats['tests_run']))*100:.1f}%")
        print(f"   Duration: {duration:.2f} seconds")
        
        if self.test_stats["tests_failed"] == 0:
            print(f"\n✅ ALL TESTS PASSED - ChromaDB pipeline is working correctly!")
        else:
            print(f"\n❌ {self.test_stats['tests_failed']} TESTS FAILED - Please check the logs above")
        
        print("="*60)
    
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
            
            # Pre-cleanup
            if not await self.pre_cleanup():
                return False
            
            # Run tests in sequence
            tests = [
                ("Dry-run functionality", self.test_dry_run_functionality),
                ("Full pipeline execution", self.test_full_pipeline_execution),
                ("ChromaDB document verification", self.test_chromadb_document_verification),
                ("Force reset functionality", self.test_force_reset_functionality)
            ]
            
            for test_name, test_func in tests:
                self.log(f"\n--- Running: {test_name} ---")
                if asyncio.iscoroutinefunction(test_func):
                    success = await test_func()
                else:
                    success = test_func()
                
                if not success:
                    self.log(f"Test failed: {test_name}", "ERROR")
            
            return True
            
        except Exception as e:
            self.log(f"Test execution failed: {str(e)}", "ERROR")
            return False
        
        finally:
            # Always cleanup
            await self.cleanup_test_environment()
            self.print_test_results()


async def main():
    """Main test execution function."""
    # Create and run test suite
    test_runner = ChromaDBPipelineTestRunner()
    
    success = await test_runner.run_all_tests()
    
    if success:
        print("\n🎯 ChromaDB test suite completed successfully!")
        return 0
    else:
        print("\n💥 ChromaDB test suite completed with failures!")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
