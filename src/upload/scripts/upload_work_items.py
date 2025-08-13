"""
Bulk Upload Script for Work Item Documentation
=============================================

This script uploads all work item documents to Azure Cognitive Search index.
It reads the WORK_ITEMS_PATH from environment variables and processes all 
markdown files found in the work item directories.

This script is a wrapper around the main upload functionality in document_upload.py
and provides additional options for selective uploading and dry-run capabilities.

Usage:
    python scripts/upload_work_items.py [--reset] [--work-item WI-123] [--dry-run]

Options:
    --reset         Reset the processing tracker and delete all documents from search index
    --work-item     Upload only specific work item (e.g., WI-123)
    --dry-run       Show what would be uploaded without actually uploading
    --force         Force reprocessing of already processed files
"""

import os
import sys
import argparse
import asyncio
from pathlib import Path
from typing import List, Optional

# Add src directory to path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root / "src" / "common"))
sys.path.insert(0, str(project_root / "src" / "upload"))

from dotenv import load_dotenv
from document_upload import main as upload_main
from document_utils import discover_markdown_files
from file_tracker import DocumentProcessingTracker
from common.azure_cognitive_search import get_azure_search_service

# Load environment variables
load_dotenv()


def get_work_items_from_path(work_items_path: str) -> List[str]:
    """Get list of all work item directories from the given path"""
    work_items_dir = Path(work_items_path)
    if not work_items_dir.exists():
        return []
    
    work_items = []
    for item in work_items_dir.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            work_items.append(item.name)
    return sorted(work_items)


def get_files_for_work_item(work_items_path: str, work_item_id: str) -> List[Path]:
    """Get all markdown files for a specific work item"""
    work_item_dir = Path(work_items_path) / work_item_id
    if not work_item_dir.exists():
        return []
    
    files = []
    for file in work_item_dir.rglob("*.md"):
        files.append(file)
    return files


def show_upload_preview(work_items_path: str, work_item_id: Optional[str] = None):
    """Show what will be uploaded without actually uploading"""
    work_items_dir = Path(work_items_path)
    
    print("� Upload Preview (Dry Run)")
    print("=" * 40)
    print(f"[FOLDER] Work Items Path: {work_items_path}")
    print(f"[SEARCH] Search Service: {os.getenv('AZURE_SEARCH_SERVICE')}")
    print(f"[LIST] Search Index: {os.getenv('AZURE_SEARCH_INDEX', 'work-items-index')}")
    
    if work_item_id:
        print(f"[TARGET] Target Work Item: {work_item_id}")
        files = get_files_for_work_item(work_items_path, work_item_id)
        print(f"[DOCUMENT] Files to process: {len(files)}")
        
        for file in files:
            relative_path = file.relative_to(work_items_dir)
            print(f"   • {relative_path}")
    else:
        print(f"[TARGET] Target: All Work Items")
        work_items = get_work_items_from_path(work_items_path)
        total_files = 0
        
        print(f"� Work Items to Process ({len(work_items)}):")
        for wi in work_items:
            files = get_files_for_work_item(work_items_path, wi)
            total_files += len(files)
            print(f"   • {wi}: {len(files)} files")
        
        print(f"[DOCUMENT] Total Files: {total_files}")
    
    print(f"\nTips: This is a dry run - no files will be uploaded")
    print(f"Tips: Remove --dry-run flag to perform actual upload")


