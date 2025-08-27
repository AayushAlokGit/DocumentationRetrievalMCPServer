#!/usr/bin/env python3
"""
Comprehensive Test Script for ChromaDB upload_with_custom_metadata.py
====================================================================

This test script validates the ChromaDB custom metadata upload functionality including:
- Metadata schema validation
- Single file upload with custom metadata
- Directory batch upload with shared metadata
- Error handling and edge cases
- Document Processing Tracker integration
- ChromaDB storage verification

Test Coverage:
1. Environment setup and validation
2. Test document creation with known content
3. Metadata schema validation (valid and invalid cases)
4. Single file custom metadata upload
5. Directory batch upload with shared metadata
6. ChromaDB document verification
7. Error handling and edge cases
8. Comprehensive cleanup and validation

Usage:
    python test_upload_with_custom_metadata_script.py
    
Author: Personal Documentation Assistant System Test Suite - ChromaDB Custom Metadata
Created: Test suite for ChromaDB custom metadata upload functionality
"""

import os
import sys
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
from src.document_upload.document_processing_tracker import DocumentProcessingTracker, load_processed_files
from src.document_upload.personal_documentation_assistant_scripts.chroma_db_scripts.upload_with_custom_metadata import (
    validate_metadata_schema,
    DirectMetadataProcessingStrategy,
    process_and_upload
)


