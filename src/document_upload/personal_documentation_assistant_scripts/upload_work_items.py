#!/usr/bin/env python3
"""
Bulk Upload Script for Work Item Documentation
=================================

This script uploads all work item documents to Azure Cognitive Search index using the new
strategy-based document processing pipeline. It supports the full 3-phase pipeline:
1. Document Discovery - Find work item documents
2. Document Processing - Extract metadata, chunk, and generate embeddings
3. Document Upload - Upload to Azure Cognitive Search

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
sys.path.insert(0, str(project_root / "src" / "document upload"))

from dotenv import load_dotenv
from document_processing_pipeline import DocumentProcessingPipeline, DocumentDiscoveryPhase
from discovery_strategies import PersonalDocumentationDiscoveryStrategy
from processing_strategies import PersonalDocumentationAssistantProcessingStrategy
from file_tracker import DocumentProcessingTracker
from common.azure_cognitive_search import get_azure_search_service

# Load environment variables
load_dotenv()


def get_work_items_from_path(work_items_directory: str) -> List[str]:
    """Get list of all work item directories from the given path"""
    work_items_dir = Path(work_items_directory)
    if not work_items_dir.exists():
        return []
    
    work_items = []
    for item in work_items_dir.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            work_items.append(item.name)
    return sorted(work_items)


def show_upload_preview(work_items_directory: str, work_item_filter: Optional[str] = None, force: bool = False):
    """Show what would be uploaded without actually uploading"""
    print("🔍 DRY RUN: Preview of documents to be processed")
    if force:
        print("🔄 FORCE REPROCESS MODE: Will clean up tracker and search index first")
    print("=" * 60)
    
    work_items_dir = Path(work_items_directory)
    if not work_items_dir.exists():
        print(f"❌ Work items directory not found: {work_items_directory}")
        return
    
    # Initialize document tracker for preview
    tracker = DocumentProcessingTracker("processed_files.json")
    print(f"📋 Document tracker: {tracker.get_tracking_source()}")
    
    # Create discovery strategy (no filter needed - handled by path selection)
    discovery_strategy = PersonalDocumentationDiscoveryStrategy()
    
    # Determine the root directory for discovery based on work item filtering
    if work_item_filter:
        # For specific work item, use the work item directory as root
        discovery_root = os.path.join(work_items_directory, work_item_filter)
        if not Path(discovery_root).exists():
            print(f"❌ Work item directory not found: {discovery_root}")
            return
        print(f"🎯 Discovery root: {discovery_root} (specific work item)")
    else:
        # For all work items, use the personal documentation root
        discovery_root = work_items_directory
        print(f"📁 Discovery root: {discovery_root} (all work items)")
    
    # Run discovery phase directly on the determined root
    print(f"\n📁 Document Discovery Preview:")
    discovery_phase = DocumentDiscoveryPhase(discovery_strategy)
    discovery_result = discovery_phase.discover_documents(discovery_root)
    
    discovery_phase.print_discovery_summary(discovery_result)
    
    # Show tracking information
    if discovery_result.discovered_files:
        print(f"\n📋 Document Tracking Analysis:")
        
        unprocessed_files = []
        already_processed = 0
        
        for file_path in discovery_result.discovered_files:
            if tracker.is_processed(file_path):
                already_processed += 1
            else:
                unprocessed_files.append(file_path)
        
        print(f"   Total discovered: {len(discovery_result.discovered_files)}")
        print(f"   Already processed: {already_processed}")
        print(f"   Need processing: {len(unprocessed_files)}")
        
        # Show force reprocess information
        if force:
            print(f"\n🧹 Force Reprocess Mode Enabled:")
            print(f"   📋 Files to remove from tracker: {already_processed}")
            print(f"   �️  Files to delete from search index: {len(discovery_result.discovered_files)} (all chunks)")
            print(f"   🔄 Total files to reprocess: {len(discovery_result.discovered_files)}")
            
            if already_processed > 0:
                print(f"\n   ⚠️  Files currently marked as processed (will be cleared):")
                for file_path in discovery_result.discovered_files:
                    if tracker.is_processed(file_path):
                        relative_path = file_path.relative_to(work_items_dir)
                        print(f"      - {relative_path}")
        
        # Show files that would be processed  
        files_to_show = discovery_result.discovered_files if force else unprocessed_files
        if files_to_show:
            action_text = "reprocessed" if force else "processed"
            print(f"\n📄 Files that would be {action_text}:")
            for i, file_path in enumerate(files_to_show, 1):
                relative_path = file_path.relative_to(work_items_dir)
                print(f"   {i:2d}. {relative_path}")
        
        if not force and already_processed > 0:
            print(f"\n⏭️  Files that would be skipped (already processed):")
            skipped_count = 0
            for file_path in discovery_result.discovered_files:
                if tracker.is_processed(file_path):
                    skipped_count += 1
                    if skipped_count <= 10:  # Show first 10 skipped files
                        relative_path = file_path.relative_to(work_items_dir)
                        print(f"   {skipped_count:2d}. {relative_path}")
            
            if already_processed > 10:
                print(f"       ... and {already_processed - 10} more files")
    
    if discovery_result.discovered_files:
        if force:
            file_count = len(discovery_result.discovered_files)
            print(f"\n💡 Use --dry-run=false --force to force reprocess all {file_count} files")
            print(f"💡 This will clear tracker and delete search index documents first")
        else:
            unprocessed_count = len([f for f in discovery_result.discovered_files if not tracker.is_processed(f)])
            print(f"\n💡 Use --dry-run=false to actually process these {unprocessed_count} unprocessed files")
            if already_processed > 0:
                print(f"💡 Use --force to reprocess all {len(discovery_result.discovered_files)} files (including {already_processed} already processed)")
    else:
        print(f"\n💡 No files found to process")


async def upload_work_items(work_item_id: Optional[str] = None, 
                           reset_tracker: bool = False,
                           dry_run: bool = False,
                           force: bool = False):
    """
    Upload work item documents using the new strategy-based pipeline.
    
    Args:
        work_item_id: If provided, upload only this specific work item
        reset_tracker: If True, reset processing tracker and delete all documents  
        dry_run: If True, show preview without uploading
        force: If True, force reprocessing of already processed files
    """
    
    # Configuration from environment
    work_items_directory = os.getenv('PERSONAL_DOCUMENTATION_ROOT_DIRECTORY', 
                                    r"C:\Users\aayushalok\Desktop\Work Items")
    search_service_name = os.getenv('AZURE_SEARCH_SERVICE')
    search_admin_key = os.getenv('AZURE_SEARCH_KEY')
    search_index_name = os.getenv('AZURE_SEARCH_INDEX', 'work-items-index')
    
    print("🚀 Work Item Documentation Upload")
    print("=" * 60)
    print(f"📁 Work Items Directory: {work_items_directory}")
    print(f"🔍 Target Work Item: {work_item_id or 'All Work Items'}")
    print(f"🔄 Mode: {'Dry Run' if dry_run else 'Upload'}")
    
    # Validate directory exists
    if not Path(work_items_directory).exists():
        print(f"❌ Work items directory not found: {work_items_directory}")
        return
    
    # Show available work items
    work_items = get_work_items_from_path(work_items_directory)
    print(f"\n📋 Available Work Items ({len(work_items)}):")
    for wi in work_items[:10]:  # Show first 10
        print(f"   • {wi}")
    if len(work_items) > 10:
        print(f"   ... and {len(work_items) - 10} more work items")
    
    # Validate specific work item if provided
    if work_item_id and work_item_id not in work_items:
        print(f"❌ Work item '{work_item_id}' not found")
        print(f"Available work items: {', '.join(work_items[:5])}...")
        return
    
    # Handle dry run
    if dry_run:
        show_upload_preview(work_items_directory, work_item_id, force)
        return
    
    # Handle reset tracker
    if reset_tracker:
        tracker = DocumentProcessingTracker("processed_files.json")
        print(f"\n🔄 Resetting processing tracker...")
        
        # Delete all documents from Azure Cognitive Search index
        print(f"🗑️  Deleting all documents from Azure Cognitive Search index...")
        try:
            search_service = get_azure_search_service(search_service_name, search_admin_key, search_index_name)
            deleted_count = search_service.delete_all_documents()
            print(f"   ✅ Deleted {deleted_count} documents from search index")
        except Exception as e:
            print(f"   ❌ Failed to delete documents from search index: {e}")
            print(f"   ⚠️  Continuing with file tracker reset only...")
        
        # Clear the tracker after deletion
        tracker.reset()
        tracker.save()
        
        print(f"\n✅ Reset completed:")
        print(f"   • Processing tracker cleared")
        print(f"   • All files will be reprocessed on next upload")
        return
    
    # Create strategy-based pipeline
    print(f"\n🏗️  Initializing Strategy-Based Pipeline...")
    
    # Initialize document tracker
    tracker = DocumentProcessingTracker("processed_files.json")
    print(f"📋 Document tracker initialized: {tracker.get_tracking_source()}")
    
    # Create discovery strategy (no work item filter needed - handled by path selection)
    discovery_strategy = PersonalDocumentationDiscoveryStrategy()
    
    # Create processing strategy
    processing_strategy = PersonalDocumentationAssistantProcessingStrategy()
    
    # Create complete pipeline with tracker
    pipeline = DocumentProcessingPipeline(
        discovery_strategy=discovery_strategy,
        processing_strategy=processing_strategy,
        tracker=tracker,
        force_reprocess=force
    )
    
    # Determine the root directory for discovery based on work item filtering
    if work_item_id:
        # For specific work item, use the work item directory as root
        discovery_root = os.path.join(work_items_directory, work_item_id)
        if not Path(discovery_root).exists():
            print(f"❌ Work item directory not found: {discovery_root}")
            return
        print(f"🎯 Discovery root: {discovery_root} (specific work item)")
    else:
        # For all work items, use the personal documentation root
        discovery_root = work_items_directory
        print(f"📁 Discovery root: {discovery_root} (all work items)")
    
    print(f"   ✅ Pipeline initialized with:")
    print(f"      • Discovery: {discovery_strategy.get_strategy_name()}")
    print(f"      • Processing: {processing_strategy.get_strategy_name()}")
    print(f"      • Target Directory: {discovery_root}")
    
    # Run the complete 3-phase pipeline
    try:
        print(f"\n🚀 Running Complete 3-Phase Pipeline...")
        
        # Run complete pipeline for the determined discovery root
        discovery_result, processing_result, upload_result = pipeline.run_complete_pipeline(
            root_directory=discovery_root,
            service_name=search_service_name,
            admin_key=search_admin_key,
            index_name=search_index_name
        )
        
        # Show final summary
        print(f"\n🎉 Complete Pipeline Summary!")
        print(f"    Files discovered: {discovery_result.total_files}")
        print(f"   ⚙️  Documents processed: {processing_result.successfully_processed}")
        print(f"   📤 Search objects uploaded: {upload_result.successfully_uploaded}")
        
        if upload_result.errors:
            print(f"   ⚠️  Errors encountered: {len(upload_result.errors)}")
            for error in upload_result.errors[:3]:
                print(f"      • {error}")
        
        success_rate = (upload_result.successfully_uploaded / discovery_result.total_files * 100) if discovery_result.total_files > 0 else 0
        print(f"   ✅ Overall success rate: {success_rate:.1f}%")
        
    except Exception as e:
        print(f"❌ Pipeline execution failed: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main entry point with command line argument parsing"""
    parser = argparse.ArgumentParser(
        description="Upload work item documentation to Azure Cognitive Search using strategy-based pipeline",
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
        help='Force reprocessing of files (clears tracker and search index for discovered files)'
    )
    
    args = parser.parse_args()
    
    # Run the upload
    try:
        asyncio.run(upload_work_items(
            work_item_id=args.work_item,
            reset_tracker=args.reset,
            dry_run=args.dry_run,
            force=args.force
        ))
    except KeyboardInterrupt:
        print(f"\n⚠️  Upload cancelled by user")
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
