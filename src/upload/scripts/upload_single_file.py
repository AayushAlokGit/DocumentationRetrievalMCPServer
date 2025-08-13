#!/usr/bin/env python3
"""
Single File Upload Script
=========================

Simple script to upload a single markdown file to the Azure Cognitive Search service.
Provide the file path as a command line argument.

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
sys.path.insert(0, str(project_root / "src" / "common"))
sys.path.insert(0, str(project_root / "src" / "upload"))

from dotenv import load_dotenv
from document_upload import upload_document_to_search
from document_utils import read_markdown_file, simple_chunk_text
from common.embedding_service import get_embedding_generator

# Load environment variables
load_dotenv()


async def upload_single_file(file_path: str):
    """Upload a single file to Azure Cognitive Search"""
    
    file_path = Path(file_path).resolve()
    
    if not file_path.exists():
        print(f"[ERROR] File not found: {file_path}")
        return False
    
    if not file_path.suffix.lower() == '.md':
        print(f"[ERROR] File must be a markdown file (.md): {file_path}")
        return False
    
    print(f"[DOCUMENT] Uploading file: {file_path.name}")
    print(f"[FOLDER] Full path: {file_path}")
    print("-" * 50)
    
    try:
        # Read and process the file
        file_data = read_markdown_file(file_path)
        if not file_data:
            print("[ERROR] Failed to read or parse the markdown file")
            return False
            
        content = file_data['content']
        metadata = file_data['metadata']
        chunks = simple_chunk_text(content)
        
        print(f"📖 File parsed successfully")
        print(f"   Title: {metadata.get('title', 'Unknown')}")
        print(f"   Work Item ID: {metadata.get('work_item_id', 'Unknown')}")
        print(f"   Tags: {metadata.get('tags', [])}")
        print(f"   Content length: {len(content)} characters")
        print(f"   Chunks created: {len(chunks)}")
        
        # Initialize embedding service  
        embedding_service = get_embedding_generator()
        
        if not embedding_service.test_connection():
            print("[ERROR] Failed to connect to Azure OpenAI. Please check your credentials.")
            return False
        
        # Generate embeddings
        print("🧠 Generating embeddings...")
        embeddings = []
        for chunk in chunks:
            embedding = await embedding_service.generate_embedding(chunk)
            embeddings.append(embedding)
        
        print(f"[SUCCESS] Generated {len(embeddings)} embeddings")
        
        # Create document structure
        document = {
            'file_path': str(file_path),
            'content': content,
            'metadata': metadata,
            'chunks': chunks,
            'embeddings': embeddings
        }
        
        # Get Azure Search configuration
        search_service_name = os.getenv('AZURE_SEARCH_SERVICE')
        search_admin_key = os.getenv('AZURE_SEARCH_KEY')
        search_index_name = os.getenv('AZURE_SEARCH_INDEX', 'work-items-index')
        
        if not search_service_name or not search_admin_key:
            print("[ERROR] Azure Search configuration missing. Check AZURE_SEARCH_SERVICE and AZURE_SEARCH_KEY environment variables.")
            return False
        
        # Upload to search
        print("⬆️  Uploading to Azure Cognitive Search...")
        success = upload_document_to_search(document, search_service_name, search_admin_key, search_index_name)
        
        if success:
            print("🎉 SUCCESS! Document uploaded successfully")
            print(f"   File: {file_path.name}")
            print(f"   Title: {metadata.get('title', 'Unknown')}")
            print(f"   Chunks uploaded: {len(chunks)}")
            print(f"   Work Item ID: {metadata.get('work_item_id', 'Unknown')}")
            return True
        else:
            print("[ERROR] Upload failed")
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