class ChromaDBCustomMetadataTestRunner:
    """
    Comprehensive test runner for ChromaDB upload_with_custom_metadata.py functionality.
    
    This test runner validates the complete custom metadata upload including:
    - Schema validation
    - Single file and directory processing
    - Error handling
    - ChromaDB integration
    - Document Processing Tracker integration
    """
    
    def __init__(self):
        """Initialize the test runner."""
        self.test_context = "test_custom_metadata_context"
        self.temp_dir: Optional[Path] = None
        self.chromadb_service = None
        self.tracker = None
        
        # Test files created during setup
        self.test_files = []
        
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
        """Set up test environment with temporary directory and test documents."""
        try:
            self.log("Setting up ChromaDB custom metadata test environment...")
            
            # Create temporary directory for test documents
            self.temp_dir = Path(tempfile.mkdtemp(prefix="chromadb_custom_metadata_test_"))
            # Create context subdirectory to mimic work item structure
            context_dir = self.temp_dir / self.test_context
            context_dir.mkdir()
            
            # Create multiple test documents with different content types
            test_docs = [
                {
                    "filename": "api_reference.md",
                    "content": """# API Reference Guide

## Authentication
Use Bearer tokens for API authentication.

### Headers
- `Authorization: Bearer <token>`
- `Content-Type: application/json`

## Endpoints

### GET /api/docs
Retrieve API documentation.

### POST /api/upload
Upload documents with metadata.

#### Request Body
```json
{
  "title": "Document Title",
  "content": "Document content here"
}
```

## Response Codes
- 200: Success
- 401: Unauthorized
- 500: Server Error

## Tags
api, reference, documentation, authentication
"""
                },
                {
                    "filename": "user_guide.md",
                    "content": """# User Guide

Welcome to the ChromaDB Custom Metadata Upload system.

## Overview
This system allows you to upload documents with custom metadata directly to ChromaDB.

## Features
- Direct metadata injection
- Schema validation
- Batch processing
- Error handling

## Getting Started

### Step 1: Prepare Your Metadata
Create a JSON object with required fields:
- title
- tags  
- category
- work_item_id

### Step 2: Run the Upload Script
```bash
python upload_with_custom_metadata.py /path/to/file --metadata '{"title": "My Doc", ...}'
```

### Step 3: Verify Upload
Check ChromaDB for your uploaded documents.

## Tags
user-guide, tutorial, getting-started, chromadb
"""
                },
                {
                    "filename": "troubleshooting.md",
                    "content": """# Troubleshooting Guide

## Common Issues

### Metadata Validation Errors
- Ensure all required fields are present
- Check field types match expected format
- Verify JSON syntax is correct

### Upload Failures
- Check ChromaDB connection
- Verify file permissions
- Review error logs

### Performance Issues
- Consider batch size for large uploads
- Monitor embedding generation time
- Check system resources

## Error Codes
- E001: Missing required metadata fields
- E002: Invalid JSON format
- E003: ChromaDB connection failed
- E004: File not found

## Support
Contact support team for additional help.

## Tags
troubleshooting, errors, support, help
"""
                }
            ]
            
            # Create test files
            for doc in test_docs:
                file_path = context_dir / doc["filename"]
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(doc["content"])
                self.test_files.append(file_path)
                self.log(f"Created test document: {doc['filename']}")
            
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
            try:
                for test_file in self.test_files:
                    results = await self.chromadb_service.vector_search(
                        query=f"file_name:{test_file.name}",
                        top=100
                    )
                    
                    if results and len(results) > 0:
                        # Delete found test documents
                        delete_ids = [doc.get('id') for doc in results if doc.get('id')]
                        if delete_ids:
                            await self.chromadb_service.delete_documents(delete_ids)
                            self.log(f"Removed {len(delete_ids)} existing test documents for {test_file.name}")
                        # Wait for deletion to propagate
                        await asyncio.sleep(0.5)
            except Exception as e:
                self.log(f"ChromaDB cleanup warning: {e}", "WARNING")
            
            # Remove test files from tracker if they exist
            for test_file in self.test_files:
                if self.tracker.is_processed(test_file):
                    self.tracker.mark_unprocessed(test_file)
            self.tracker.save()
            
            self.log("Pre-test cleanup completed", "SUCCESS")
            return True
            
        except Exception as e:
            self.log(f"Pre-cleanup failed: {str(e)}", "ERROR")
            return False
    
    def test_metadata_schema_validation(self) -> bool:
        """Test metadata schema validation with various cases."""
        try:
            self.log("Testing metadata schema validation...")
            self.test_stats["tests_run"] += 1
            
            # Test valid metadata
            valid_metadata = {
                "title": "Test Document",
                "tags": "test,validation",
                "category": "testing",
                "work_item_id": "TEST-001"
            }
            is_valid, errors = validate_metadata_schema(valid_metadata)
            if not is_valid:
                self.log(f"Valid metadata rejected: {errors}", "ERROR")
                self.test_stats["tests_failed"] += 1
                return False
            
            # Test metadata with optional fields
            valid_with_optional = {
                "title": "Test Document",
                "tags": ["test", "validation", "optional"],
                "category": "testing", 
                "work_item_id": "TEST-001",
                "file_type": "md",
                "metadata_json": '{"custom": "field"}'
            }
            is_valid, errors = validate_metadata_schema(valid_with_optional)
            if not is_valid:
                self.log(f"Valid metadata with optional fields rejected: {errors}", "ERROR")
                self.test_stats["tests_failed"] += 1
                return False
            
            # Test missing required fields
            missing_required = {
                "title": "Test Document",
                "tags": "test"
                # Missing category and work_item_id
            }
            is_valid, errors = validate_metadata_schema(missing_required)
            if is_valid:
                self.log("Invalid metadata (missing required) was accepted", "ERROR")
                self.test_stats["tests_failed"] += 1
                return False
            
            # Test system-generated fields provided by user
            with_system_fields = {
                "title": "Test Document",
                "tags": "test",
                "category": "testing",
                "work_item_id": "TEST-001",
                "id": "should_not_be_provided",  # System-generated
                "content_vector": [0.1, 0.2, 0.3]  # System-generated
            }
            is_valid, errors = validate_metadata_schema(with_system_fields)
            if is_valid:
                self.log("Invalid metadata (with system fields) was accepted", "ERROR")
                self.test_stats["tests_failed"] += 1
                return False
            
            # Test unknown fields
            with_unknown_fields = {
                "title": "Test Document",
                "tags": "test",
                "category": "testing",
                "work_item_id": "TEST-001",
                "unknown_field": "value"
            }
            is_valid, errors = validate_metadata_schema(with_unknown_fields)
            if is_valid:
                self.log("Invalid metadata (with unknown fields) was accepted", "ERROR")
                self.test_stats["tests_failed"] += 1
                return False
            
            self.log("Metadata schema validation test passed", "SUCCESS")
            self.test_stats["tests_passed"] += 1
            return True
            
        except Exception as e:
            self.log(f"Metadata validation test failed: {str(e)}", "ERROR")
            self.test_stats["tests_failed"] += 1
            return False
    
    async def test_single_file_upload(self) -> bool:
        """Test single file upload with custom metadata."""
        try:
            self.log("Testing single file upload with custom metadata...")
            self.test_stats["tests_run"] += 1
            
            # Use the first test file
            test_file = self.test_files[0]  # api_reference.md
            
            # Custom metadata for single file
            metadata = {
                "title": "API Reference Guide - Custom",
                "tags": ["api", "reference", "custom-upload"],
                "category": "documentation",
                "work_item_id": "CUSTOM-001",
                "metadata_json": json.dumps({"test_type": "single_file", "upload_method": "custom_metadata"})
            }
            
            # Process and upload the single file
            success = await process_and_upload(test_file, metadata, validate_only=False)
            
            if not success:
                self.log("Single file upload failed", "ERROR")
                self.test_stats["tests_failed"] += 1
                return False
            
            # Verify document was uploaded to ChromaDB
            await asyncio.sleep(1)  # Wait for indexing
            results = await self.chromadb_service.vector_search(
                query="API Reference custom upload",
                top=5
            )
            
            if not results:
                self.log("Single file not found in ChromaDB after upload", "ERROR")
                self.test_stats["tests_failed"] += 1
                return False
            
            # Verify custom metadata is present
            found_doc = None
            for doc in results:
                if doc.get('file_name') == test_file.name:
                    found_doc = doc
                    break
            
            if not found_doc:
                self.log("Uploaded file not found in search results", "ERROR")
                self.test_stats["tests_failed"] += 1
                return False
            
            # Check custom metadata
            if found_doc.get('title') != metadata['title']:
                self.log(f"Custom title not preserved: expected '{metadata['title']}', got '{found_doc.get('title')}'", "ERROR")
                self.test_stats["tests_failed"] += 1
                return False
            
            if found_doc.get('work_item_id') != metadata['work_item_id']:
                self.log(f"Custom work_item_id not preserved: expected '{metadata['work_item_id']}', got '{found_doc.get('work_item_id')}'", "ERROR")
                self.test_stats["tests_failed"] += 1
                return False
            
            self.log("Single file upload test passed", "SUCCESS")
            self.test_stats["tests_passed"] += 1
            return True
            
        except Exception as e:
            self.log(f"Single file upload test failed: {str(e)}", "ERROR")
            self.test_stats["tests_failed"] += 1
            return False
    
    async def test_directory_batch_upload(self) -> bool:
        """Test directory batch upload with shared metadata."""
        try:
            self.log("Testing directory batch upload with shared metadata...")
            self.test_stats["tests_run"] += 1
            
            # Shared metadata for all files in directory
            metadata = {
                "title": "Documentation Suite - Batch Upload",
                "tags": "documentation,batch,suite,shared-metadata",
                "category": "reference",
                "work_item_id": "BATCH-001"
            }
            
            # Process and upload the entire directory
            success = await process_and_upload(self.temp_dir, metadata, validate_only=False)
            
            if not success:
                self.log("Directory batch upload failed", "ERROR")
                self.test_stats["tests_failed"] += 1
                return False
            
            # Verify all documents were uploaded to ChromaDB
            await asyncio.sleep(2)  # Wait for indexing
            
            uploaded_files = 0
            for test_file in self.test_files:
                results = await self.chromadb_service.vector_search(
                    query=f"file_name:{test_file.name}",
                    top=5
                )
                
                if results:
                    # Find our document in results
                    found = any(doc.get('file_name') == test_file.name for doc in results)
                    if found:
                        uploaded_files += 1
                        self.log(f"Verified {test_file.name} in ChromaDB")
                    else:
                        self.log(f"File {test_file.name} not found in ChromaDB", "WARNING")
                else:
                    self.log(f"No results found for {test_file.name}", "WARNING")
            
            if uploaded_files == 0:
                self.log("No files found in ChromaDB after batch upload", "ERROR")
                self.test_stats["tests_failed"] += 1
                return False
            
            # Check shared metadata consistency
            results = await self.chromadb_service.vector_search(
                query="documentation suite batch",
                top=10
            )
            
            shared_work_item_count = 0
            for doc in results:
                if doc.get('work_item_id') == metadata['work_item_id']:
                    shared_work_item_count += 1
            
            if shared_work_item_count == 0:
                self.log("Shared metadata not found in uploaded documents", "ERROR")
                self.test_stats["tests_failed"] += 1
                return False
            
            self.log(f"Directory batch upload test passed: {uploaded_files} files uploaded", "SUCCESS")
            self.test_stats["tests_passed"] += 1
            return True
            
        except Exception as e:
            self.log(f"Directory batch upload test failed: {str(e)}", "ERROR")
            self.test_stats["tests_failed"] += 1
            return False
    
    async def test_error_handling(self) -> bool:
        """Test error handling for various failure scenarios."""
        try:
            self.log("Testing error handling scenarios...")
            self.test_stats["tests_run"] += 1
            
            # Test 1: Non-existent file
            non_existent_file = self.temp_dir / "does_not_exist.md"
            metadata = {
                "title": "Test",
                "tags": "test",
                "category": "testing",
                "work_item_id": "ERROR-001"
            }
            
            try:
                success = await process_and_upload(non_existent_file, metadata, validate_only=False)
                # Should handle gracefully and return False
                if success:
                    self.log("Non-existent file upload should have failed", "ERROR")
                    self.test_stats["tests_failed"] += 1
                    return False
            except Exception:
                # Expected to fail, this is OK
                pass
            
            # Test 2: Invalid metadata (should be caught by validation)
            invalid_metadata = {
                "title": "Test"
                # Missing required fields
            }
            
            try:
                success = await process_and_upload(self.test_files[0], invalid_metadata, validate_only=True)
                # Should fail validation
                if success:
                    self.log("Invalid metadata should have failed validation", "ERROR")
                    self.test_stats["tests_failed"] += 1
                    return False
            except Exception:
                # Expected to fail, this is OK
                pass
            
            self.log("Error handling test passed", "SUCCESS")
            self.test_stats["tests_passed"] += 1
            return True
            
        except Exception as e:
            self.log(f"Error handling test failed: {str(e)}", "ERROR")
            self.test_stats["tests_failed"] += 1
            return False
    
    async def test_tracker_integration(self) -> bool:
        """Test Document Processing Tracker integration."""
        try:
            self.log("Testing Document Processing Tracker integration...")
            self.test_stats["tests_run"] += 1
            
            # Use a file that hasn't been processed yet
            test_file = self.test_files[-1]  # troubleshooting.md
            
            # Verify not already processed
            if self.tracker.is_processed(test_file):
                self.tracker.mark_unprocessed(test_file)
                self.tracker.save()
            
            # Process the file
            metadata = {
                "title": "Troubleshooting Guide - Tracker Test",
                "tags": "troubleshooting,tracker,integration",
                "category": "support",
                "work_item_id": "TRACKER-001"
            }
            
            success = await process_and_upload(test_file, metadata, validate_only=False)
            
            if not success:
                self.log("Tracker integration test upload failed", "ERROR")
                self.test_stats["tests_failed"] += 1
                return False
            
            # Verify file is now tracked
            self.log(f"Checking if {test_file} is processed in tracker...")
            self.log(f"File path type: {type(test_file)}")
            self.log(f"File exists: {test_file.exists()}")
            
            # Force reload tracker state
            self.tracker.processed_files = load_processed_files(self.tracker.tracking_file)
            
            if not self.tracker.is_processed(test_file):
                self.log("File not marked as processed in tracker", "ERROR")
                self.log(f"Processed files count: {len(self.tracker.processed_files)}")
                self.log(f"Tracked files: {list(self.tracker.processed_files.keys())}")
                self.test_stats["tests_failed"] += 1
                return False
            
            # Get file metadata from tracker
            stored_metadata = self.tracker.get_file_metadata(test_file)
            if not stored_metadata:
                self.log("No metadata found in tracker", "ERROR")
                self.test_stats["tests_failed"] += 1
                return False
            
            # Verify metadata is stored correctly
            if stored_metadata.get('work_item_id') != metadata['work_item_id']:
                self.log("Tracker metadata doesn't match uploaded metadata", "ERROR")
                self.test_stats["tests_failed"] += 1
                return False
            
            self.log("Tracker integration test passed", "SUCCESS")
            self.test_stats["tests_passed"] += 1
            return True
            
        except Exception as e:
            self.log(f"Tracker integration test failed: {str(e)}", "ERROR")
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
            if self.chromadb_service and self.test_files:
                try:
                    for test_file in self.test_files:
                        results = await self.chromadb_service.vector_search(
                            query=f"file_name:{test_file.name}",
                            top=100
                        )
                        if results:
                            delete_ids = [doc.get('id') for doc in results if doc.get('id')]
                            if delete_ids:
                                await self.chromadb_service.delete_documents(delete_ids)
                                self.log(f"Final cleanup: removed {len(delete_ids)} test documents for {test_file.name}")
                except Exception as e:
                    self.log(f"Final cleanup warning: {e}", "WARNING")
            
            self.log("Test environment cleanup completed", "SUCCESS")
            
        except Exception as e:
            self.log(f"Cleanup failed: {str(e)}", "WARNING")
    
    def print_test_results(self):
        """Print comprehensive test results."""
        self.test_stats["end_time"] = time.time()
        duration = self.test_stats["end_time"] - self.test_stats["start_time"]
        
        print("\n" + "="*70)
        print("🧪 CHROMADB CUSTOM METADATA UPLOAD TEST RESULTS")
        print("="*70)
        
        print(f"\n📊 Test Statistics:")
        print(f"   Tests run: {self.test_stats['tests_run']}")
        print(f"   Tests passed: {self.test_stats['tests_passed']}")
        print(f"   Tests failed: {self.test_stats['tests_failed']}")
        print(f"   Success rate: {(self.test_stats['tests_passed']/max(1,self.test_stats['tests_run']))*100:.1f}%")
        print(f"   Duration: {duration:.2f} seconds")
        
        if self.test_stats["tests_failed"] == 0:
            print(f"\n✅ ALL TESTS PASSED - ChromaDB custom metadata upload is working correctly!")
        else:
            print(f"\n❌ {self.test_stats['tests_failed']} TESTS FAILED - Please check the logs above")
        
        print("="*70)
    
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
                ("Metadata schema validation", self.test_metadata_schema_validation),
                ("Single file upload", self.test_single_file_upload),
                ("Directory batch upload", self.test_directory_batch_upload),
                ("Error handling", self.test_error_handling),
                ("Tracker integration", self.test_tracker_integration)
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
    test_runner = ChromaDBCustomMetadataTestRunner()
    
    success = await test_runner.run_all_tests()
    
    if success:
        print("\n🎯 ChromaDB custom metadata upload test suite completed successfully!")
        return 0
    else:
        print("\n💥 ChromaDB custom metadata upload test suite completed with failures!")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
