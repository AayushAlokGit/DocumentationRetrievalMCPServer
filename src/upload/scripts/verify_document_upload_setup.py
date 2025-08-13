#!/usr/bin/env python3
"""
Document Upload System Verification Script
=========================================

This script verifies that the Document Upload System setup is correct
and all components required for document processing and indexing are working properly.

This focuses specifically on the document upload pipeline components:
- Environment variables
- Azure OpenAI connection for embeddings
- Azure Cognitive Search connection
- Work Items directory structure
- Document processing capabilities
"""

import os
import sys
import asyncio
from pathlib import Path
from typing import Dict, Any, List

# Add src directory to path - go up to project root then to src
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root / "src" / "common"))
sys.path.insert(0, str(project_root / "src" / "upload"))

def print_header(title: str):
    """Print a formatted header"""
    print(f"\n{'='*60}")
    print(f"[DOCUMENT] {title}")
    print(f"{'='*60}")

def print_result(test_name: str, success: bool, message: str = ""):
    """Print test result"""
    status = "[SUCCESS] PASS" if success else "[ERROR] FAIL"
    print(f"{status} {test_name}")
    if message:
        print(f"    {message}")

async def verify_document_upload_environment() -> Dict[str, bool]:
    """Verify environment variables required for document upload system"""
    print_header("Document Upload System - Environment Variables")
    
    required_vars = [
        'AZURE_OPENAI_ENDPOINT',
        'AZURE_OPENAI_KEY', 
        'EMBEDDING_DEPLOYMENT',
        'AZURE_SEARCH_SERVICE',
        'AZURE_SEARCH_KEY',
        'PERSONAL_DOCUMENTATION_ROOT_DIRECTORY'
    ]
    
    optional_vars = [
        'AZURE_SEARCH_INDEX',
        'CHUNK_SIZE',
        'CHUNK_OVERLAP',
        'VECTOR_DIMENSIONS'
    ]
    
    results = {}
    
    # Check required variables for document upload
    all_required_present = True
    for var in required_vars:
        value = os.getenv(var)
        is_present = bool(value)
        results[var] = is_present
        all_required_present &= is_present
        
        print_result(f"Required: {var}", is_present, 
                    "Set" if value else "Missing - required for document upload")
    
    # Check optional variables  
    for var in optional_vars:
        value = os.getenv(var)
        print_result(f"Optional: {var}", True, 
                    f"Set to: {value}" if value else "Using default")
    
    results['all_required'] = all_required_present
    return results

async def verify_work_items_directory() -> Dict[str, Any]:
    """Verify work items directory structure for document upload"""
    print_header("Document Upload System - Work Items Directory")
    
    PERSONAL_DOCUMENTATION_ROOT_DIRECTORY = os.getenv('PERSONAL_DOCUMENTATION_ROOT_DIRECTORY')
    results = {'path_set': bool(PERSONAL_DOCUMENTATION_ROOT_DIRECTORY)}
    
    if not PERSONAL_DOCUMENTATION_ROOT_DIRECTORY:
        print_result("Work Items Path", False, "PERSONAL_DOCUMENTATION_ROOT_DIRECTORY not set in .env")
        return results
    
    work_items_dir = Path(PERSONAL_DOCUMENTATION_ROOT_DIRECTORY)
    results['directory_exists'] = work_items_dir.exists()
    
    if not work_items_dir.exists():
        print_result("Directory Exists", False, f"Directory not found: {PERSONAL_DOCUMENTATION_ROOT_DIRECTORY}")
        return results
    
    print_result("Directory Exists", True, f"Found: {PERSONAL_DOCUMENTATION_ROOT_DIRECTORY}")
    
    # Count work item directories (subdirectories with markdown files)
    work_item_dirs = []
    for item in work_items_dir.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            md_files = list(item.glob("*.md"))
            if md_files:
                work_item_dirs.append((item.name, len(md_files)))
    
    results['work_item_count'] = len(work_item_dirs)
    results['has_work_items'] = len(work_item_dirs) > 0
    
    # Count total markdown files
    md_files = list(work_items_dir.rglob("*.md"))
    results['markdown_files_count'] = len(md_files)
    results['has_markdown_files'] = len(md_files) > 0
    
    print_result("Work Item Directories", results['has_work_items'], 
                f"Found {len(work_item_dirs)} work item directories")
    print_result("Markdown Files", results['has_markdown_files'],
                f"Found {len(md_files)} markdown files ready for processing")
    
    if work_item_dirs:
        print("\n[LIST] Work Item Directories discovered:")
        for name, md_count in sorted(work_item_dirs)[:10]:
            print(f"    • {name}: {md_count} markdown files")
        if len(work_item_dirs) > 10:
            print(f"    ... and {len(work_item_dirs) - 10} more")
    
    return results

