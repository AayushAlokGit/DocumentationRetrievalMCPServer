"""
Test Script for upload_with_custom_metadata - Direct Metadata Upload
===================================================================

Comprehensive test script that validates upload_with_custom_metadata functionality by:
1. Creating a test document with known content
2. Processing it through upload_with_custom_metadata with custom metadata
3. Querying the search index to verify document presence and metadata
4. Cleaning up by deleting the test document and all its chunks

This test ensures that upload_with_custom_metadata correctly:
- Validates metadata schema
- Processes documents with custom metadata
- Uploads to Azure Search with expected fields
- Integrates properly with DocumentProcessingTracker
- Handles chunking and embedding generation

Usage:
    python test_upload_with_custom_metadata_script.py [--keep-test-file] [--verbose]

Author: Personal Documentation Assistant System  
Version: 1.0.0
"""

import os
import sys
import json
import asyncio
import argparse
import tempfile
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
from dotenv import load_dotenv

# Add src directory to path for imports
current_dir = Path(__file__).parent
src_dir = current_dir.parent.parent.parent
sys.path.insert(0, str(src_dir))

# Import project modules
from src.common.vector_search_services.azure_cognitive_search import get_azure_search_service, FilterBuilder
from src.document_upload.document_processing_tracker import DocumentProcessingTracker

# Load environment variables
load_dotenv()


class UploadWithCustomMetadataTestRunner:
    """Comprehensive test runner for upload_with_custom_metadata validation"""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.test_file_path = None
        self.azure_search = None
        self.tracker = None
        self.test_document_ids = []
        self.test_metadata = None
        
    def log(self, message: str, level: str = "INFO"):
        """Enhanced logging with levels"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        if level == "ERROR":
            print(f"[{timestamp}] ❌ {message}")
        elif level == "SUCCESS":
            print(f"[{timestamp}] ✅ {message}")
        elif level == "WARNING":
            print(f"[{timestamp}] ⚠️  {message}")
        else:
            print(f"[{timestamp}] 📝 {message}")
    
    def create_test_document(self) -> Path:
        """Create a comprehensive test document with known content"""
        
        self.log("Creating test document with comprehensive content...")
        
        test_content = """# upload_with_custom_metadata Test Document

## Overview
This is a comprehensive test document created specifically to validate upload_with_custom_metadata functionality.
The document contains multiple sections to test chunking and metadata processing.

## Features Being Tested
- Custom metadata injection
- Document processing pipeline
- Azure Search integration
- Tracker functionality
- Embedding generation

## Test Metadata Fields
This document will be processed with the following custom metadata:
- Title: "upload_with_custom_metadata Test Document"
- Tags: ["testing", "upload-with-custom-metadata", "validation"]
- Category: "test-documents"
- Work Item ID: "TEST-001"

## Content for Chunking
This section contains enough content to potentially create multiple chunks,
allowing us to test how upload_with_custom_metadata handles chunking while maintaining
consistent metadata across all chunks.

### Section 1: Technical Details
upload_with_custom_metadata uses the DirectMetadataProcessingStrategy to inject custom metadata
directly into processed documents, bypassing all auto-generation logic.

### Section 2: Processing Flow
The script processes documents through the following phases:
1. Metadata validation
2. File discovery 
3. Custom processing strategy application
4. Azure Search upload
5. Tracker integration

