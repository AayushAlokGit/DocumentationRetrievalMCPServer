"""
Azure Cognitive Search Index Creation Script
==========================================

Enhanced script to create and manage the Azure Cognitive Search index with vector search 
capabilities. Uses the centralized AzureCognitiveSearch service class for consistent 
operations and proper error handling.

Features:
- Connection testing with comprehensive validation
- Index creation with optimized schema for document processing pipeline
- Index existence checking with detailed statistics
- Safe index deletion with confirmation prompts
- Integration with document processing pipeline schema
- Support for custom vector dimensions

Usage:
    python create_index.py [--vector-dimensions 1536] [--force-recreate]

The script will:
1. Test connection to Azure Cognitive Search
2. Check if index already exists with statistics
3. Offer to recreate existing index if found
4. Create new index with schema matching the processing pipeline
5. Provide guidance for next steps
"""

import os
import sys
import argparse
from pathlib import Path

# Add the src directory to the path so we can import our modules
current_dir = Path(__file__).parent
src_dir = current_dir.parent.parent
sys.path.insert(0, str(src_dir))

from dotenv import load_dotenv
from src.common.vector_search_services.azure_cognitive_search import get_azure_search_service

# Load environment variables
load_dotenv()


def create_search_index(vector_dimensions: int = 1536, force_recreate: bool = False):
    """
    Create the Azure Cognitive Search index using the centralized service class.
    
    Args:
        vector_dimensions: Number of dimensions for vector embeddings
        force_recreate: If True, delete existing index without prompting
        
    Returns:
        bool: True if successful, False otherwise
    """
    
    try:
        # Get the Azure Search service instance
        search_service = get_azure_search_service()
        
        print(f"🔧 Index Creation Configuration:")
        print(f"   Service: {search_service.service_name}")
        print(f"   Index: {search_service.index_name}")
        print(f"   Vector dimensions: {vector_dimensions}")
        print(f"   Force recreate: {force_recreate}")
        print("-" * 50)
        
        # Check if index already exists
        if search_service.index_exists():
            stats = search_service.get_index_stats()
            print(f"⚠️  Index '{search_service.index_name}' already exists:")
            print(f"   Documents: {stats.get('document_count', 0):,}")
            
            if not force_recreate:
                response = input("\nRecreate existing index? This will DELETE all data! (yes/no): ")
                if response.lower() not in ['yes', 'y']:
                    print("🚫 Index creation cancelled")
                    return False
            
            print("🗑️  Deleting existing index...")
            if not search_service.delete_index():
                print("❌ Failed to delete existing index")
                return False
            print("✅ Existing index deleted successfully")
        
        # Create the new index
        print(f"\n🏗️  Creating new search index...")
        success = search_service.create_index(vector_dimensions=vector_dimensions)
        
        if success:
            print("✅ Index created successfully!")
            print(f"\n📊 Index Schema Summary:")
            
            # Display the key fields that match our processing pipeline
            schema_fields = [
                ("id", "Unique document chunk identifier"),
                ("content", "Searchable text content"),
                ("content_vector", f"Vector embeddings ({vector_dimensions} dimensions)"),
                ("file_path", "Full file path"),
                ("file_name", "File name"),
                ("file_type", "File extension (.md, .txt, .docx)"),
                ("title", "Document title"),
                ("tags", "Document tags (comma-separated)"),
                ("category", "Document category"),
                ("context_name", "Context identifier (work items, projects)"),
                ("last_modified", "Last modification timestamp"),
                ("chunk_index", "Chunk identifier within document"),
                ("metadata_json", "Additional metadata as JSON")
            ]
            
            for field, description in schema_fields:
                print(f"   • {field:<20} - {description}")
            
            print(f"\n🎯 Next Steps:")
            print(f"   1. Upload documents using upload_single_file.py or upload_work_items.py")
            print(f"   2. Test search functionality using the MCP server")
            print(f"   3. Monitor index statistics via Azure portal")
            
            return True
        else:
            print("❌ Index creation failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error during index creation: {e}")
        import traceback
        print("Full error traceback:")
        traceback.print_exc()
        return False


def check_index_exists():
    """
    Check if the search index exists and display comprehensive statistics.
    
    Returns:
        bool: True if index exists, False otherwise
    """
    try:
        # Get the Azure Search service instance
        search_service = get_azure_search_service()
        # Use the service class method to check index existence
        exists = search_service.index_exists()
        return exists
        
    except Exception as e:
        print(f"❌ Error checking index existence: {e}")
        return False