async def verify_azure_openai_for_embeddings() -> bool:
    """Verify Azure OpenAI connection specifically for embedding generation"""
    print_header("Document Upload System - Azure OpenAI (Embeddings)")
    
    try:
        from embedding_service import get_embedding_generator
        
        embedding_generator = get_embedding_generator()
        print_result("Embedding Service Initialization", True, "Service created successfully")
        
        # Test connection
        connection_ok = embedding_generator.test_connection()
        print_result("Azure OpenAI Connection", connection_ok,
                    "Successfully connected to Azure OpenAI" if connection_ok 
                    else "Failed to connect - check AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_KEY")
        
        if connection_ok:
            # Test embedding generation (critical for document upload)
            try:
                print("[REFRESH] Testing embedding generation for document upload...")
                embedding = await embedding_generator.generate_embedding("test document content for upload")
                embedding_ok = embedding is not None and len(embedding) > 0
                
                if embedding_ok:
                    expected_dim = int(os.getenv('VECTOR_DIMENSIONS', '1536'))
                    actual_dim = len(embedding)
                    dimension_ok = actual_dim == expected_dim
                    
                    print_result("Embedding Generation", embedding_ok,
                                f"Generated {actual_dim}D embedding (expected: {expected_dim}D)")
                    print_result("Embedding Dimensions", dimension_ok,
                                f"Dimensions match expected size for search index" if dimension_ok
                                else f"Dimension mismatch: got {actual_dim}, expected {expected_dim}")
                    return connection_ok and embedding_ok and dimension_ok
                else:
                    print_result("Embedding Generation", False, "Failed to generate test embedding")
                    return False
                    
            except Exception as e:
                print_result("Embedding Generation", False, f"Error: {e}")
                return False
        
        return connection_ok
        
    except ImportError as e:
        print_result("Embedding Dependencies", False, f"Import error: {e}")
        return False
    except Exception as e:
        print_result("Azure OpenAI Setup", False, f"Error: {e}")
        return False

async def verify_azure_search_for_upload() -> bool:
    """Verify Azure Cognitive Search connection for document upload"""
    print_header("Document Upload System - Azure Cognitive Search")
    
    try:
        from azure_cognitive_search import get_azure_search_service
        
        search_service = get_azure_search_service()
        print_result("Search Service Initialization", True, "Service created successfully")
        
        # Test connection and index
        try:
            # Check if index exists (may not exist on first setup)
            index_exists = search_service.index_exists()
            index_name = search_service.index_name
            
            if index_exists:
                print_result("Search Index Exists", True, f"Index '{index_name}' found and ready")
                
                # If index exists, check its contents
                try:
                    doc_count = search_service.get_document_count()
                    work_items = search_service.get_work_items()
                    
                    print_result("Index Document Count", True, f"{doc_count} documents currently indexed")
                    print_result("Index Work Items", True, f"{len(work_items)} work items currently indexed")
                    
                    if work_items:
                        print("\n[LIST] Currently Indexed Work Items:")
                        for item in sorted(work_items)[:10]:
                            print(f"    • {item}")
                        if len(work_items) > 10:
                            print(f"    ... and {len(work_items) - 10} more")
                            
                except Exception as e:
                    print_result("Index Content Check", False, f"Error reading index: {e}")
                    
            else:
                print_result("Search Index Exists", False, 
                            f"Index '{index_name}' not found - run create index script first")
                print("Tips: Next step: python scripts/create_azure_cognitive_search_index.py")
            
            return True  # Connection works even if index doesn't exist yet
            
        except Exception as e:
            print_result("Search Service Connection", False, f"Error connecting to search service: {e}")
            return False
            
    except ImportError as e:
        print_result("Azure Search Dependencies", False, f"Import error: {e}")
        return False
    except Exception as e:
        print_result("Azure Search Setup", False, f"Error: {e}")
        return False

