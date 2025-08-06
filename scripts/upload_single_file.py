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
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from document_upload import upload_document_to_search
from document_utils import read_markdown_file, extract_metadata, simple_chunk_text
from openai_service import get_openai_service


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
        content = read_markdown_file(file_path)
        metadata = extract_metadata(content, file_path)
        chunks = simple_chunk_text(content)
        
        print(f"📖 File parsed successfully")
        print(f"   Title: {metadata.get('title', 'Unknown')}")
        print(f"   Work Item ID: {metadata.get('work_item_id', 'Unknown')}")
        print(f"   Tags: {metadata.get('tags', [])}")
        print(f"   Content length: {len(content)} characters")
        print(f"   Chunks created: {len(chunks)}")
        
        # Initialize OpenAI service  
        openai_service = get_openai_service()
        
        if not openai_service.test_connection():
            print("[ERROR] Failed to connect to Azure OpenAI. Please check your credentials.")
            return False
        
        # Generate embeddings
        print("🧠 Generating embeddings...")
        embeddings = []
        for chunk in chunks:
            embedding = await openai_service.get_embedding_async(chunk)
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
        
        # Upload to search
        print("⬆️  Uploading to Azure Cognitive Search...")
        success = await upload_document_to_search(document)
        
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
