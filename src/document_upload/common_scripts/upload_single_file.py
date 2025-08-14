#!/usr/bin/env python3
"""
Single File Upload Script
=========================

Simple script to upload a single markdown file to the Azure Cognitive Search service using 
the document processing pipeline. This ensures consistency with bulk uploads and leverages 
the full processing strategy.

Usage:
    python scripts/upload_single_file.py "path/to/your/file.md"
"""

import sys
import asyncio
import os
from pathlib import Path

# Add src to path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root / "src" / "document_upload"))

from dotenv import load_dotenv
from document_upload.document_processing_pipeline import DocumentProcessingPipeline
from document_upload.file_tracker import DocumentProcessingTracker

# Load environment variables
load_dotenv()


async def upload_single_file(file_path: str):
    """Upload a single file to Azure Cognitive Search using the full processing pipeline"""
    
    file_path = Path(file_path).resolve()
    
    if not file_path.exists():
        print(f"[ERROR] File not found: {file_path}")
        return False
    
    if not file_path.suffix.lower() in ['.md', '.txt', '.docx']:
        print(f"[ERROR] File must be a supported type (.md, .txt, .docx): {file_path}")
        return False
    
    print(f"[DOCUMENT] Uploading file: {file_path.name}")
    print(f"[FOLDER] Full path: {file_path}")
    print("-" * 50)
    
    try:
        # Initialize the file tracker (same as bulk upload)
        # Use the parent directory of the file for tracking
        tracking_file_path = "processed_files.json"
        tracker = DocumentProcessingTracker(str(tracking_file_path))
        
        # Initialize the processing pipeline
        pipeline = DocumentProcessingPipeline(tracker=tracker)
        
        print(f"📋 Using Document Processing Pipeline")
        print(f"   File to process: {file_path}")
        print(f"   Processing strategy: PersonalDocumentationAssistant")
        
        # Get Azure Search configuration
        search_service_name = os.getenv('AZURE_SEARCH_SERVICE')
        search_admin_key = os.getenv('AZURE_SEARCH_KEY')
        search_index_name = os.getenv('AZURE_SEARCH_INDEX', 'work-items-index')
        
        if not search_service_name or not search_admin_key:
            print("[ERROR] Azure Search configuration missing. Check AZURE_SEARCH_SERVICE and AZURE_SEARCH_KEY environment variables.")
            return False
        
        # Run the full pipeline using the file path as root_directory
        # The updated discovery strategy will handle single files correctly
        discovery_result, processing_result, upload_result = await pipeline.run_complete_pipeline(
            root_directory=str(file_path),  # Pass file path as root directory
            service_name=search_service_name,
            admin_key=search_admin_key,
            index_name=search_index_name
        )
        
        # Print results
        if discovery_result and discovery_result.total_files > 0:
            print(f"🎉 SUCCESS! Document processed successfully")
            print(f"   File: {file_path.name}")
            
            if processing_result:
                print(f"   Documents processed: {processing_result.successfully_processed}")
                print(f"   Total chunks: {len(processing_result.processed_documents[0].content_chunks) if processing_result.processed_documents else 0}")
                
            if upload_result:
                print(f"   Search objects uploaded: {upload_result.successfully_uploaded}")
                
            return True
        else:
            print("[ERROR] File was not processed (may not have supported extension)")
            return False
            
    except Exception as e:
        print(f"[ERROR] Error processing file: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main entry point"""
    if len(sys.argv) != 2:
        print("Usage: python scripts/upload_single_file.py \"path/to/your/file.md\"")
        print("\nExample:")
        print("  python scripts/upload_single_file.py \"C:/path/to/document.md\"")
        sys.exit(1)
    
    file_path = sys.argv[1]
    print("🧪 Single File Upload")
    print(f"File: {file_path}")
    print("=" * 50)
    
    # Run the upload
    success = asyncio.run(upload_single_file(file_path))
    
    if success:
        print("[SUCCESS] Upload completed successfully!")
        sys.exit(0)
    else:
        print("[ERROR] Upload failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
