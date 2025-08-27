#!/usr/bin/env python3
"""
ChromaDB with Local Embedding Test
==================================

Test ChromaDB service with local embedding service
"""

import os
import sys
import asyncio

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

async def test_chromadb_with_local_embedding():
    """Test ChromaDB service with local embedding"""
    print("🧪 Testing ChromaDB with Local Embedding Service...")
    
    # Set environment to use local embedding provider
    os.environ['EMBEDDING_PROVIDER'] = 'local'
    os.environ['LOCAL_EMBEDDING_MODEL'] = 'fast'
    
    try:
        from src.common.vector_search_services.chromadb_service import ChromaDBService
        
        print("🔧 Initializing ChromaDB service with local embeddings...")
        chromadb_service = ChromaDBService(collection_name="test_local_embedding_clean")
        
        # Delete collection if exists to start fresh
        try:
            chromadb_service.client.delete_collection("test_local_embedding_clean")
            print("   🗑️ Cleaned existing collection")
        except:
            pass
            
        # Recreate service
        chromadb_service = ChromaDBService(collection_name="test_local_embedding_clean")
        
        # Test documents (without embeddings first)
        test_documents = [
            {
                'id': 'doc1',
                'content': 'This is a test document about machine learning and artificial intelligence.',
                'context_name': 'test_context',
                'file_name': 'test1.md',
                'category': 'technology'
            },
            {
                'id': 'doc2', 
                'content': 'Python is a popular programming language for data science and web development.',
                'context_name': 'test_context',
                'file_name': 'test2.md',
                'category': 'programming'
            }
        ]
        
        # Generate embeddings for the documents
        print("🧮 Generating embeddings for test documents...")
        from src.common.embedding_services.embedding_service_factory import get_embedding_generator
        embedding_gen = get_embedding_generator(provider='local')
        
        for doc in test_documents:
            embedding = await embedding_gen.generate_embedding(doc['content'])
            doc['content_vector'] = embedding
            print(f"   ✅ Generated embedding for {doc['id']} (dimension: {len(embedding)})")
        
        print("📄 Uploading test documents...")
        success_count, failed_count = chromadb_service.upload_search_objects_batch(test_documents)
        print(f"   ✅ Uploaded: {success_count}, ❌ Failed: {failed_count}")
        
        if success_count > 0:
            # Test search
            print("🔍 Testing search functionality...")
            search_results = await chromadb_service.vector_search(
                query="machine learning programming",
                top=5,
                filters={'context_name': 'test_context'}
            )
            
            print(f"   Found {len(search_results)} results:")
            for i, result in enumerate(search_results, 1):
                score = result.get('score', 'N/A')
                score_str = f"{score:.4f}" if isinstance(score, (int, float)) else str(score)
                print(f"   {i}. ID: {result.get('id')}")
                print(f"      Score: {score_str}")
                print(f"      Content: {result.get('content', '')[:80]}...")
                
        return success_count > 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_chromadb_with_local_embedding())
    if result:
        print("\n🎉 ChromaDB with local embedding is working perfectly!")
    else:
        print("\n💥 ChromaDB with local embedding test failed")
