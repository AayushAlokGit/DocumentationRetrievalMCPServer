#!/usr/bin/env python3
"""
Document Upload System Verification Script - Strategy-Based Pipeline
===================================================================

This script verifies that the new strategy-based Document Upload System setup is correct
and all components required for document processing and indexing are working properly.

This verifies:
- Environment variables
- Azure OpenAI connection for embeddings  
- Azure Cognitive Search connection
- Work Items directory structure
- New strategy-based pipeline components
- Document processing capabilities (markdown, text, DOCX)
"""

import os
import sys
import asyncio
from pathlib import Path
from typing import Dict, Any, List
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# Add src directory to path - go up to project root then to src
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root / "src" / "common"))
sys.path.insert(0, str(project_root / "src" / "document_upload"))

def print_header(title: str):
    """Print a formatted header"""
    print(f"\n{'='*60}")
    print(f"🔍 {title}")
    print(f"{'='*60}")

def print_result(test_name: str, success: bool, message: str = ""):
    """Print test result"""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} {test_name}")
    if message:
        print(f"    {message}")

async def verify_environment_variables() -> Dict[str, bool]:
    """Verify environment variables required for document upload system"""
    print_header("Environment Variables")
    
    # Note: Environment variables are loaded via .env file, so we test functionality instead of direct env vars
    results = {}
    
    # Test if .env file exists
    env_file = project_root / ".env"
    if env_file.exists():
        print_result("Environment file (.env)", True, f"Found .env file at {env_file}")
        results['env_file'] = True
    else:
        print_result("Environment file (.env)", False, "No .env file found")
        results['env_file'] = False
    
    # Test critical environment variables that we know should be set
    critical_vars = [
        'PERSONAL_DOCUMENTATION_ROOT_DIRECTORY'
    ]
    
    for var in critical_vars:
        value = os.getenv(var)
        success = value is not None and value.strip() != ""
        results[var] = success
        
        if success:
            # Show partial value for security
            display_value = value[:30] + "..." if len(value) > 30 else value
            print_result(f"Environment variable: {var}", True, f"Set to: {display_value}")
        else:
            print_result(f"Environment variable: {var}", False, "Not set or empty")
    
    # Note: Azure credentials will be tested in Azure services section
    print("    Note: Azure credentials tested in Azure Services section")
    
    return results

async def verify_strategy_pipeline_components() -> Dict[str, bool]:
    """Verify that new strategy-based pipeline components are available"""
    print_header("Strategy-Based Pipeline Components")
    
    results = {}
    
    # Test importing pipeline components with correct paths
    try:
        from document_upload.document_processing_pipeline import DocumentProcessingPipeline
        print_result("DocumentProcessingPipeline import", True, "Main pipeline class available")
        results['pipeline'] = True
    except ImportError as e:
        print_result("DocumentProcessingPipeline import", False, f"Import error: {e}")
        results['pipeline'] = False
    
    # Test importing discovery strategies
    try:
        from document_upload.discovery_strategies import (
            GeneralDocumentDiscoveryStrategy, 
            PersonalDocumentationDiscoveryStrategy
        )
        print_result("Discovery strategies import", True, "Discovery strategy classes available")
        results['discovery'] = True
    except ImportError as e:
        print_result("Discovery strategies import", False, f"Import error: {e}")
        results['discovery'] = False
    
    # Test importing processing strategies
    try:
        from document_upload.processing_strategies import (
            PersonalDocumentationAssistantProcessingStrategy
        )
        print_result("Processing strategies import", True, "Processing strategy classes available")
        results['processing'] = True
    except ImportError as e:
        print_result("Processing strategies import", False, f"Import error: {e}")
        results['processing'] = False
    
    # Test Azure Cognitive Search (more important than DOCX)
    try:
        from common.azure_cognitive_search import AzureCognitiveSearch
        print_result("Azure Cognitive Search import", True, "Azure search service available")
        results['azure_search'] = True
    except ImportError as e:
        print_result("Azure Cognitive Search import", False, f"Import error: {e}")
        results['azure_search'] = False
    
    # Test DOCX support (optional)
    try:
        from docx import Document
        print_result("DOCX support", True, "python-docx library available")
        results['docx'] = True
    except ImportError:
        print_result("DOCX support", False, "python-docx library not installed (optional)")
        results['docx'] = False
    
    return results