def delete_index():
    """
    Delete the search index with confirmation (use with caution!).
    
    Returns:
        bool: True if successful, False otherwise
    """
    
    try:
        # Get the Azure Search service instance
        search_service = get_azure_search_service()
        
        if not search_service.index_exists():
            print(f"ℹ️  Index '{search_service.index_name}' does not exist")
            return True
        
        # Get statistics before deletion
        stats = search_service.get_index_stats()
        print(f"⚠️  WARNING: This will permanently delete:")
        print(f"   Index: {search_service.index_name}")
        print(f"   Documents: {stats.get('document_count', 0):,}")
        print(f"   Storage: {stats.get('storage_size', 0):,} bytes")
        
        response = input("\nAre you absolutely sure? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("🚫 Index deletion cancelled")
            return False
        
        # Use the service class method to delete the index
        success = search_service.delete_index()
        
        if success:
            print("✅ Index deleted successfully")
        else:
            print("❌ Failed to delete index")
            
        return success
        
    except Exception as e:
        print(f"❌ Error during index deletion: {e}")
        return False


def test_connection():
    """
    Test connection to Azure Cognitive Search with comprehensive validation.
    
    Returns:
        bool: True if connection successful, False otherwise
    """
    
    try:
        # Get the Azure Search service instance
        search_service = get_azure_search_service()
        
        # Use the service class method to test connection
        success = search_service.test_connection()
        
        if success:
            print("✅ Connection to Azure Cognitive Search successful")
            print(f"   Service: {search_service.service_name}")
            print(f"   Endpoint: {search_service.endpoint}")
            print(f"   Target index: {search_service.index_name}")
        else:
            print("❌ Connection to Azure Cognitive Search failed")
            print("   Check your environment variables and network connectivity")
            
        return success
        
    except Exception as e:
        print(f"❌ Error testing connection: {e}")
        return False


def validate_environment():
    """Validate that all required environment variables are set"""
    required_vars = [
        'AZURE_SEARCH_SERVICE',
        'AZURE_SEARCH_KEY',
        'AZURE_OPENAI_ENDPOINT',
        'AZURE_OPENAI_KEY'
    ]
    
    missing_vars = []
    optional_vars = ['AZURE_SEARCH_INDEX']  # Has default value
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        
        print("\n📋 Required environment variables:")
        print("   AZURE_SEARCH_SERVICE - Azure Cognitive Search service name")
        print("   AZURE_SEARCH_KEY - Azure Cognitive Search admin key")
        print("   AZURE_OPENAI_ENDPOINT - Azure OpenAI endpoint")
        print("   AZURE_OPENAI_KEY - Azure OpenAI API key")
        print("\n📋 Optional environment variables:")
        print("   AZURE_SEARCH_INDEX - Search index name (default: work-items-index)")
        return False
    
    return True


def main():
    """Main function to create and manage the search index"""
    
    parser = argparse.ArgumentParser(
        description="Create and manage Azure Cognitive Search index for document processing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Create index with default settings
    python create_index.py
    
    # Create index with custom vector dimensions
    python create_index.py --vector-dimensions 768
    
    # Force recreate existing index
    python create_index.py --force-recreate
    
    # Check if index exists
    python create_index.py --check-only
    
    # Delete existing index (with confirmation)
    python create_index.py --delete
        """
    )
    
    parser.add_argument(
        '--vector-dimensions',
        type=int,
        default=1536,
        help='Number of dimensions for vector embeddings (default: 1536 for text-embedding-ada-002)'
    )
    
    parser.add_argument(
        '--force-recreate',
        action='store_true',
        help='Force recreation of existing index without confirmation'
    )
    
    parser.add_argument(
        '--check-only',
        action='store_true',
        help='Only check if index exists, do not create'
    )
    
    parser.add_argument(
        '--delete',
        action='store_true',
        help='Delete existing index (with confirmation)'
    )
    
    args = parser.parse_args()
    
    print("🏗️  Azure Cognitive Search Index Management")
    print("=" * 60)
    
    # Validate environment
    if not validate_environment():
        sys.exit(1)
    
    # Test connection first
    print("🔗 Testing connection to Azure Cognitive Search...")
    if not test_connection():
        print("\n❌ Cannot connect to Azure Cognitive Search")
        print("   Please check your environment variables and network connectivity")
        sys.exit(1)
    
    # Handle delete operation
    if args.delete:
        print(f"\n🗑️  Delete Index Operation")
        success = delete_index()
        sys.exit(0 if success else 1)
    
    # Check if index exists
    print(f"\n📋 Checking index status...")
    index_exists = check_index_exists()
    
    # Handle check-only operation
    if args.check_only:
        print(f"\n👁️  Check complete - index {'exists' if index_exists else 'does not exist'}")
        sys.exit(0)
    
    # Handle index creation
    if not index_exists or args.force_recreate:
        print(f"\n🏗️  Creating search index...")
        success = create_search_index(
            vector_dimensions=args.vector_dimensions,
            force_recreate=args.force_recreate
        )
        
        if success:
            print(f"\n🎉 Index setup completed successfully!")
            print(f"\n🚀 Ready for document upload!")
            print(f"   • Use upload_single_file.py for individual files")
            print(f"   • Use upload_work_items.py for bulk uploads")
            print(f"   • Use the MCP server for querying")
            sys.exit(0)
        else:
            print(f"\n❌ Index creation failed!")
            sys.exit(1)
    else:
        print(f"\n✅ Index already exists and is ready for use!")
        print(f"   • Use --force-recreate to recreate the index")
        print(f"   • Use --delete to delete the existing index")
        sys.exit(0)


if __name__ == "__main__":
    main()
