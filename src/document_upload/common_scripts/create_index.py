"""
Azure Cognitive Search Index Creation Script
==========================================

Creates the search index with vector search capabilities using the AzureCognitiveSearch service class.
This script provides a simplified interface for index management by leveraging the centralized
service class instead of directly implementing Azure SDK calls.

Features:
- Connection testing
- Index creation with matching schema from service class
- Index existence checking with statistics
- Safe index deletion with confirmation
- Comprehensive error handling and user feedback

Usage:
    python create_index.py

The script will:
1. Test connection to Azure Cognitive Search
2. Check if index already exists
3. Offer to recreate existing index if found
4. Create new index with optimized schema
5. Provide next steps for document upload
"""

import os
import sys
from pathlib import Path

# Add the src directory to the path so we can import our modules
current_dir = Path(__file__).parent
src_dir = current_dir.parent.parent
sys.path.insert(0, str(src_dir))

from common.azure_cognitive_search import get_azure_search_service


def create_search_index(vector_dimensions: int = 1536):
    """Create the Azure Cognitive Search index using the service class"""
    
    try:
        # Get the Azure Search service instance
        search_service = get_azure_search_service()
        
        # Use the service class method to create the index
        success = search_service.create_index(vector_dimensions=vector_dimensions)
        
        if success:
            print("\n🎉 Index creation successful!")
        else:
            print("\n[ERROR] Index creation failed!")
            
        return success
        
    except Exception as e:
        print(f"[ERROR] Error during index creation: {e}")
        return False


def check_index_exists():
    """Check if the search index already exists using the service class"""
    
    try:
        # Get the Azure Search service instance
        search_service = get_azure_search_service()
        
        # Use the service class method to check index existence
        exists = search_service.index_exists()
        
        if exists:
            print(f"[SUCCESS] Index '{search_service.index_name}' already exists")
            # Get some basic stats
            stats = search_service.get_index_stats()
            print(f"   Documents: {stats.get('document_count', 0)}")
            print(f"   Work Items: {stats.get('work_item_count', 0)}")
        else:
            print(f"[INFO] Index '{search_service.index_name}' does not exist")
            
        return exists
        
    except Exception as e:
        print(f"[ERROR] Error checking index existence: {e}")
        return False


def delete_index():
    """Delete the search index using the service class (use with caution!)"""
    
    try:
        # Get the Azure Search service instance
        search_service = get_azure_search_service()
        
        # Use the service class method to delete the index
        success = search_service.delete_index()
        
        return success
        
    except Exception as e:
        print(f"[ERROR] Error during index deletion: {e}")
        return False


def test_connection():
    """Test connection to Azure Cognitive Search using the service class"""
    
    try:
        # Get the Azure Search service instance
        search_service = get_azure_search_service()
        
        # Use the service class method to test connection
        success = search_service.test_connection()
        
        if success:
            print("[SUCCESS] Connection to Azure Cognitive Search successful")
            print(f"   Service: {search_service.service_name}")
            print(f"   Endpoint: {search_service.endpoint}")
            print(f"   Index: {search_service.index_name}")
        else:
            print("[ERROR] Connection to Azure Cognitive Search failed")
            
        return success
        
    except Exception as e:
        print(f"[ERROR] Error testing connection: {e}")
        return False


def main():
    """Main function to create the search index"""
    
    print("Azure Cognitive Search Index Setup")
    print("=" * 40)
    
    # Test connection first
    print("Testing connection to Azure Cognitive Search...")
    if not test_connection():
        print("\n[ERROR] Cannot connect to Azure Cognitive Search.")
        print("Please check your environment variables and credentials.")
        return
    
    # Check if index exists
    print("\nChecking if index exists...")
    if check_index_exists():
        response = input("\nIndex already exists. Recreate? (y/N): ")
        if response.lower() == 'y':
            print("Deleting existing index...")
            if not delete_index():
                print("[ERROR] Failed to delete existing index. Aborting.")
                return
        else:
            print("Keeping existing index.")
            return
    
    # Create the index
    print("\nCreating search index...")
    success = create_search_index()
    
    if success:
        print("\n🎉 Setup complete! You can now upload documents.")
        print("\nNext steps:")
        print("1. Use upload_single_file.py to upload individual documents")
        print("2. Use upload_work_items.py to upload work item documentation")
        print("3. Test search functionality with the MCP server")
    else:
        print("\n[ERROR] Setup failed. Check the error messages above and try again.")


if __name__ == "__main__":
    main()
