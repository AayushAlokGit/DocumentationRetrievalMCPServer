"""
ChromaDB Context-Based Document Deletion Script
==============================================

Simple script for deletion of documents from ChromaDB vector database
based on exact context name and filename matching.

Features:
- Exact context and filename matching
- Preview system to see what will be deleted
- Dry-run capability for testing
- Document tracker integration
- Safety confirmations

Usage Examples:
    # Preview what would be deleted
    python delete_by_context_and_filename.py "WORK-123" "readme.md" --preview
    
    # Dry run (test without deletion)
    python delete_by_context_and_filename.py "WORK-123" "readme.md" --dry-run
    
    # Actual deletion
    python delete_by_context_and_filename.py "WORK-123" "readme.md"

Author: Personal Documentation Assistant System - ChromaDB Version
Version: 1.0.0
"""

import os
import sys
import argparse
import time
import logging
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from dotenv import load_dotenv

# Add project root directory to path for imports
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Import project modules
from src.common.vector_search_services.chromadb_service import get_chromadb_service, ChromaDBFilterBuilder
from src.document_upload.document_processing_tracker import DocumentProcessingTracker

# Import logging utilities
sys.path.append(str(current_dir))
from logging_utils import setup_script_logging

# Load environment variables
load_dotenv()

# Global logger instance
_script_logger = None

def print_and_log(message: str, end: str = '\n'):
    """
    Helper function to print to console and optionally log to file.
    Uses the global logger instance if available.
    """
    print(message, end=end)
    if _script_logger:
        _script_logger.log(message, end=end)


