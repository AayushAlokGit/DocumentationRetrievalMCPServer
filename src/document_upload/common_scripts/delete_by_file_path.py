"""
Delete Documents by File Path Script
===================================

This script deletes all documents from the Azure Cognitive Search index
that match a specific file path or filename pattern.

Usage:
    python delete_by_file_path.py <file_path_or_pattern>
    python delete_by_file_path.py "01-Architecture.md"
    python delete_by_file_path.py "PersonalDocumentationAssistantMCPServer/docs/AppDescription.md"

Example:
    python delete_by_file_path.py "01-Architecture.md"
    python delete_by_file_path.py "docs/MCP_SERVER_SETUP.md"
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


def delete_documents_by_file_path(file_path_pattern: str, confirm: bool = True) -> bool:
    """
    Delete all documents that match a specific file path pattern
    
    Args:
        file_path_pattern: File path or pattern to search for
        confirm: Whether to ask for confirmation before deletion
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Initialize the search service
        search_service = get_azure_search_service()
        
        print(f"🗑️  Delete Documents by File Path")
        print("=" * 50)
        print(f"[TARGET] File Path Pattern: {file_path_pattern}")
        print(f"[SERVICE] Azure Search Service: {search_service.service_name}")
        print(f"[INDEX] Search Index: {search_service.index_name}")
        
        # Test connection first
        if not search_service.test_connection():
            print("[ERROR] Failed to connect to Azure Cognitive Search")
            return False
        
        # First, find all documents that match the file path pattern
        print(f"\n[SEARCH] Finding documents matching file path pattern '{file_path_pattern}'...")
        
        # Get all documents to search through them
        results = search_service.search_client.search(
            search_text="*",
            select="id,title,file_path,context_id",
            top=1000  # Get up to 1000 documents
        )
        
        documents_to_delete = []
        matched_files = []
        
        file_pattern_lower = file_path_pattern.lower()
        
        for result in results:
            file_path = result.get("file_path", "")
            file_basename = Path(file_path).name.lower()
            file_path_lower = file_path.lower()
            
            # Check various matching conditions:
            # 1. Exact filename match
            # 2. Filename contained in the basename
            # 3. Pattern contained in the full path
            # 4. Exact path match
            if (file_basename == file_pattern_lower or 
                file_pattern_lower in file_basename or
                file_pattern_lower in file_path_lower or
                file_path == file_path_pattern):
                
                documents_to_delete.append(result)
                matched_files.append({
                    "id": result.get("id"),
                    "title": result.get("title", "Untitled"),
                    "file_path": file_path,
                    "context_id": result.get("context_id", "")
                })
        
        if not documents_to_delete:
            print(f"[INFO] No documents found matching file path pattern: {file_path_pattern}")
            return True
        
        # Show what will be deleted
        print(f"\n[PREVIEW] Found {len(documents_to_delete)} documents to delete:")
        for i, file_info in enumerate(matched_files[:10], 1):  # Show first 10
            print(f"   {i}. {file_info['title']} (Context ID: {file_info['context_id']})")
            print(f"      File: {file_info['file_path']}")
            print(f"      ID: {file_info['id']}")
        
        if len(documents_to_delete) > 10:
            print(f"   ... and {len(documents_to_delete) - 10} more documents")
        
        # Show matching criteria used
        print(f"\n[MATCH] Documents matched based on:")
        print(f"   - Exact filename match: {file_path_pattern}")
        print(f"   - Filename contains: {file_path_pattern}")
        print(f"   - Full path contains: {file_path_pattern}")
        print(f"   - Exact path match: {file_path_pattern}")
        
        # Confirmation prompt
        if confirm:
            print(f"\n[WARNING] This will permanently delete {len(documents_to_delete)} documents from the search index!")
            response = input("Are you sure you want to continue? (yes/no): ").lower().strip()
            if response not in ['yes', 'y']:
                print("[CANCELLED] Operation cancelled by user")
                return False
        
        # Perform the deletion - try filter method first for exact matches, then fallback to pattern matching
        print(f"\n[DELETE] Deleting documents matching file path pattern '{file_path_pattern}'...")
        
        # First, try exact filename match using the more efficient filter method
        deleted_count = search_service.delete_documents_by_filter({"file_name": file_path_pattern})
        
        # If no exact matches found, try the pattern matching approach
        if deleted_count == 0:
            print(f"[INFO] No exact filename matches found, trying pattern matching...")
            deleted_count = search_service.delete_documents_by_filename(file_path_pattern)
        
        if deleted_count > 0:
            print(f"[SUCCESS] Successfully deleted {deleted_count} documents matching pattern '{file_path_pattern}'")
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
        description="Delete all documents matching a file path pattern from Azure Cognitive Search",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Delete all documents with filename "01-Architecture.md"
    python delete_by_file_path.py "01-Architecture.md"
    
    # Delete documents with specific full path
    python delete_by_file_path.py "PersonalDocumentationAssistantMCPServer/docs/AppDescription.md"
    
    # Delete without confirmation prompt
    python delete_by_file_path.py "MCP_SERVER_SETUP.md" --no-confirm
    
    # Delete all documents containing "docs" in the path
    python delete_by_file_path.py "docs"
        """
    )
    
    parser.add_argument(
        'file_path_pattern',
        type=str,
        help='File path or pattern to match for deletion (can be filename, partial path, or full path)'
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
        success = delete_documents_by_file_path(
            file_path_pattern=args.file_path_pattern,
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
