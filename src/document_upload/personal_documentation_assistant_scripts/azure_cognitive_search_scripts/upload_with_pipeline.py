#!/usr/bin/env python3
"""
Script 2: Full Pipeline Upload Script

This script provides complete DocumentProcessingPipeline functionality with:
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
Created: Based on comprehensive implementation plan and Script 1 learnings
"""

import os
import sys
import argparse
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dotenv import load_dotenv

# Add src to path for imports - navigate up to src directory
current_dir = Path(__file__).parent
src_dir = current_dir.parent.parent
sys.path.insert(0, str(src_dir))

# Import project modules
from src.common.vector_search_services.azure_cognitive_search import get_azure_search_service
from document_upload.file_tracker import DocumentProcessingTracker
from document_upload.document_processing_pipeline import DocumentProcessingPipeline
from document_upload.processing_strategies import PersonalDocumentationAssistantAzureCognitiveSearchProcessingStrategy
from document_upload.discovery_strategies import GeneralDocumentDiscoveryStrategy

# Load environment variables
load_dotenv()


async def force_reset_index_and_tracker() -> bool:
    """Complete index reset and tracker cleanup with comprehensive validation"""
    print("🗑️  Performing complete force reset...")
    
    # Load environment and initialize services (using existing patterns)
    load_dotenv()
    
    try:
        # Initialize Azure Search service using existing factory function
        azure_search = get_azure_search_service()
        tracker = DocumentProcessingTracker()
        
        # 1. Delete all documents from index using existing method
        print("   🔄 Deleting all documents from search index...")
        deleted_count = azure_search.delete_all_documents()
        print(f"   ✅ Successfully deleted {deleted_count} documents from index")
        
        # 2. Clear tracker state completely using existing method
        print("   🔄 Clearing document processing tracker...")
        tracker.clear()  # Complete cleanup (clears data and deletes file)
        tracker.save()
        print(f"   ✅ Document tracker cleared and saved")
        
        # 3. Verification step using existing method
        remaining_docs = azure_search.get_document_count()
        if remaining_docs == 0:
            print("   ✅ Force reset completed successfully")
            return True
        else:
            print(f"   ⚠️  Warning: {remaining_docs} documents still remain in index")
            return False
            
    except Exception as e:
        print(f"   ❌ Error during force reset: {str(e)}")
        print("   💡 Try running the script again or check Azure Search connectivity")
        return False


def create_configured_pipeline() -> DocumentProcessingPipeline:
    """Create fully configured pipeline with proper strategy integration"""
    
    # Use GeneralDocumentDiscoveryStrategy for unified file/directory handling
    # (eliminates need for manual path type checking like in Script 1)
    discovery_strategy = GeneralDocumentDiscoveryStrategy()

    # Use PersonalDocumentationAssistantAzureCognitiveSearchProcessingStrategy for auto metadata generation
    processing_strategy = PersonalDocumentationAssistantAzureCognitiveSearchProcessingStrategy()

    # Initialize tracker for idempotent operations
    tracker = DocumentProcessingTracker()

    # Create pipeline with standard configuration
    pipeline = DocumentProcessingPipeline(
        discovery_strategy=discovery_strategy,
        processing_strategy=processing_strategy,
        tracker=tracker
    )
    
    return pipeline


