#!/usr/bin/env python3
"""
ChromaDB Full Pipeline Upload Script
===================================

This script provides complete DocumentProcessingPipeline functionality with ChromaDB:
- Full 3-phase pipeline execution (Discovery → Processing → Upload)
- Force reset capability (delete all documents + tracker cleanup)
- Dry-run preview mode
- Comprehensive error handling and progress tracking
- Statistics reporting with detailed metrics
- Resume capability using DocumentProcessingTracker

Usage Examples:
    # Process single file
    python upload_with_pipeline.py "C:/docs/readme.md"
    
    # Process entire directory
    python upload_with_pipeline.py "C:/Work Items"
    
    # Complete reset: delete all + reprocess all
    python upload_with_pipeline.py "C:/docs" --force-reset
    
    # Preview what would be processed
    python upload_with_pipeline.py "C:/docs" --dry-run

Author: Personal Documentation Assistant System
Created: ChromaDB migration of Azure Cognitive Search pipeline script
"""

import os
import sys
import argparse
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path for imports - navigate up to project root
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Import project modules
from src.common.vector_search_services.chromadb_service import get_chromadb_service
from src.document_upload.upload_strategies import ChromaDBDocumentUploadStrategy
from src.document_upload.document_processing_tracker import DocumentProcessingTracker
from src.document_upload.document_processing_pipeline import DocumentProcessingPipeline
from src.document_upload.processing_strategies import PersonalDocumentationAssistantChromaDBProcessingStrategy

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


async def force_reset_chromadb_and_tracker() -> bool:
    """Complete ChromaDB reset and tracker cleanup with comprehensive validation"""
    print_and_log("🗑️  Performing complete force reset...")
    
    try:
        # Initialize ChromaDB service and tracker
        chromadb_service = get_chromadb_service()
        tracker = DocumentProcessingTracker()
        processing_strategy = PersonalDocumentationAssistantChromaDBProcessingStrategy()
        upload_strategy = ChromaDBDocumentUploadStrategy(processing_strategy=processing_strategy)
        
        # 1. Delete all documents from ChromaDB
        print_and_log("   🔄 Deleting all documents from ChromaDB...")
        deleted_count = await upload_strategy.delete_all_documents_from_service()
        
        if deleted_count >= 0:
            print_and_log(f"   ✅ Successfully deleted {deleted_count} documents from ChromaDB")
        else:
            print_and_log("   ⚠️ Document deletion may have failed")
        
        # 2. Clear tracker state completely
        print_and_log("   🔄 Clearing document processing tracker...")
        tracker.clear()
        print_and_log("   ✅ Document tracker cleared")
        
        # 3. Test connection to verify ChromaDB is accessible
        try:
            await chromadb_service.test_connection()
            print_and_log("   ✅ ChromaDB connection verified")
        except Exception as e:
            print_and_log(f"   ⚠️ ChromaDB connection test failed: {e}")
        
        print_and_log("   ✅ Force reset completed successfully")
        return True
        
    except Exception as e:
        print_and_log(f"   ❌ Error during force reset: {str(e)}")
        print_and_log("   💡 Try running the script again or check ChromaDB connectivity")
        return False


def create_configured_pipeline() -> DocumentProcessingPipeline:
    """Create fully configured pipeline with ChromaDB strategies"""
    from document_upload.discovery_strategies import GeneralDocumentDiscoveryStrategy
    
    # Initialize strategies
    discovery_strategy = GeneralDocumentDiscoveryStrategy()
    processing_strategy = PersonalDocumentationAssistantChromaDBProcessingStrategy()
    upload_strategy = ChromaDBDocumentUploadStrategy(processing_strategy=processing_strategy)
    tracker = DocumentProcessingTracker()

    # Create pipeline with ChromaDB configuration
    pipeline = DocumentProcessingPipeline(
        discovery_strategy=discovery_strategy,
        processing_strategy=processing_strategy,
        upload_strategy=upload_strategy,
        tracker=tracker
    )
    
    return pipeline


