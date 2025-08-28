#!/usr/bin/env python3
"""
ChromaDB Data Inspector
======================

Simple script to inspect ChromaDB data and view collection contents
"""

import chromadb
from chromadb.config import Settings
import json
from pathlib import Path

def export_collection_to_json(collection_name="documentation_collection", 
                              output_file="chromadb_export.json",
                              chromadb_path="./chromadb_data"):
    """Export a specific collection to JSON for viewing"""
    
    client = chromadb.PersistentClient(path=chromadb_path)
    
    try:
        collection = client.get_collection(collection_name)
        results = collection.get(include=['metadatas', 'documents'])
        
        # Format for JSON export
        export_data = {
            "collection_name": collection_name,
            "document_count": len(results['ids']),
            "documents": []
        }
        
        for i, doc_id in enumerate(results['ids']):
            doc = {
                "id": doc_id,
                "content": results['documents'][i] if i < len(results['documents']) else "",
                "metadata": results['metadatas'][i] if i < len(results['metadatas']) else {}
            }
            export_data["documents"].append(doc)
        
        # Save to JSON file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Exported {len(results['ids'])} documents to {output_file}")
        
    except Exception as e:
        print(f"❌ Export failed: {e}")


if __name__ == "__main__":
    import sys
    
    print("ChromaDB Data JSON Export")
    print("=========================")
    
    # Parse command line arguments
    # Usage: python export_chromadb_data.py [collection_name] [output_file]
    collection_name = sys.argv[1] if len(sys.argv) > 1 else "documentation_collection"
    output_file = sys.argv[2] if len(sys.argv) > 2 else "chromadb_export.json"
    
    print(f"📤 Exporting collection '{collection_name}' to '{output_file}'...")
    export_collection_to_json(collection_name, output_file)