async def verify_azure_services() -> Dict[str, bool]:
    """Verify connections to Azure services"""
    print_header("Azure Services Connectivity")
    
    results = {}
    
    # Test Azure OpenAI connection
    try:
        from common.embedding_service import get_embedding_generator
        embedding_service = get_embedding_generator()
        
        connection_test = embedding_service.test_connection()
        if connection_test:
            print_result("Azure OpenAI connection", True, "Embedding service connection successful")
            results['openai'] = True
        else:
            print_result("Azure OpenAI connection", False, "Connection test failed")
            results['openai'] = False
            
    except Exception as e:
        print_result("Azure OpenAI connection", False, f"Error: {e}")
        results['openai'] = False
    
    # Test Azure Cognitive Search connection
    try:
        from common.azure_cognitive_search import AzureCognitiveSearch
        
        service_name = os.getenv('AZURE_SEARCH_SERVICE')
        admin_key = os.getenv('AZURE_SEARCH_KEY')
        index_name = os.getenv('AZURE_SEARCH_INDEX', 'work-items-index')
        
        if service_name and admin_key:
            search_service = AzureCognitiveSearch()
            
            # Test 1: Check if index exists
            try:
                # Check if index exists by trying to get it
                from azure.search.documents.indexes import SearchIndexClient
                from azure.core.credentials import AzureKeyCredential
                
                index_client = SearchIndexClient(
                    endpoint=f"https://{service_name}.search.windows.net",
                    credential=AzureKeyCredential(admin_key)
                )
                
                # Try to get the index
                try:
                    index = index_client.get_index(index_name)
                    print_result("Azure Search Index exists", True, f"Index '{index_name}' found with {len(index.fields)} fields")
                    results['index_exists'] = True
                    
                    # Test 2: Count documents in the index
                    try:
                        # Use search with empty query to count all documents
                        search_results = search_service.search_client.search("*", top=1, include_total_count=True)
                        total_count = search_results.get_count()
                        
                        if total_count is not None:
                            if total_count > 0:
                                print_result("Index document count", True, f"Index contains {total_count} documents")
                            else:
                                print_result("Index document count", True, "Index is empty (0 documents)")
                            results['document_count'] = True
                        else:
                            print_result("Index document count", False, "Could not retrieve document count")
                            results['document_count'] = False
                            
                    except Exception as count_error:
                        print_result("Index document count", False, f"Error counting documents: {count_error}")
                        results['document_count'] = False
                        
                except Exception as index_error:
                    if "NotFound" in str(index_error) or "404" in str(index_error):
                        print_result("Azure Search Index exists", False, f"Index '{index_name}' not found - needs to be created")
                        results['index_exists'] = False
                        results['document_count'] = False
                    else:
                        print_result("Azure Search Index exists", False, f"Index access error: {index_error}")
                        results['index_exists'] = False
                        results['document_count'] = False
                
                # Test 3: Basic search service connectivity
                try:
                    # Test basic connectivity by listing indexes
                    indexes = list(index_client.list_indexes())
                    print_result("Azure Cognitive Search connection", True, f"Service accessible, found {len(indexes)} indexes")
                    results['search'] = True
                except Exception as e:
                    print_result("Azure Cognitive Search connection", False, f"Service access error: {e}")
                    results['search'] = False
                    
            except Exception as e:
                print_result("Azure Cognitive Search connection", False, f"Service initialization error: {e}")
                results['search'] = False
                results['index_exists'] = False
                results['document_count'] = False
        else:
            print_result("Azure Cognitive Search connection", False, "Missing service name or admin key")
            results['search'] = False
            results['index_exists'] = False
            results['document_count'] = False
            
    except Exception as e:
        print_result("Azure Cognitive Search connection", False, f"Error: {e}")
        results['search'] = False
    
    return results

async def verify_work_items_directory() -> Dict[str, bool]:
    """Verify work items directory structure"""
    print_header("Work Items Directory Structure")
    
    results = {}
    
    work_items_dir = os.getenv('PERSONAL_DOCUMENTATION_ROOT_DIRECTORY')
    
    if not work_items_dir:
        print_result("Work items directory configured", False, "PERSONAL_DOCUMENTATION_ROOT_DIRECTORY not set")
        results['configured'] = False
        return results
    
    work_items_path = Path(work_items_dir)
    
    # Check if directory exists
    if work_items_path.exists():
        print_result("Work items directory exists", True, f"Found: {work_items_path}")
        results['exists'] = True
        
        # Count work item directories
        work_item_dirs = [d for d in work_items_path.iterdir() if d.is_dir() and not d.name.startswith('.')]
        work_item_count = len(work_item_dirs)
        
        if work_item_count > 0:
            print_result("Work item directories found", True, f"Found {work_item_count} work item directories")
            results['has_work_items'] = True
            
            # Show first few work items
            sample_work_items = [d.name for d in work_item_dirs[:5]]
            print(f"    Sample work items: {', '.join(sample_work_items)}")
            if work_item_count > 5:
                print(f"    ... and {work_item_count - 5} more")
            
            # Count total documents
            total_docs = 0
            supported_extensions = ['.md', '.txt', '.docx']
            
            for work_item_dir in work_item_dirs[:10]:  # Check first 10 work items
                for ext in supported_extensions:
                    total_docs += len(list(work_item_dir.rglob(f"*{ext}")))
            
            print_result("Documents found", True, f"Found {total_docs} documents in first 10 work items")
            results['has_documents'] = total_docs > 0
            
        else:
            print_result("Work item directories found", False, "No work item directories found")
            results['has_work_items'] = False
            results['has_documents'] = False
    else:
        print_result("Work items directory exists", False, f"Directory not found: {work_items_path}")
        results['exists'] = False
        results['has_work_items'] = False
        results['has_documents'] = False
    
    results['configured'] = True
    return results