## Conclusion
This test document should be successfully processed with the custom metadata
provided during the test run, and all chunks should contain the expected
metadata fields in the Azure Search index.
"""
        
        # Create temporary test file (different name every time)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write(test_content)
            self.test_file_path = Path(f.name)
        
        self.log(f"Test document created: {self.test_file_path}")
        return self.test_file_path
    
    def prepare_test_metadata(self) -> Dict[str, Any]:
        """Prepare comprehensive test metadata for upload_with_custom_metadata"""
        
        self.test_metadata = {
            "title": "upload_with_custom_metadata Test Document",
            "tags": ["testing", "upload-with-custom-metadata", "validation", "automated-test"],
            "category": "test-documents",
            "work_item_id": "TEST-001",
            "file_type": "markdown",
            "last_modified": datetime.now().isoformat() + 'Z'
        }
        
        self.log("Test metadata prepared:")
        if self.verbose:
            for key, value in self.test_metadata.items():
                self.log(f"  {key}: {value}")
        
        return self.test_metadata
    
    async def run_upload_with_custom_metadata(self) -> bool:
        """Execute upload_with_custom_metadata with the test document and metadata"""
        
        self.log("Executing upload_with_custom_metadata with test document...")
        
        try:
            # Import upload_with_custom_metadata module
            script_path = Path(__file__).parent.parent / "upload_with_custom_metadata.py"
            
            if not script_path.exists():
                self.log(f"upload_with_custom_metadata not found at expected location: {script_path}", "ERROR")
                return False
            
            # Prepare command arguments
            metadata_json = json.dumps(self.test_metadata)
            
            # Execute upload_with_custom_metadata programmatically by importing its functions
            sys.path.insert(0, str(script_path.parent))
            
            try:
                import src.document_upload.personal_documentation_assistant_scripts.azure_cognitive_search_scripts.upload_with_custom_metadata as script
                
                # Run upload_with_custom_metadata's main processing function
                success = await script.process_and_upload(
                    target_path=self.test_file_path,
                    metadata=self.test_metadata,
                    validate_only=False
                )
                
                if success:
                    self.log("upload_with_custom_metadata execution completed successfully", "SUCCESS")
                    return True
                else:
                    self.log("upload_with_custom_metadata execution failed", "ERROR")
                    return False
                    
            except ImportError as e:
                self.log(f"Failed to import upload_with_custom_metadata: {e}", "ERROR")
                self.log("Running upload_with_custom_metadata via subprocess as fallback...", "WARNING")
                return await self._run_script_subprocess()
                
        except Exception as e:
            self.log(f"Error executing upload_with_custom_metadata: {str(e)}", "ERROR")
            return False
    
    async def _run_script_subprocess(self) -> bool:
        """Fallback: Run upload_with_custom_metadata via subprocess"""
        
        import subprocess
        
        script_path = Path(__file__).parent.parent / "upload_with_custom_metadata.py"
        metadata_json = json.dumps(self.test_metadata)
        
        cmd = [
            sys.executable,
            str(script_path),
            str(self.test_file_path),
            "--metadata", metadata_json
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                self.log("upload_with_custom_metadata subprocess execution successful", "SUCCESS")
                if self.verbose and result.stdout:
                    self.log(f"upload_with_custom_metadata output:\n{result.stdout}")
                return True
            else:
                self.log(f"upload_with_custom_metadata subprocess failed with code {result.returncode}", "ERROR")
                if result.stderr:
                    self.log(f"Error output: {result.stderr}", "ERROR")
                return False
                
        except subprocess.TimeoutExpired:
            self.log("upload_with_custom_metadata execution timed out", "ERROR")
            return False
        except Exception as e:
            self.log(f"Subprocess execution error: {str(e)}", "ERROR")
            return False
    
    def search_for_test_document(self) -> List[Dict[str, Any]]:
        """Search Azure Search index for the test document with retry logic for indexing delays"""
        
        self.log("Searching for test document in Azure Search index...")
        
        # Retry with delays to handle Azure Search indexing latency
        max_retries = 3
        retry_delays = [2, 5, 10]  # seconds
        
        for attempt in range(max_retries):
            try:
                # Search by filterable fields: context_name and category
                filters = {
                    'context_name': self.test_metadata['work_item_id'],  # Should be TEST-001
                    'category': self.test_metadata['category']  # Should be test-documents
                }
                
                results = self.azure_search.search_client.search(
                    search_text="*",
                    filter=FilterBuilder.build_filter(filters),
                    select="*",  # Get all fields
                    top=100
                )
                
                found_docs = list(results)
                self.test_document_ids = [doc['id'] for doc in found_docs]
                
                if found_docs:
                    self.log(f"Found {len(found_docs)} document chunks", "SUCCESS")
                    return found_docs
                else:
                    if attempt < max_retries - 1:
                        delay = retry_delays[attempt]
                        self.log(f"No documents found, retrying in {delay} seconds (attempt {attempt + 1}/{max_retries})...", "WARNING")
                        import time
                        time.sleep(delay)
                    else:
                        self.log("No documents found after all retries", "ERROR")
                
            except Exception as e:
                self.log(f"Error searching for test document (attempt {attempt + 1}): {str(e)}", "ERROR")
                if attempt < max_retries - 1:
                    delay = retry_delays[attempt]
                    self.log(f"Retrying in {delay} seconds...", "WARNING")
                    import time
                    time.sleep(delay)
        
        return []
    
    def verify_document_metadata(self, found_docs: List[Dict[str, Any]]) -> bool:
        """Verify that the document contains expected metadata"""
        
        self.log("Verifying document metadata...")
        
        if not found_docs:
            self.log("No documents found to verify", "ERROR")
            return False
        
        verification_passed = True
        
        for i, doc in enumerate(found_docs, 1):
            self.log(f"Verifying chunk {i}/{len(found_docs)}...")
            
            # Verify core metadata fields
            expected_checks = [
                ('title', self.test_metadata['title']),
                ('category', self.test_metadata['category']),
                ('context_name', self.test_metadata['work_item_id']),  # Should be mapped from work_item_id
                ('file_type', self.test_metadata['file_type'])
            ]
            
            for field, expected_value in expected_checks:
                actual_value = doc.get(field)
                if actual_value != expected_value:
                    self.log(f"  ❌ {field}: expected '{expected_value}', got '{actual_value}'", "ERROR")
                    verification_passed = False
                else:
                    self.log(f"  ✅ {field}: '{actual_value}'", "SUCCESS")
            
            # Verify tags (can be string or list)
            doc_tags = doc.get('tags', '')
            expected_tags = self.test_metadata['tags']
            
            if isinstance(doc_tags, str):
                # Tags stored as comma-separated string
                actual_tag_list = [tag.strip() for tag in doc_tags.split(',') if tag.strip()]
            else:
                # Tags stored as list
                actual_tag_list = doc_tags if isinstance(doc_tags, list) else []
            
            missing_tags = set(expected_tags) - set(actual_tag_list)
            if missing_tags:
                self.log(f"  ❌ tags: missing {missing_tags}, got {actual_tag_list}", "ERROR")
                verification_passed = False
            else:
                self.log(f"  ✅ tags: {actual_tag_list}", "SUCCESS")
            
            # Verify required system fields
            system_fields = ['id', 'content', 'file_path', 'file_name', 'chunk_index']
            for field in system_fields:
                if field not in doc or doc[field] is None:
                    self.log(f"  ❌ {field}: missing or null", "ERROR")
                    verification_passed = False
                else:
                    if self.verbose:
                        value = str(doc[field])[:50] + "..." if len(str(doc[field])) > 50 else str(doc[field])
                        self.log(f"  ✅ {field}: {value}")
            
            # Verify content vector (embedding)
            if 'content_vector' in doc and doc['content_vector']:
                self.log(f"  ✅ content_vector: present ({len(doc['content_vector'])} dimensions)", "SUCCESS")
            else:
                self.log("  ❌ content_vector: missing or empty", "ERROR")
                verification_passed = False
        
        if verification_passed:
            self.log("All metadata verification checks passed!", "SUCCESS")
        else:
            self.log("Metadata verification failed!", "ERROR")
        
        return verification_passed
    
    def _cleanup_existing_test_documents(self):
        """Pre-cleanup any existing test documents with our test context and category"""
        
        try:
            # Search for existing test documents
            filters = {
                'context_name': self.test_metadata['work_item_id'],  # TEST-001
                'category': self.test_metadata['category']  # test-documents
            }
            
            results = self.azure_search.search_client.search(
                search_text="*",
                filter=FilterBuilder.build_filter(filters),
                select="id",  # Only need IDs for deletion
                top=100
            )
            
            existing_docs = list(results)
            if existing_docs:
                self.log(f"Found {len(existing_docs)} existing test documents - cleaning up...")
                
                for doc in existing_docs:
                    try:
                        success = self.azure_search.delete_document(doc['id'])
                        if success:
                            self.log(f"  🧹 Deleted existing test doc: {doc['id']}")
                    except Exception as e:
                        self.log(f"  ⚠️  Warning: Failed to delete {doc['id']}: {str(e)}", "WARNING")
            else:
                self.log("No existing test documents found - clean environment")
                
        except Exception as e:
            self.log(f"Warning: Pre-cleanup failed: {str(e)}", "WARNING")
    
    def cleanup_test_documents(self) -> bool:
        """Delete all test document chunks from Azure Search"""
        
        self.log("Cleaning up test documents from Azure Search...")
        
        if not self.test_document_ids:
            self.log("No test documents to clean up", "WARNING")
            return True
        
        try:
            deleted_count = 0
            failed_count = 0
            
            for doc_id in self.test_document_ids:
                try:
                    success = self.azure_search.delete_document(doc_id)
                    if success:
                        deleted_count += 1
                        self.log(f"  ✅ Deleted document: {doc_id}")
                    else:
                        failed_count += 1
                        self.log(f"  ❌ Failed to delete: {doc_id}", "ERROR")
                except Exception as e:
                    failed_count += 1
                    self.log(f"  ❌ Error deleting {doc_id}: {str(e)}", "ERROR")
            
            # Clean up tracker
            if self.test_file_path and deleted_count > 0:
                try:
                    self.tracker.mark_unprocessed(self.test_file_path)
                    self.tracker.save()
                    self.log("  ✅ Cleaned up document tracker", "SUCCESS")
                except Exception as e:
                    self.log(f"  ⚠️  Warning: Failed to clean tracker: {str(e)}", "WARNING")
            
            self.log(f"Cleanup completed: {deleted_count} deleted, {failed_count} failed", 
                    "SUCCESS" if failed_count == 0 else "WARNING")
            
            return failed_count == 0
            
        except Exception as e:
            self.log(f"Error during cleanup: {str(e)}", "ERROR")
            return False
    
    def cleanup_test_file(self, keep_file: bool = False):
        """Remove the temporary test file"""
        
        if not keep_file and self.test_file_path and self.test_file_path.exists():
            try:
                self.test_file_path.unlink()
                self.log(f"Removed test file: {self.test_file_path}", "SUCCESS")
            except Exception as e:
                self.log(f"Failed to remove test file: {str(e)}", "WARNING")
    
    async def run_complete_test(self, keep_test_file: bool = False) -> bool:
        """Execute the complete test workflow"""
        
        self.log("="*60)
        self.log("STARTING upload_with_custom_metadata COMPREHENSIVE TEST")
        self.log("="*60)
        
        try:
            # Initialize services
            self.log("Initializing Azure services...")
            self.azure_search = get_azure_search_service()
            self.tracker = DocumentProcessingTracker()
            self.log("Services initialized successfully", "SUCCESS")
            
            # Phase 1: Create test document
            test_file = self.create_test_document()
            
            # Phase 2: Prepare metadata
            self.prepare_test_metadata()
            
            # Phase 2.1: Pre-cleanup any existing test documents (for clean test environment)
            self.log("Pre-cleaning any existing test documents...")
            self._cleanup_existing_test_documents()
            
            # Phase 2.5: Ensure test file is not marked as processed (safety check)
            if self.tracker.is_processed(self.test_file_path):
                self.log("Test file already marked as processed - unmarking for clean test", "WARNING")
                self.tracker.mark_unprocessed(self.test_file_path)
                self.tracker.save()
            
            # Phase 3: Execute upload_with_custom_metadata
            script_success = await self.run_upload_with_custom_metadata()
            if not script_success:
                self.log("upload_with_custom_metadata execution failed - stopping test", "ERROR")
                return False
            
            # Phase 4: Search for document
            found_docs = self.search_for_test_document()
            if not found_docs:
                self.log("Test document not found in search index - test failed", "ERROR")
                return False
            
            # Phase 5: Verify metadata
            metadata_valid = self.verify_document_metadata(found_docs)
            if not metadata_valid:
                self.log("Metadata verification failed", "ERROR")
            
            # Phase 6: Cleanup
            cleanup_success = self.cleanup_test_documents()
            
            # Phase 7: Remove test file
            self.cleanup_test_file(keep_test_file)
            
            # Final result
            overall_success = script_success and found_docs and metadata_valid and cleanup_success
            
            self.log("="*60)
            if overall_success:
                self.log("upload_with_custom_metadata TEST COMPLETED SUCCESSFULLY! ✅", "SUCCESS")
            else:
                self.log("upload_with_custom_metadata TEST FAILED ❌", "ERROR")
            self.log("="*60)
            
            return overall_success
            
        except Exception as e:
            self.log(f"Test execution error: {str(e)}", "ERROR")
            return False


async def main():
    """Main test execution function"""
    
    parser = argparse.ArgumentParser(
        description="Comprehensive test script for upload_with_custom_metadata validation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This test script validates upload_with_custom_metadata functionality by:
1. Creating a test document with known content
2. Processing it through upload_with_custom_metadata with custom metadata  
3. Verifying document presence and metadata in Azure Search
4. Cleaning up test documents from the index

Exit codes:
  0 - All tests passed
  1 - Tests failed or errors occurred
        """)
    
    parser.add_argument("--keep-test-file", action="store_true",
                       help="Keep the temporary test file after test completion")
    
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Enable verbose output for detailed test information")
    
    args = parser.parse_args()
    
    # Validate environment
    required_vars = ['AZURE_SEARCH_SERVICE', 'AZURE_SEARCH_KEY', 'AZURE_OPENAI_ENDPOINT', 'AZURE_OPENAI_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\n💡 Please ensure your .env file contains all required variables")
        return 1
    
    # Execute test
    test_runner = UploadWithCustomMetadataTestRunner(verbose=args.verbose)
    
    try:
        success = await test_runner.run_complete_test(keep_test_file=args.keep_test_file)
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Unexpected test error: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