async def process_path_with_chromadb_pipeline(target_path: str, dry_run: bool = False) -> bool:
    """Process path using complete ChromaDB pipeline with comprehensive error handling"""
    
    # Validate path exists
    target_path_obj = Path(target_path)
    if not target_path_obj.exists():
        print_and_log(f"❌ Error: Path does not exist: {target_path}")
        return False
    
    # Load environment
    load_dotenv()
    
    # Create configured pipeline
    pipeline = create_configured_pipeline()

    try:
        print_and_log(f"🚀 Starting ChromaDB pipeline processing...")
        print_and_log(f"   📍 Target path: {target_path}")
        print_and_log(f"   🔍 Dry run: {dry_run}")
        print_and_log(f"   📊 Vector service: ChromaDB (local)")
        print_and_log(f"   🤖 Embedding service: Local (sentence-transformers)")
        
        if dry_run:
            # Show discovery preview without processing
            print_and_log(f"\n🔍 DRY RUN: Discovery Preview")
            discovery_result = pipeline.discovery_phase.discover_documents(str(target_path_obj))
            pipeline.discovery_phase.print_discovery_summary(discovery_result)
            
            # Show what would be processed
            if discovery_result.discovered_files:
                unprocessed_files, total_discovered, already_processed = pipeline.filter_unprocessed_files(
                    discovery_result.discovered_files
                )
                
                print_and_log(f"\n📊 Processing Preview:")
                print_and_log(f"   📁 Total files found: {total_discovered}")
                print_and_log(f"   ⏭️  Already processed: {already_processed}")
                print_and_log(f"   🔄 Would process: {len(unprocessed_files)}")
                
                if unprocessed_files:
                    print_and_log(f"\n📄 Files that would be processed:")
                    for i, file_path in enumerate(unprocessed_files[:10], 1):  # Show first 10 files
                        print_and_log(f"   {i}. {file_path.name}")
                    if len(unprocessed_files) > 10:
                        print_and_log(f"   ... and {len(unprocessed_files) - 10} more files")
                
                print_and_log(f"\n💡 Run without --dry-run to perform actual processing")
            else:
                print_and_log(f"\n💡 No files found to process in: {target_path}")
            
            return True
        
        # Execute complete pipeline
        print_and_log(f"\n🚀 Executing complete ChromaDB pipeline...")
        discovery_result, processing_result, upload_result = await pipeline.run_complete_pipeline(
            root_directory=str(target_path_obj)
        )
        
        # Show comprehensive results
        print_chromadb_pipeline_statistics(discovery_result, processing_result, upload_result)
        
        # Return success if any documents were processed or if no files needed processing
        success = (upload_result.successfully_uploaded > 0 or 
                  processing_result.successfully_processed == 0)
        
        if success:
            print_and_log(f"\n✅ ChromaDB pipeline execution completed successfully")
        else:
            print_and_log(f"\n⚠️  ChromaDB pipeline execution completed with issues")
            
        return success
        
    except Exception as e:
        print_and_log(f"❌ ChromaDB pipeline execution failed: {str(e)}")
        print_and_log("💡 Check ChromaDB service connectivity and configuration")
        return False


