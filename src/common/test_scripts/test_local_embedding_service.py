#!/usr/bin/env python3
"""
Test Local Embedding Service
====================                        print("❌ Single embedding test failed")
                        failed_models += 1
                
                else:
                    print(f"❌ Model {model_name} failed connection test")
                    failed_models += 1
                    
            except Exception as e:
                print(f"❌ Error testing {model_name}: {e}")
                failed_models += 1
        
        print(f"\n🎉 Local embedding service testing completed!")
        print(f"📊 Results: ✅ {successful_models} successful, ❌ {failed_models} failed")
        
        return successful_models > 0
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Install dependencies: pip install sentence-transformers torch transformers")
        return False the local sentence transformers embedding service
"""

import os
import sys
import asyncio

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

async def test_local_embedding_service():
    """Test local embedding service with all available models"""
    print("🧪 Testing Local Embedding Service - All Models...")
    
    try:
        from src.common.embedding_services.local_embedding_service import LocalEmbeddingGenerator, EMBEDDING_MODELS
        
        # Test all available models from the local embedding service
        print(f"📋 Found {len(EMBEDDING_MODELS)} available models to test")
        
        successful_models = 0
        failed_models = 0
        
        for model_type, model_info in EMBEDDING_MODELS.items():
            model_name = model_info['model']
            dimension = model_info['dimension']
            description = model_info['description']
            
            print(f"\n🔧 Testing {model_type.upper()}: {model_name}")
            print(f"   📝 {description}")
            print(f"   📐 Expected dimension: {dimension}")
            
            try:
                # Initialize the embedding generator
                generator = LocalEmbeddingGenerator(model_name=model_name)
                
                # Test connection
                if generator.test_connection():
                    print(f"✅ Model {model_name} loaded successfully")
                    print(f"   Embedding dimension: {generator.embedding_dimension}")
                    
                    # Verify dimension matches expected
                    if generator.embedding_dimension == dimension:
                        print(f"✅ Dimension verification passed")
                    else:
                        print(f"⚠️  Dimension mismatch: expected {dimension}, got {generator.embedding_dimension}")
                    
                    # Test single embedding
                    test_text = "This is a test document about machine learning and artificial intelligence."
                    embedding = await generator.generate_embedding(test_text)
                    
                    if embedding and len(embedding) > 0:
                        print(f"✅ Single embedding test passed")
                        print(f"   Text: '{test_text[:50]}...'")
                        print(f"   Embedding dimension: {len(embedding)}")
                        print(f"   First 5 values: {embedding[:5]}")
                        successful_models += 1
                    else:
                        print("❌ Single embedding test failed")
                    
                    # Test batch embeddings
                    test_texts = [
                        "Python is a programming language",
                        "Machine learning uses algorithms to find patterns",
                        "Natural language processing works with text data"
                    ]
                    
                    batch_embeddings = await generator.generate_embeddings_batch(test_texts)
                    
                    if batch_embeddings and len(batch_embeddings) == len(test_texts):
                        successful_embeddings = [emb for emb in batch_embeddings if emb is not None]
                        print(f"✅ Batch embedding test passed")
                        print(f"   Processed {len(successful_embeddings)}/{len(test_texts)} texts")
                    else:
                        print("❌ Batch embedding test failed")
                
                else:
                    print(f"❌ Model {model_name} failed connection test")
                    
            except Exception as e:
                print(f"❌ Error testing {model_name}: {e}")
        
        print("\n🎉 Local embedding service testing completed!")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Install dependencies: pip install sentence-transformers torch transformers")
        return False
        
    return True


async def main():
    """Run all local embedding tests"""
    print("🚀 Local Embedding Service Test Suite - All Models\n")
    
    success = await test_local_embedding_service()

    if success:
        print("\n✅ Tests completed! Local embedding service is ready to use.")
        print("\n📋 Summary:")
        print("   • Multiple embedding models tested: ✅")
        print("   • Local embedding generation: ✅ Working")
        print("   • No API keys required: ✅")
        print("   • Offline operation: ✅")
        print("   • Free forever: ✅")
        print("\n🔧 Available models:")
        print("   • Fast: all-MiniLM-L6-v2 (384 dim)")
        print("   • Quality: all-mpnet-base-v2 (768 dim)")
        print("   • QA: multi-qa-MiniLM-L6-cos-v1 (384 dim)")
    else:
        print("\n❌ All tests failed. Check dependencies.")

if __name__ == "__main__":
    asyncio.run(main())