async def upload_work_items(work_item_id: Optional[str] = None, 
                          reset_tracker: bool = False,
                          dry_run: bool = False,
                          force: bool = False):
    """Upload work item documents to Azure Search"""
    
    print("[START] Work Item Documentation Upload")
    print("=" * 50)
    
    # Get configuration
    work_items_path = os.getenv('WORK_ITEMS_PATH')
    if not work_items_path:
        print("[ERROR] WORK_ITEMS_PATH environment variable not set")
        return
    
    work_items_dir = Path(work_items_path)
    if not work_items_dir.exists():
        print(f"[ERROR] Work items directory not found: {work_items_path}")
        return
    
    # Show available work items
    work_items = get_work_items_from_path(work_items_path)
    print(f"File: Available Work Items ({len(work_items)}):")
    for wi in work_items[:10]:  # Show first 10
        print(f"   • {wi}")
    if len(work_items) > 10:
        print(f"   ... and {len(work_items) - 10} more")
    
    # Validate specific work item if provided
    if work_item_id and work_item_id not in work_items:
        print(f"[ERROR] Work item '{work_item_id}' not found")
        print(f"Available work items: {', '.join(work_items)}")
        return
    
    # Handle dry run
    if dry_run:
        show_upload_preview(work_items_path, work_item_id)
        return
    
    # Handle reset tracker
    if reset_tracker:
        tracker = DocumentProcessingTracker("processed_files.json")
        print(f"[REFRESH] Resetting processing tracker...")
        
        # Delete all documents from Azure Cognitive Search index
        print(f"[SEARCH] Deleting all documents from Azure Cognitive Search index...")
        try:
            search_service = get_azure_search_service()
            deleted_count = search_service.delete_all_documents()
            print(f"   [SUCCESS] Deleted {deleted_count} documents from search index")
        except Exception as e:
            print(f"   [ERROR] Failed to delete documents from search index: {e}")
            print(f"   [WARNING] Continuing with file tracker reset only...")
        
        # Clear the tracker after deletion
        tracker.reset()
        tracker.save()
        
        print(f"[RESULTS] Reset processing completed:")
        print(f"   • Processing tracker cleared: ✅")
        print(f"   [SUCCESS] All files will be reprocessed on next upload")
    
    # Handle force reprocessing for specific work item
    if force and work_item_id:
        tracker = DocumentProcessingTracker("processed_files.json")
        files_to_force = get_files_for_work_item(work_items_path, work_item_id)
        print(f"[FAST] Force mode: Marking {len(files_to_force)} files for reprocessing...")
        
        for file in files_to_force:
            if tracker.is_processed(file):
                tracker.mark_unprocessed(file)
        
        tracker.save()
        print(f"   [SUCCESS] Files marked for reprocessing")
    
    # Set up environment for specific work item upload
    original_path = None
    if work_item_id:
        original_path = os.environ.get('WORK_ITEMS_PATH')
        work_item_dir = work_items_dir / work_item_id
        os.environ['WORK_ITEMS_PATH'] = str(work_item_dir)
        print(f"[TARGET] Uploading specific work item: {work_item_id}")
        print(f"[FOLDER] Target directory: {work_item_dir}")
    
    try:
        # Use the existing main upload function from document_upload.py
        print(f"[START] Starting upload using document_upload.main()...")
        await upload_main()
        
        print(f"\n🎉 Upload completed successfully!")
        print(f"Tips: Documents are now searchable via:")
        print(f"   • VS Code MCP server integration")
        print(f"   • search_documents.py script")
        print(f"   • Azure Cognitive Search REST API")
        
    finally:
        # Restore original environment if it was changed
        if original_path is not None:
            os.environ['WORK_ITEMS_PATH'] = original_path


def main():
    """Main entry point for the upload script"""
    
    parser = argparse.ArgumentParser(
        description="Upload work item documentation to Azure Cognitive Search",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Upload all work items
    python scripts/upload_work_items.py
    
    # Upload specific work item
    python scripts/upload_work_items.py --work-item WI-123
    
    # Show what would be uploaded without uploading
    python scripts/upload_work_items.py --dry-run
    
    # Reset and reprocess all files (also deletes all documents from search index)
    python scripts/upload_work_items.py --reset
    
    # Force reprocess specific work item
    python scripts/upload_work_items.py --work-item WI-123 --force
        """
    )
    
    parser.add_argument(
        '--work-item', 
        type=str, 
        help='Upload only specific work item (e.g., WI-123)'
    )
    
    parser.add_argument(
        '--reset', 
        action='store_true',
        help='Reset processing tracker and delete all documents from search index'
    )
    
    parser.add_argument(
        '--dry-run', 
        action='store_true',
        help='Show what would be uploaded without actually uploading'
    )
    
    parser.add_argument(
        '--force', 
        action='store_true',
        help='Force reprocessing of already processed files (use with --work-item)'
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.force and not args.work_item:
        print("[ERROR] --force option requires --work-item to be specified")
        sys.exit(1)
    
    # Run the upload
    try:
        asyncio.run(upload_work_items(
            work_item_id=args.work_item,
            reset_tracker=args.reset,
            dry_run=args.dry_run,
            force=args.force
        ))
    except KeyboardInterrupt:
        print(f"\n[WARNING]  Upload cancelled by user")
    except Exception as e:
        print(f"[ERROR] Upload failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