async def test_pipeline_functionality() -> Dict[str, bool]:
    """Test basic pipeline functionality with a small test (optional)"""
    print_header("Pipeline Functionality Test (Optional)")
    
    results = {}
    
    try:
        # Try to import and test basic functionality
        from document_upload.processing_strategies import PersonalDocumentationAssistantProcessingStrategy
        
        # Simple test: Create strategy instance
        strategy = PersonalDocumentationAssistantProcessingStrategy()
        strategy_name = strategy.get_strategy_name()
        
        if strategy_name == "PersonalDocumentationAssistant":
            print_result("Strategy instantiation", True, f"Strategy '{strategy_name}' created successfully")
            results['strategy_test'] = True
        else:
            print_result("Strategy instantiation", False, "Unexpected strategy name")
            results['strategy_test'] = False
        
        results['test'] = True
        
    except Exception as e:
        print_result("Pipeline functionality test", False, f"Error: {e}")
        print("    Note: This is optional - core Azure services are working")
        results['test'] = False
        results['strategy_test'] = False
    
    return results

async def main():
    """Main verification function"""
    print("🚀 Document Upload System Verification - Strategy-Based Pipeline")
    print("=" * 80)
    
    all_results = {}
    
    # Run all verification tests
    env_results = await verify_environment_variables()
    all_results['environment'] = env_results
    
    pipeline_results = await verify_strategy_pipeline_components()
    all_results['pipeline'] = pipeline_results
    
    azure_results = await verify_azure_services()
    all_results['azure'] = azure_results
    
    directory_results = await verify_work_items_directory()
    all_results['directory'] = directory_results
    
    test_results = await test_pipeline_functionality()
    all_results['test'] = test_results
    
    # Print summary
    print_header("Verification Summary")
    
    # Count overall results
    total_tests = 0
    passed_tests = 0
    
    for category, results in all_results.items():
        category_passed = sum(1 for success in results.values() if success)
        category_total = len(results)
        total_tests += category_total
        passed_tests += category_passed
        
        status = "✅" if category_passed == category_total else "⚠️" if category_passed > 0 else "❌"
        print(f"{status} {category.title()}: {category_passed}/{category_total} tests passed")
    
    print(f"\n📊 Overall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All verification tests passed! Your system is ready for document upload.")
    elif passed_tests > total_tests * 0.8:
        print("⚠️  Most tests passed. Check the failed tests above and fix any issues.")
    else:
        print("❌ Multiple verification tests failed. Please address the issues above.")
    
    # System readiness assessment
    print_header("System Readiness Assessment")
    
    # Check critical components (must work for system to function)
    critical_checks = {
        'Environment file exists': all_results['environment'].get('env_file', False),
        'Work items directory configured': all_results['environment'].get('PERSONAL_DOCUMENTATION_ROOT_DIRECTORY', False),
        'Azure OpenAI connected': all_results['azure'].get('openai', False),
        'Azure Search connected': all_results['azure'].get('search', False),
        'Search index exists': all_results['azure'].get('index_exists', False),
        'Work items directory ready': all_results['directory'].get('exists', False) and all_results['directory'].get('has_documents', False),
    }
    
    # Optional checks (nice to have but not critical for basic functionality)
    optional_checks = {
        'Document count available': all_results['azure'].get('document_count', False),
        'Pipeline components importable': all_results['pipeline'].get('processing', False),
        'DOCX support': all_results['pipeline'].get('docx', False),
        'Strategy test passed': all_results['test'].get('strategy_test', False)
    }
    
    print("🔧 Critical Requirements:")
    for check, passed in critical_checks.items():
        print_result(check, passed)
    
    print("\n📋 Optional Features:")
    for check, passed in optional_checks.items():
        print_result(check, passed)
    
    overall_ready = all(critical_checks.values())
    
    if overall_ready:
        print("\n🚀 SYSTEM READY: You can now run document upload scripts!")
        print("📋 Next steps:")
        print("   1. Run: python src\\document_upload\\personal_documentation_assistant_scripts\\upload_work_items.py --dry-run")
        print("   2. Run: python src\\document_upload\\personal_documentation_assistant_scripts\\upload_work_items.py --work-item \"Task XXXXX\"")
        print("   3. Force reprocess: python src\\document_upload\\personal_documentation_assistant_scripts\\upload_work_items.py --work-item \"Task XXXXX\" --force")
    else:
        print("\n⚠️  SYSTEM NOT READY: Please fix the failed critical checks above before running uploads.")
        print("    Note: Optional features failing is OK - core functionality is what matters.")
    
    return overall_ready

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n⚠️  Verification cancelled by user")
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        sys.exit(1)