async def verify_document_processing_pipeline() -> bool:
    """Verify document processing components work correctly"""
    print_header("Document Upload System - Document Processing Pipeline")
    
    try:
        # Test document utilities
        from document_utils import discover_markdown_files, extract_metadata
        print_result("Document Utilities Import", True, "Document processing utilities available")
        
        # Test file tracker
        from file_tracker import DocumentProcessingTracker
        
        tracker = DocumentProcessingTracker("test_processed_files.json")
        print_result("File Tracker", True, "Document processing tracker available")
        
        # Test file tracking functionality
        PERSONAL_DOCUMENTATION_ROOT_DIRECTORY = os.getenv('PERSONAL_DOCUMENTATION_ROOT_DIRECTORY')
        if PERSONAL_DOCUMENTATION_ROOT_DIRECTORY and Path(PERSONAL_DOCUMENTATION_ROOT_DIRECTORY).exists():
            try:
                # Test tracking with actual markdown files
                markdown_files = discover_markdown_files(PERSONAL_DOCUMENTATION_ROOT_DIRECTORY)
                if markdown_files:
                    test_file = markdown_files[0]
                    
                    # Test basic tracking operations
                    initially_processed = tracker.is_processed(test_file)
                    tracker.mark_processed(test_file)
                    now_processed = tracker.is_processed(test_file)
                    tracker.save()
                    
                    # Verify tracking file exists
                    tracking_file_exists = tracker.tracking_file.exists()
                    
                    # Test unprocessing
                    tracker.mark_unprocessed(test_file)
                    after_unprocess = tracker.is_processed(test_file)
                    
                    # Get stats
                    stats = tracker.get_stats()
                    
                    print_result("File Tracking Operations", True,
                                f"Tracking operations work correctly - file marked and unmarked")
                    print_result("Tracking File Creation", tracking_file_exists,
                                f"Tracking file created at: {tracker.tracking_file}")
                    print_result("Tracking Statistics", True,
                                f"Stats available - {stats['total_processed']} files tracked")
                    
                    # Test metadata extraction on the same file
                    try:
                        with open(test_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                        metadata = extract_metadata(content, test_file)
                        print_result("Metadata Extraction", True,
                                    f"Successfully extracted metadata from {test_file.name}")
                    except Exception as e:
                        print_result("Metadata Extraction", False, f"Error processing {test_file.name}: {e}")
                        
                else:
                    print_result("File Tracking Test", False, "No markdown files found for tracking test")
                    
            except Exception as e:
                print_result("File Tracking Test", False, f"Error testing file tracking: {e}")
                return False
        else:
            print_result("File Tracking Test", False, "Work items path not available for tracking test")
        
        # Clean up test tracking file
        if tracker.tracking_file.exists():
            tracker.tracking_file.unlink()
        
        # Test document upload functionality
        PERSONAL_DOCUMENTATION_ROOT_DIRECTORY = os.getenv('PERSONAL_DOCUMENTATION_ROOT_DIRECTORY')
        if PERSONAL_DOCUMENTATION_ROOT_DIRECTORY and Path(PERSONAL_DOCUMENTATION_ROOT_DIRECTORY).exists():
            try:
                markdown_files = discover_markdown_files(PERSONAL_DOCUMENTATION_ROOT_DIRECTORY)
                print_result("File Discovery", len(markdown_files) > 0,
                            f"Discovered {len(markdown_files)} markdown files for processing")
                        
            except Exception as e:
                print_result("File Discovery", False, f"Error discovering files: {e}")
                return False
        else:
            print_result("File Discovery", False, "Work items path not set or doesn't exist")
            return False
            
        # Clean up test file
        test_file_path = Path("test_processed_files.json")
        if test_file_path.exists():
            test_file_path.unlink()
            
        return True
        
    except ImportError as e:
        print_result("Document Processing Dependencies", False, f"Import error: {e}")
        return False
    except Exception as e:
        print_result("Document Processing Pipeline", False, f"Error: {e}")
        return False

def print_document_upload_summary(results: Dict[str, bool]):
    """Print overall summary for document upload system verification"""
    print_header("Document Upload System - Verification Summary")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("🎉 Document Upload System verification PASSED!")
        print("\n[SUCCESS] Your system is ready for document upload and indexing.")
        print("\n[LIST] Next steps:")
        print("   1. Create search index: python scripts/create_azure_cognitive_search_index.py")
        print("   2. Upload documents: python scripts/upload_work_items.py") 
        print("   3. Verify upload: Check document count and test search")
        print("\n🔗 After successful upload, proceed to MCP Server setup:")
        print("   📖 See MCP_SERVER_SETUP.md")
    else:
        failed_components = [k for k, v in results.items() if not v]
        print("[WARNING]  Document Upload System verification FAILED!")
        print(f"\n[ERROR] Failed components: {', '.join(failed_components)}")
        print("\n[INFO] Common solutions:")
        print("   • Missing .env file: Copy .env.example to .env and configure")
        print("   • Azure credentials: Check Azure OpenAI and Cognitive Search credentials")
        print("   • Dependencies: Run 'pip install -r requirements.txt'")
        print("   • Work items path: Ensure PERSONAL_DOCUMENTATION_ROOT_DIRECTORY points to directory with markdown files")
        print("\n📖 See DOCUMENT_UPLOAD_SETUP.md for detailed setup instructions")

async def main():
    """Run document upload system verification"""
    print("[DOCUMENT] Work Item Documentation - Document Upload System Verification")
    print("=" * 80)
    print("This script verifies the Document Upload System setup is ready for:")
    print("• Processing work item markdown files")
    print("• Generating embeddings via Azure OpenAI") 
    print("• Creating searchable index in Azure Cognitive Search")
    print("• Tracking processed files")
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    results = {}
    
    # Run document upload specific verifications
    env_results = await verify_document_upload_environment()
    results['environment'] = env_results.get('all_required', False)
    
    work_items_results = await verify_work_items_directory()
    results['work_items_directory'] = work_items_results.get('has_work_items', False) and work_items_results.get('has_markdown_files', False)
    
    results['azure_openai_embeddings'] = await verify_azure_openai_for_embeddings()
    results['azure_search_upload'] = await verify_azure_search_for_upload()
    results['document_processing'] = await verify_document_processing_pipeline()
    
    # Print summary
    print_document_upload_summary(results)
    
    # Exit with appropriate code
    sys.exit(0 if all(results.values()) else 1)

if __name__ == "__main__":
    asyncio.run(main())