async def process_path_with_pipeline(target_path: str, dry_run: bool = False) -> bool:
    """Process path using complete pipeline with comprehensive error handling"""
    
    # Validate path exists
    target_path_obj = Path(target_path)
    if not target_path_obj.exists():
        print(f"❌ Error: Path does not exist: {target_path}")
        return False
    
    # Load environment and validate (using existing pattern from create_index.py)
    load_dotenv()
    
    # Validate environment variables (using existing pattern)
    required_vars = ['AZURE_SEARCH_SERVICE', 'AZURE_SEARCH_KEY', 'AZURE_OPENAI_ENDPOINT', 'AZURE_OPENAI_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\n💡 Please ensure your .env file contains all required variables:")
        print("   AZURE_SEARCH_SERVICE, AZURE_SEARCH_KEY, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_KEY")
        return False

    # Create configured pipeline
    pipeline = create_configured_pipeline()

    try:
        # Get Azure credentials from environment (matching existing patterns)
        service_name = os.getenv('AZURE_SEARCH_SERVICE')
        admin_key = os.getenv('AZURE_SEARCH_KEY')
        index_name = os.getenv('AZURE_SEARCH_INDEX', 'work-items-index')  # Default value like existing scripts
        
        print(f"🚀 Starting full pipeline processing...")
        print(f"   📍 Target path: {target_path}")
        print(f"   ️  Dry run: {dry_run}")
        print(f"   🔍 Search service: {service_name}")
        print(f"   📋 Index: {index_name}")
        
        if dry_run:
            # Show discovery preview without processing
            print(f"\n🔍 DRY RUN: Discovery Preview")
            discovery_result = pipeline.discovery_phase.discover_documents(str(target_path_obj))
            pipeline.discovery_phase.print_discovery_summary(discovery_result)
            
            # Show what would be processed using existing method
            if discovery_result.discovered_files:
                unprocessed_files, total_discovered, already_processed = pipeline.filter_unprocessed_files(
                    discovery_result.discovered_files
                )
                
                print(f"\n📊 Processing Preview:")
                print(f"   📁 Total files found: {total_discovered}")
                print(f"   ⏭️  Already processed: {already_processed}")
                print(f"   🔄 Would process: {len(unprocessed_files)}")
                
                if unprocessed_files:
                    print(f"\n📄 Files that would be processed:")
                    for i, file_path in enumerate(unprocessed_files[:10], 1):  # Show first 10 files
                        print(f"   {i}. {file_path.name}")
                    if len(unprocessed_files) > 10:
                        print(f"   ... and {len(unprocessed_files) - 10} more files")
                
                print(f"\n💡 Run without --dry-run to perform actual processing")
            else:
                print(f"\n📂 No files found to process in: {target_path}")
            
            return True
        
        # Execute complete pipeline using existing method signature
        print(f"\n🚀 Executing complete pipeline...")
        discovery_result, processing_result, upload_result = await pipeline.run_complete_pipeline(
            root_directory=str(target_path_obj),
            service_name=service_name,
            admin_key=admin_key,
            index_name=index_name
        )
        
        # Show comprehensive results
        print_pipeline_statistics(discovery_result, processing_result, upload_result)
        
        # Return success if any documents were processed or if no files needed processing
        success = (upload_result.successfully_uploaded > 0 or 
                  processing_result.successfully_processed == 0)
        
        if success:
            print(f"\n✅ Pipeline execution completed successfully")
        else:
            print(f"\n⚠️  Pipeline execution completed with issues")
            
        return success
        
    except Exception as e:
        print(f"❌ Pipeline execution failed: {str(e)}")
        print("💡 Check your environment configuration and Azure connectivity")
        import traceback
        print(f"🔍 Debug info: {traceback.format_exc()}")
        return False


def print_pipeline_statistics(discovery_result, processing_result, upload_result):
    """Enhanced statistics reporting based on Script 1 patterns"""
    print("\n" + "="*60)
    print("📊 PIPELINE EXECUTION STATISTICS")
    print("="*60)
    
    # Discovery Phase Stats
    print(f"\n📁 Discovery Phase:")
    print(f"   Total files discovered: {discovery_result.total_files}")
    if hasattr(discovery_result, 'files_by_type') and discovery_result.files_by_type:
        print(f"   Files by type: {discovery_result.files_by_type}")
    if hasattr(discovery_result, 'skipped_files'):
        print(f"   Files skipped: {len(discovery_result.skipped_files)}")
    
    # Processing Phase Stats  
    print(f"\n⚙️  Processing Phase:")
    print(f"   Successfully processed: {processing_result.successfully_processed}")
    print(f"   Failed processing: {processing_result.failed_documents}")
    print(f"   Processing time: {processing_result.processing_time:.2f}s")
    if hasattr(processing_result, 'strategy_name'):
        print(f"   Strategy used: {processing_result.strategy_name}")
    
    # Upload Phase Stats
    print(f"\n📤 Upload Phase:")
    print(f"   Search objects uploaded: {upload_result.successfully_uploaded}")
    print(f"   Failed uploads: {upload_result.failed_uploads}")
    print(f"   Upload time: {upload_result.upload_time:.2f}s")
    
    # Overall Pipeline Stats
    discovery_time = getattr(discovery_result, 'discovery_time', 0)
    total_time = discovery_time + processing_result.processing_time + upload_result.upload_time
    print(f"\n🎯 Overall Results:")
    print(f"   Total execution time: {total_time:.2f}s")
    
    if discovery_result.total_files > 0:
        # Calculate success rate based on total discovered files
        success_rate = (upload_result.successfully_uploaded / discovery_result.total_files) * 100
        print(f"   Overall success rate: {success_rate:.1f}%")
        
        # Processing efficiency
        if processing_result.successfully_processed > 0:
            upload_efficiency = (upload_result.successfully_uploaded / processing_result.successfully_processed) * 100
            print(f"   Upload efficiency: {upload_efficiency:.1f}%")
    
    # Error Summary
    all_errors = []
    if hasattr(discovery_result, 'errors') and discovery_result.errors:
        all_errors.extend(discovery_result.errors)
    if hasattr(processing_result, 'errors') and processing_result.errors:
        all_errors.extend(processing_result.errors)
    if hasattr(upload_result, 'errors') and upload_result.errors:
        all_errors.extend(upload_result.errors)
    
    if all_errors:
        print(f"\n⚠️  Errors encountered: {len(all_errors)}")
        for i, error in enumerate(all_errors[:5], 1):  # Show first 5 errors
            print(f"   {i}. {error}")
        if len(all_errors) > 5:
            print(f"   ... and {len(all_errors) - 5} more errors")
    else:
        print(f"\n✅ No errors encountered during processing")
        
    # Performance insights
    if discovery_result.total_files > 0:
        avg_processing_time = processing_result.processing_time / max(processing_result.successfully_processed, 1)
        print(f"\n📈 Performance Metrics:")
        print(f"   Average processing time per file: {avg_processing_time:.2f}s")
        
        if upload_result.successfully_uploaded > 0:
            avg_upload_time = upload_result.upload_time / upload_result.successfully_uploaded
            print(f"   Average upload time per object: {avg_upload_time:.2f}s")


def main() -> int:
    """Enhanced CLI with comprehensive options and validation"""
    parser = argparse.ArgumentParser(
        description="Upload documents using full DocumentProcessingPipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process single file
  python upload_with_pipeline.py "C:/docs/readme.md"
  
  # Process entire directory
  python upload_with_pipeline.py "C:/Work Items"
  
  # Complete reset: delete all + reprocess all
  python upload_with_pipeline.py "C:/docs" --force-reset
  
  # Preview what would be processed
  python upload_with_pipeline.py "C:/docs" --dry-run
  
  # Verbose output for debugging
  python upload_with_pipeline.py "C:/docs" --verbose

Advanced Usage:
  # Full system reset with preview
  python upload_with_pipeline.py "C:/Work Items" --force-reset --dry-run
  
  # Process with detailed statistics
  python upload_with_pipeline.py "C:/docs" --stats --verbose
        """)
    
    parser.add_argument("path", 
                       help="Root directory or file path to process")
    
    parser.add_argument("--force-reset", action="store_true",
                       help="Delete all documents from index and tracker, then reprocess all")
                       
    parser.add_argument("--dry-run", action="store_true",
                       help="Show what would be processed without making changes")
                       
    parser.add_argument("--stats", action="store_true",
                       help="Show detailed processing statistics after completion")
                       
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Enable verbose logging for debugging")

    args = parser.parse_args()

    # Configure logging
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        print("🔍 Verbose logging enabled")
    
    # Validate path
    if not Path(args.path).exists():
        print(f"❌ Error: Path does not exist: {args.path}")
        return 1
    
    print("🚀 Full Pipeline Upload Script - Script 2")
    print("="*50)
    print(f"📍 Target path: {args.path}")
    print(f"🔄 Force reset: {args.force_reset}")
    print(f"️  Dry run: {args.dry_run}")
    print(f"📊 Show stats: {args.stats}")
    print(f"🔍 Verbose: {args.verbose}")

    async def async_main() -> int:
        try:
            success = False
            
            if args.force_reset:
                # Handle complete reset
                print("\n⚠️  WARNING: This will delete ALL documents and tracker data!")
                print("   - All documents will be removed from the search index")
                print("   - Document processing tracker will be cleared")
                print("   - This operation cannot be undone")
                
                if not args.dry_run:
                    confirm = input("\nContinue with force reset? (y/N): ").lower().strip()
                    if confirm != 'y':
                        print("Operation cancelled.")
                        return 0
                else:
                    print("\n🔍 DRY RUN: Would perform complete force reset")
                
                # Perform reset (unless dry run)
                if not args.dry_run:
                    reset_success = await force_reset_index_and_tracker()
                    if not reset_success:
                        print("❌ Force reset failed")
                        return 1
                    print("✅ Force reset completed successfully")
                else:
                    print("🔍 DRY RUN: Would delete all documents and tracker data")
                
                # Process with force reprocess after reset
                success = await process_path_with_pipeline(
                    args.path, 
                    dry_run=args.dry_run
                )
                
            else:
                # Regular processing
                success = await process_path_with_pipeline(
                    args.path,
                    dry_run=args.dry_run
                )
            
            if success:
                if not args.dry_run:
                    print("\n✅ Pipeline processing completed successfully")
                else:
                    print("\n✅ Dry run completed successfully")
                return 0
            else:
                if not args.dry_run:
                    print("\n❌ Pipeline processing failed")
                else:
                    print("\n❌ Dry run failed")
                return 1
                
        except KeyboardInterrupt:
            print("\n⏹️  Processing interrupted by user")
            return 1
        except Exception as e:
            print(f"\n❌ Unexpected error: {str(e)}")
            if args.verbose:
                import traceback
                print("\n🔍 Full traceback:")
                traceback.print_exc()
            return 1

    # Run async main function
    return asyncio.run(async_main())


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
