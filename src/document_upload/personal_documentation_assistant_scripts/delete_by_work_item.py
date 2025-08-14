"""
Delete Documents by Work Item ID Script
======================================

This script deletes all documents from the Azure Cognitive Search index
that match a specific work item ID.

Usage:
    python delete_by_work_item.py <work_item_id>
    python delete_by_work_item.py docs
    python delete_by_work_item.py PersonalDocumentationAssistantMCPServer

Example:
    python delete_by_work_item.py docs
"""

import os
import sys
import argparse
from pathlib import Path
from typing import List

# Add src directory to path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root / "src" / "common"))

from dotenv import load_dotenv
from common.azure_cognitive_search import get_azure_search_service

# Load environment variables
load_dotenv()


def delete_documents_by_work_item(work_item_id: str, confirm: bool = True) -> bool:
    """
    Delete all documents for a specific work item from the search index
    
    Args:
        work_item_id: The work item ID to delete documents for
        confirm: Whether to ask for confirmation before deletion
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Initialize the search service
        search_service = get_azure_search_service()
        
        print(f"🗑️  Delete Documents by Work Item ID")
        print("=" * 50)
        print(f"[TARGET] Work Item ID: {work_item_id}")
        print(f"[SERVICE] Azure Search Service: {search_service.service_name}")
        print(f"[INDEX] Search Index: {search_service.index_name}")
        
        # Test connection first
        if not search_service.test_connection():
            print("[ERROR] Failed to connect to Azure Cognitive Search")
            return False
        
        # First, find all documents for the work item to show what will be deleted
        print(f"\n[SEARCH] Finding documents for work item '{work_item_id}'...")
        results = search_service.search_client.search(
            search_text="*",
            filter=f"work_item_id eq '{work_item_id}'",
            select="id,title,file_path,work_item_id",
            top=1000  # Get up to 1000 documents
        )
        
        documents_found = list(results)
        
        if not documents_found:
            print(f"[INFO] No documents found for work item: {work_item_id}")
            return True
        
        # Show what will be deleted
        print(f"\n[PREVIEW] Found {len(documents_found)} documents to delete:")
        for i, doc in enumerate(documents_found[:10], 1):  # Show first 10
            print(f"   {i}. {doc.get('title', 'Untitled')} (ID: {doc.get('id')})")
            print(f"      File: {doc.get('file_path', 'N/A')}")
        
        if len(documents_found) > 10:
            print(f"   ... and {len(documents_found) - 10} more documents")
        
        # Confirmation prompt
        if confirm:
            print(f"\n[WARNING] This will permanently delete {len(documents_found)} documents from the search index!")
            response = input("Are you sure you want to continue? (yes/no): ").lower().strip()
            if response not in ['yes', 'y']:
                print("[CANCELLED] Operation cancelled by user")
                return False
        
        # Perform the deletion
        print(f"\n[DELETE] Deleting documents for work item '{work_item_id}'...")
        deleted_count = search_service.delete_documents_by_filter({"context_id": work_item_id})
        
        if deleted_count > 0:
            print(f"[SUCCESS] Successfully deleted {deleted_count} documents for work item '{work_item_id}'")
            return True
        else:
            print(f"[WARNING] No documents were deleted")
            return False
            
    except Exception as e:
        print(f"[ERROR] Failed to delete documents: {e}")
        return False


def main():
    """Main entry point for the delete script"""
    
    parser = argparse.ArgumentParser(
        description="Delete all documents for a specific work item from Azure Cognitive Search",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Delete all documents with work_item_id "docs"
    python delete_by_work_item.py docs
    
    # Delete without confirmation prompt
    python delete_by_work_item.py docs --no-confirm
    
    # Delete documents for specific work item
    python delete_by_work_item.py PersonalDocumentationAssistantMCPServer
        """
    )
    
    parser.add_argument(
        'work_item_id',
        type=str,
        help='Work item ID to delete documents for (e.g., "docs", "WI-123")'
    )
    
    parser.add_argument(
        '--no-confirm',
        action='store_true',
        help='Skip confirmation prompt and delete immediately'
    )
    
    args = parser.parse_args()
    
    # Validate environment
    if not os.getenv('AZURE_SEARCH_SERVICE'):
        print("[ERROR] AZURE_SEARCH_SERVICE environment variable not set")
        sys.exit(1)
    
    if not os.getenv('AZURE_SEARCH_KEY'):
        print("[ERROR] AZURE_SEARCH_KEY environment variable not set")
        sys.exit(1)
    
    # Run the deletion
    try:
        success = delete_documents_by_work_item(
            work_item_id=args.work_item_id,
            confirm=not args.no_confirm
        )
        
        if success:
            print(f"\n✅ Deletion completed successfully!")
        else:
            print(f"\n❌ Deletion failed or was cancelled")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print(f"\n[CANCELLED] Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