def print_chromadb_pipeline_statistics(discovery_result, processing_result, upload_result):
    """Enhanced statistics reporting for ChromaDB pipeline"""
    print_and_log("\n" + "="*60)
    print_and_log("📊 CHROMADB PIPELINE EXECUTION STATISTICS")
    print_and_log("="*60)
    
    # Discovery Phase Stats
    print_and_log(f"\n📁 Discovery Phase:")
    print_and_log(f"   Total files discovered: {discovery_result.total_files}")
    if hasattr(discovery_result, 'files_by_type') and discovery_result.files_by_type:
        print_and_log(f"   Files by type: {discovery_result.files_by_type}")
    if hasattr(discovery_result, 'skipped_files'):
        print_and_log(f"   Files skipped: {len(discovery_result.skipped_files)}")
    
    # Processing Phase Stats  
    print_and_log(f"\n⚙️  Processing Phase:")
    print_and_log(f"   Successfully processed: {processing_result.successfully_processed}")
    print_and_log(f"   Failed processing: {processing_result.failed_documents}")
    print_and_log(f"   Processing time: {processing_result.processing_time:.2f}s")
    print_and_log(f"   Strategy used: {processing_result.strategy_name}")
    
    # Strategy-specific metadata
    if hasattr(processing_result, 'strategy_metadata') and processing_result.strategy_metadata:
        metadata = processing_result.strategy_metadata
        work_items_count = metadata.get('work_items_count', 0)
        if work_items_count > 0:
            print_and_log(f"   Work items found: {work_items_count}")
            work_items = metadata.get('work_items_found', [])
            if work_items:
                print_and_log(f"   Work items: {', '.join(work_items[:5])}")
                if len(work_items) > 5:
                    print_and_log(f"   (and {len(work_items) - 5} more)")
    
    # Upload Phase Stats
    print_and_log(f"\n📤 Upload Phase:")
    print_and_log(f"   Search objects uploaded: {upload_result.successfully_uploaded}")
    print_and_log(f"   Failed uploads: {upload_result.failed_uploads}")
    print_and_log(f"   Upload time: {upload_result.upload_time:.2f}s")
    
    # Overall Pipeline Stats
    discovery_time = getattr(discovery_result, 'discovery_time', 0)
    total_time = discovery_time + processing_result.processing_time + upload_result.upload_time
    print_and_log(f"\n📈 Overall Pipeline:")
    print_and_log(f"   Total execution time: {total_time:.2f}s")
    print_and_log(f"   Vector service: ChromaDB (local)")
    print_and_log(f"   Embedding service: Local sentence-transformers")
    
    # Error Summary
    all_errors = []
    if hasattr(discovery_result, 'errors'):
        all_errors.extend(discovery_result.errors)
    if hasattr(processing_result, 'errors'):
        all_errors.extend(processing_result.errors)  
    if hasattr(upload_result, 'errors'):
        all_errors.extend(upload_result.errors)
    
    if all_errors:
        print_and_log(f"\n⚠️  Errors encountered: {len(all_errors)}")
        # Show first few errors
        for error in all_errors[:3]:
            print_and_log(f"   • {error}")
        if len(all_errors) > 3:
            print_and_log(f"   • ... and {len(all_errors) - 3} more errors")
    
    print_and_log("="*60)


async def run_main():
    """Main async entry point."""
    parser = argparse.ArgumentParser(
        description="ChromaDB Full Pipeline Upload Script for Personal Documentation Assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "/path/to/document.md"
  %(prog)s "/path/to/work-items/" 
  %(prog)s "/path/to/docs/" --force-reset
  %(prog)s "/path/to/docs/" --dry-run
  %(prog)s "/path/to/docs/" --log-file "upload_session.log"
  %(prog)s "/path/to/docs/" --log-file "/absolute/path/to/logs/upload.log"
        """
    )
    
    parser.add_argument(
        'input_path',
        help='Path to file or directory to process'
    )
    
    parser.add_argument(
        '--force-reset',
        action='store_true',
        help='Delete all existing documents and tracker state before processing'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview what would be processed without making changes'
    )
    
    parser.add_argument(
        '--log-file',
        type=str,
        help='Path to log file for capturing script output (relative to FILE_TRACKING_DIRECTORY/logs/ or absolute path)'
    )
    
    args = parser.parse_args()
    
    # Initialize logger if log file is specified, or auto-generate if enabled
    global _script_logger
    if args.log_file:
        # User specified a log file
        _script_logger = setup_script_logging(log_file=args.log_file, script_path=__file__)
    else:
        # Auto-generate log file based on script path and IST timestamp
        _script_logger = setup_script_logging(script_path=__file__)
    
    try:
        # Validate input path
        input_path = Path(args.input_path).resolve()
        if not input_path.exists():
            print_and_log(f"❌ Input path does not exist: {input_path}")
            return 1
        
        # Handle force reset if requested
        if args.force_reset:
            if not await force_reset_chromadb_and_tracker():
                print_and_log("❌ Force reset failed")
                return 1
        
        # Process the path with ChromaDB pipeline
        success = await process_path_with_chromadb_pipeline(str(input_path), args.dry_run)
        
        # Close log file if logger was used
        if _script_logger:
            _script_logger.close_log()
        
        # Return appropriate exit code
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print_and_log("\n⚠️ Operation cancelled by user")
        if _script_logger:
            _script_logger.close_log()
        return 1
    except Exception as e:
        print_and_log(f"❌ Script execution failed: {e}")
        if _script_logger:
            _script_logger.close_log()
        return 1


def main():
    """Entry point wrapper."""
    exit_code = asyncio.run(run_main())
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
