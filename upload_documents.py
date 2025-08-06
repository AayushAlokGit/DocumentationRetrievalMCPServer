#!/usr/bin/env python3
"""
Document Upload Entry Point
===========================

Entry point for uploading work item documentation to Azure Cognitive Search.
"""

import sys
from pathlib import Path

# Add module paths
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "common"))
sys.path.insert(0, str(project_root / "upload"))

def main():
    """Main entry point for document upload operations"""
    import argparse
    from document_upload import DocumentUploader
    
    parser = argparse.ArgumentParser(description="Upload work item documentation to Azure Cognitive Search")
    parser.add_argument("path", help="Path to work items directory")
    parser.add_argument("--create-index", action="store_true", help="Create search index if it doesn't exist")
    parser.add_argument("--force", action="store_true", help="Force re-upload of all documents")
    
    args = parser.parse_args()
    
    uploader = DocumentUploader()
    
    if args.create_index:
        print("Creating search index...")
        uploader.create_index()
    
    print(f"Uploading documents from: {args.path}")
    uploader.upload_work_items_directory(args.path, force_reupload=args.force)

if __name__ == "__main__":
    main()