async def find_matching_documents(chromadb_service, context_name: str, file_name: str, mode: str = "delete") -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Simple search for documents with exact context and filename match
    """
    print_and_log(f"🔍 Searching for documents...")
    print_and_log(f"   📝 Context: '{context_name}'")
    print_and_log(f"   📄 File: '{file_name}'")
    print_and_log(f"   🔧 Mode: '{mode}'")
    
    try:
        # Build filters for exact matching
        filters = {
            'context_name': context_name,
            'file_name': file_name
        }
        
        # Search using ChromaDB service async method
        matching_docs = await chromadb_service.get_documents_by_filter_async(filters)
        
        # Generate statistics
        files_found = {}
        for doc in matching_docs:
            file_path = doc.get('file_path', 'Unknown')
            if file_path not in files_found:
                files_found[file_path] = []
            files_found[file_path].append(doc)
        
        stats = {
            'total_matches': len(matching_docs),
            'unique_files': len(files_found),
            'chunk_count': len(matching_docs),
            'contexts_found': len(set(doc.get('context_name', '') for doc in matching_docs)),
            'matching_mode_used': mode,
            'files_breakdown': files_found
        }
        
        print_and_log(f"   ✅ Search completed: {stats['total_matches']} chunks in {stats['unique_files']} files")
        return matching_docs, stats
        
    except Exception as e:
        print_and_log(f"   ❌ Search failed: {str(e)}")
        return [], {
            'total_matches': 0, 
            'unique_files': 0, 
            'chunk_count': 0, 
            'contexts_found': 0,
            'files_breakdown': {},
            'error': str(e)
        }
    
    print_and_log(f"🔍 Searching for documents...")
    print_and_log(f"   📝 Context: '{context_name}'")
    print_and_log(f"   📄 File: '{file_name}'")
    print_and_log(f"   🎯 Mode: {matching_mode}")
    
    try:
        # Build filters based on matching mode using ChromaDBFilterBuilder
        if matching_mode == 'exact':
            filters = {
                'context_name': context_name,
                'file_name': file_name
            }
        elif matching_mode == 'contains':
            # Start with exact context, use manual filtering for filename contains
            filters = {
                'context_name': context_name
            }
        elif matching_mode == 'flexible':
            # Flexible matching: exact context + flexible filename
            # First try exact, then fallback to contains
            filters = {
                'context_name': context_name,
                'file_name': file_name  # Start with exact match
            }
        
        # Search using ChromaDB service methods
        if matching_mode == 'exact' or matching_mode == 'flexible':
            # Use get_documents_by_filter for exact matches
            results = chromadb_service.get_documents_by_filter(filters)
            matching_docs = results
        else:  # contains mode
            # Get all documents with exact context match first
            context_filter = {'context_name': context_name}
            results = chromadb_service.get_documents_by_filter(context_filter)
            
            # Filter results where file_name contains the search term
            file_name_lower = file_name.lower()
            matching_docs = [
                doc for doc in results 
                if file_name_lower in doc.get('file_name', '').lower()
            ]
        
        # If flexible mode and no exact matches, try contains matching
        if matching_mode == 'flexible' and not matching_docs:
            print_and_log("   🔄 No exact matches found, trying flexible matching...")
            
            # Get all documents with exact context match
            context_filter = {'context_name': context_name}
            all_results = chromadb_service.get_documents_by_filter(context_filter)
            
            # Filter results where file_name contains the search term
            file_name_lower = file_name.lower()
            matching_docs = [
                doc for doc in all_results 
                if file_name_lower in doc.get('file_name', '').lower()
            ]
        
        # Generate comprehensive statistics
        files_found = {}
        for doc in matching_docs:
            file_path = doc.get('file_path', 'Unknown')
            if file_path not in files_found:
                files_found[file_path] = []
            files_found[file_path].append(doc)
        
        stats = {
            'total_matches': len(matching_docs),
            'unique_files': len(files_found),
            'chunk_count': len(matching_docs),
            'contexts_found': len(set(doc.get('context_name', '') for doc in matching_docs)),
            'files_breakdown': files_found,
            'matching_mode_used': matching_mode
        }
        
        print_and_log(f"   ✅ Search completed: {stats['total_matches']} chunks in {stats['unique_files']} files")
        return matching_docs, stats
        
    except Exception as e:
        print_and_log(f"   ❌ Search failed: {str(e)}")
        return [], {
            'total_matches': 0, 
            'unique_files': 0, 
            'chunk_count': 0, 
            'contexts_found': 0,
            'files_breakdown': {},
            'matching_mode_used': matching_mode,
            'error': str(e)
        }


def preview_deletion_impact(matching_docs: List[Dict[str, Any]], search_stats: Dict[str, Any], 
                          show_details: bool = True) -> bool:
    """
    Enhanced preview system with comprehensive impact analysis and user guidance
    """
    
    if not matching_docs:
        print_and_log("\\n🔍 No matching documents found.")
        print_and_log("💡 Try using different matching mode:")
        print_and_log("   --mode exact     (exact context + filename match)")  
        print_and_log("   --mode contains  (exact context + filename contains)")
        print_and_log("   --mode flexible  (exact context + flexible filename)")
        
        if 'error' in search_stats:
            print_and_log(f"⚠️  Search error: {search_stats['error']}")
        
        return False
    
    print_and_log(f"\\n📋 DELETION IMPACT ANALYSIS")
    print_and_log("="*50)
    
    # High-level summary
    total_chunks = search_stats['total_matches'] 
    unique_files = search_stats['unique_files']
    contexts = search_stats['contexts_found']
    
    print_and_log(f"📊 Overview:")
    print_and_log(f"   🧩 Total chunks to delete: {total_chunks}")
    print_and_log(f"   📄 Unique files affected: {unique_files}")
    print_and_log(f"   🏷️  Contexts involved: {contexts}")
    print_and_log(f"   🎯 Matching mode: {search_stats['matching_mode_used']}")
    
    if show_details and 'files_breakdown' in search_stats:
        print_and_log(f"\\n📁 Files and Chunks Breakdown:")
        
        for file_path, chunks in search_stats['files_breakdown'].items():
            file_name = Path(file_path).name if file_path != 'Unknown' else 'Unknown'
            context_name = chunks[0].get('context_name', 'N/A') if chunks else 'N/A'
            
            print_and_log(f"\\n   📄 {file_name}")
            print_and_log(f"      📍 Path: {file_path}")
            print_and_log(f"      🏷️  Context: {context_name}")
            print_and_log(f"      🧩 Chunks: {len(chunks)}")
            
            # Show first few chunks with available metadata
            for i, chunk in enumerate(chunks[:3], 1):
                chunk_id = chunk.get('id', 'N/A')
                title = chunk.get('title', 'No title')[:50]
                print_and_log(f"         {i}. ID {chunk_id}: {title}...")
            
            if len(chunks) > 3:
                print_and_log(f"         ... and {len(chunks) - 3} more chunks")
    
    # Warning for large deletions
    if total_chunks > 10:
        print_and_log(f"\\n⚠️  WARNING: This will delete {total_chunks} document chunks!")
        print_and_log("   This action cannot be undone.")
        
    return True


def get_user_confirmation(matching_docs: List[Dict[str, Any]], force: bool = False) -> bool:
    """Enhanced confirmation system with safety checks"""
    
    if force:
        print_and_log("🚀 Force mode enabled - proceeding without confirmation")
        return True
    
    total_chunks = len(matching_docs)
    
    # Extra confirmation for large deletions
    if total_chunks > 20:
        print_and_log(f"\\n🛑 LARGE DELETION WARNING")
        print_and_log(f"   You are about to delete {total_chunks} document chunks!")
        print_and_log("   This is a large operation that cannot be undone.")
        
        first_confirm = input("\\n   Type 'CONFIRM' to proceed with large deletion: ").strip()
        if first_confirm != 'CONFIRM':
            print_and_log("   Operation cancelled - confirmation not received")
            return False
    
    # Standard confirmation
    confirm = input(f"\\n❓ Delete {total_chunks} document chunks? (y/N): ").lower().strip()
    
    if confirm in ['y', 'yes']:
        print_and_log("✅ Deletion confirmed")
        return True
    else:
        print_and_log("❌ Operation cancelled")
        return False


async def delete_documents_and_cleanup_tracker(chromadb_service, tracker: DocumentProcessingTracker,
                                       matching_docs: List[Dict[str, Any]], 
                                       dry_run: bool = False) -> Tuple[int, int, List[str], Dict[str, Any]]:
    """
    Enhanced atomic deletion with comprehensive error handling and performance metrics
    
    Based on ChromaDBService.delete_documents() method signature
    Uses DocumentProcessingTracker.mark_unprocessed() for cleanup (verified method)
    
    Returns:
        Tuple of (successful_deletes, failed_deletes, error_messages, operation_stats)
    """
    
    if dry_run:
        print_and_log(f"\\n🔍 DRY RUN: Would delete {len(matching_docs)} document chunks")
        unique_files = len(set(doc.get('file_path') for doc in matching_docs if doc.get('file_path')))
        return len(matching_docs), 0, [], {
            'operation': 'dry_run', 
            'duration': 0, 
            'files_would_untrack': unique_files
        }
    
    print_and_log(f"\\n🗑️  Starting deletion of {len(matching_docs)} document chunks...")
    
    start_time = time.time()
    
    successful_deletes = 0
    failed_deletes = 0
    error_messages = []
    file_paths_to_untrack = set()
    
    try:
        # Extract document IDs for batch deletion
        doc_ids = [doc.get('id') for doc in matching_docs if doc.get('id')]
        
        if not doc_ids:
            print_and_log("   ⚠️ No valid document IDs found")
            return 0, len(matching_docs), ["No valid document IDs found"], {
                'operation': 'delete',
                'duration': 0,
                'total_processed': len(matching_docs),
                'successful_deletes': 0,
                'failed_deletes': len(matching_docs),
                'success_rate': 0
            }
        
        print_and_log(f"   📋 Collected {len(doc_ids)} document IDs for deletion")
        
        # Perform batch deletion using ChromaDB service
        deleted_count = await chromadb_service.delete_documents(doc_ids)
        
        if deleted_count > 0:
            successful_deletes = deleted_count
            print_and_log(f"   ✅ Successfully deleted {deleted_count} document chunks")
            
            # Collect file paths for tracker cleanup
            for doc in matching_docs:
                file_path = doc.get('file_path')
                if file_path and file_path != 'Unknown':
                    file_paths_to_untrack.add(Path(file_path))
        else:
            failed_deletes = len(matching_docs)
            error_messages.append("Batch deletion returned 0 deletions")
            print_and_log("   ❌ Batch deletion failed or returned 0 deletions")
            
    except Exception as e:
        failed_deletes = len(matching_docs)
        error_msg = f"Batch deletion failed: {str(e)}"
        error_messages.append(error_msg)
        print_and_log(f"   ❌ Error during batch deletion: {error_msg}")
    
    # Cleanup tracker for successfully deleted files (using verified method)
    tracker_cleanup_count = 0
    if file_paths_to_untrack and successful_deletes > 0:
        print_and_log(f"\\n📋 Cleaning up document tracker for {len(file_paths_to_untrack)} files...")
        
        for file_path in file_paths_to_untrack:
            try:
                # Use actual mark_unprocessed method (verified in codebase)
                tracker.mark_unprocessed(file_path)
                tracker_cleanup_count += 1
                print_and_log(f"   🧹 Unmarked: {file_path.name}")
            except Exception as e:
                error_msg = f"Failed to untrack {file_path}: {str(e)}"
                error_messages.append(error_msg)
                print_and_log(f"   ⚠️  Warning: {error_msg}")
        
        # Save tracker state (using verified method)
        try:
            tracker.save()
            print_and_log(f"   ✅ Tracker saved with {tracker_cleanup_count} files unmarked")
        except Exception as e:
            error_msg = f"Failed to save tracker: {str(e)}"
            error_messages.append(error_msg)
            print_and_log(f"   ❌ Error saving tracker: {error_msg}")
    
    # Calculate operation statistics
    end_time = time.time()
    duration = end_time - start_time
    
    operation_stats = {
        'operation': 'delete',
        'duration': duration,
        'total_processed': len(matching_docs),
        'successful_deletes': successful_deletes,
        'failed_deletes': failed_deletes,
        'tracker_cleanups': tracker_cleanup_count,
        'success_rate': (successful_deletes / len(matching_docs)) * 100 if matching_docs else 0,
        'files_untracked': len(file_paths_to_untrack)
    }
    
    return successful_deletes, failed_deletes, error_messages, operation_stats


def print_deletion_results(successful: int, failed: int, errors: List[str], 
                         stats: Dict[str, Any], show_detailed_stats: bool):
    """Enhanced results reporting"""
    
    print_and_log(f"\\n📊 DELETION RESULTS")
    print_and_log("="*40)
    print_and_log(f"✅ Successfully deleted: {successful}")
    print_and_log(f"❌ Failed deletions: {failed}")
    print_and_log(f"⏱️  Operation time: {stats.get('duration', 0):.2f}s")
    
    if successful > 0:
        success_rate = stats.get('success_rate', 0)
        print_and_log(f"📈 Success rate: {success_rate:.1f}%")
        
        tracker_cleanups = stats.get('tracker_cleanups', 0)
        files_untracked = stats.get('files_untracked', 0)
        if tracker_cleanups > 0:
            print_and_log(f"📋 Tracker files cleaned: {tracker_cleanups}/{files_untracked}")

    # Show errors summary
    if errors:
        print_and_log(f"\\n⚠️  Errors encountered ({len(errors)}):")
        for i, error in enumerate(errors[:3], 1):  # Show first 3
            print_and_log(f"   {i}. {error}")
        if len(errors) > 3:
            print_and_log(f"   ... and {len(errors) - 3} more errors")

    if show_detailed_stats:
        print_and_log(f"\\n📈 Detailed Statistics:")
        print_and_log(f"   Total documents processed: {stats.get('total_processed', 0)}")
        print_and_log(f"   Operation type: {stats.get('operation', 'unknown')}")
        if stats.get('operation') == 'dry_run':
            print_and_log("   💡 This was a dry run - no actual changes were made")
            files_would_untrack = stats.get('files_would_untrack', 0)
            if files_would_untrack > 0:
                print_and_log(f"   📋 Would untrack {files_would_untrack} files from tracker")


async def main():
    """Enhanced CLI with comprehensive options"""
    
    parser = argparse.ArgumentParser(
        description="Delete documents by context name and filename with advanced options",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Exact matching (default)
  python delete_by_context_and_filename.py "WORK-123" "readme.md"
  
  # Flexible matching (tries exact, then contains)
  python delete_by_context_and_filename.py "WORK-123" "readme" --mode flexible
  
  # Preview what would be deleted
  python delete_by_context_and_filename.py "WORK-123" "readme.md" --preview
  
  # Force deletion without confirmation
  python delete_by_context_and_filename.py "WORK-123" "readme.md" --force
  
  # Detailed preview with chunk information
  python delete_by_context_and_filename.py "WORK-123" "readme.md" --preview --detailed
  
  # Dry run to see what would happen
  python delete_by_context_and_filename.py "WORK-123" "readme.md" --dry-run
        """)

    parser.add_argument("context_name", 
                       help="Context name to match (exact match)")
    
    parser.add_argument("file_name", 
                       help="File name to match (based on matching mode)")

    parser.add_argument("--mode", choices=['exact', 'contains', 'flexible'], 
                       default='exact',
                       help="Matching mode: exact (default), contains, or flexible")

    parser.add_argument("--preview", action="store_true",
                       help="Preview what would be deleted without deleting")

    parser.add_argument("--dry-run", action="store_true", 
                       help="Show deletion preview and simulate operation")

    parser.add_argument("--force", action="store_true",
                       help="Delete without confirmation prompt")

    parser.add_argument("--detailed", action="store_true",
                       help="Show detailed chunk information in preview")
    
    parser.add_argument("--log-file",
                       type=str,
                       help="Path to log file for capturing script output (relative to ScriptExecutionLogs/ or absolute path)")

    parser.add_argument("--stats", action="store_true",
                       help="Show comprehensive operation statistics")

    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Enable verbose logging for debugging")

    args = parser.parse_args()

    # Initialize logger
    global _script_logger
    if args.log_file:
        # User specified a log file
        _script_logger = setup_script_logging(log_file=args.log_file, script_path=__file__)
    else:
        # Auto-generate log file based on script path and IST timestamp
        _script_logger = setup_script_logging(script_path=__file__)

    # Configure logging
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    # Validate mutually exclusive options
    if args.preview and args.dry_run:
        print_and_log("💡 Note: --preview and --dry-run are similar. Using --dry-run behavior.")
        args.preview = False

    try:
        # Load environment and validate
        load_dotenv()
        
        # Validate environment variables for ChromaDB
        required_vars = ['CHROMADB_COLLECTION_NAME', 'CHROMADB_PERSIST_DIRECTORY']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            print_and_log("⚠️ Missing ChromaDB environment variables (using defaults):")
            for var in missing_vars:
                print_and_log(f"   - {var}")
            print_and_log("\\n💡 ChromaDB will use default configuration")

        # Initialize services
        print_and_log("🔧 Initializing ChromaDB services...")
        try:
            chromadb_service = get_chromadb_service()
            tracker = DocumentProcessingTracker()
            print_and_log("   ✅ Services initialized successfully")
        except Exception as e:
            print_and_log(f"   ❌ Failed to initialize services: {str(e)}")
            print_and_log("   💡 Check your ChromaDB configuration and connectivity")
            return 1

        # Perform search
        matching_docs, search_stats = await find_matching_documents(
            chromadb_service, args.context_name, args.file_name, args.mode
        )

        # Show preview
        preview_success = preview_deletion_impact(
            matching_docs, search_stats, show_details=args.detailed
        )

        if not preview_success:
            return 0  # No matches found

        # Handle preview-only mode
        if args.preview:
            print_and_log("\\n💡 Preview complete. Use without --preview to perform deletion.")
            return 0

        # Get confirmation (unless dry run)
        if not args.dry_run:
            if not get_user_confirmation(matching_docs, args.force):
                return 0

        # Perform deletion
        successful, failed, errors, operation_stats = await delete_documents_and_cleanup_tracker(
            chromadb_service, tracker, matching_docs, dry_run=args.dry_run
        )

        # Show results
        print_deletion_results(successful, failed, errors, operation_stats, args.stats)

        # Return appropriate exit code
        return 0 if failed == 0 else 1

    except KeyboardInterrupt:
        print_and_log("\\n⏹️  Operation interrupted by user")
        return 1
    except Exception as e:
        print_and_log(f"❌ Unexpected error: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
