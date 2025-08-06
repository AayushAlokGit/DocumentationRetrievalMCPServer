"""
Common OpenAI Service
Centralized service for OpenAI client initialization and operations
"""

import os
import asyncio
from typing import List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class OpenAIService:
    """Centralized OpenAI service for embedding generation"""
    
    def __init__(self):
        self.azure_openai_endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
        self.azure_openai_key = os.getenv('AZURE_OPENAI_KEY')
        self.embedding_deployment = os.getenv('EMBEDDING_DEPLOYMENT', 'text-embedding-ada-002')
        self.api_version = os.getenv('OPENAI_API_VERSION', '2024-05-01-preview')
        self._client = None
        
        # Validate configuration
        if not self.azure_openai_endpoint:
            raise ValueError("AZURE_OPENAI_ENDPOINT is required")
        if not self.azure_openai_key:
            raise ValueError("AZURE_OPENAI_KEY is required")
    
    def _get_client(self):
        """Get or create OpenAI client with error handling"""
        if self._client is None:
            try:
                from openai import AzureOpenAI
                self._client = AzureOpenAI(
                    azure_endpoint=self.azure_openai_endpoint,
                    api_key=self.azure_openai_key,
                    api_version=self.api_version
                )
                        
            except ImportError as e:
                print(f"Failed to import OpenAI library: {e}")
                raise e
        
        return self._client
    
    async def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for given text"""
        try:
            client = self._get_client()
            response = client.embeddings.create(
                input=text,
                model=self.embedding_deployment
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return None
    
    async def generate_embeddings_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """Generate embeddings for a batch of texts with improved rate limiting"""
        embeddings = []
        
        # Process each text individually to avoid rate limits
        for i, text in enumerate(texts):
            try:
                client = self._get_client()
                response = client.embeddings.create(
                    input=[text],  # Single text to avoid batch limits
                    model=self.embedding_deployment
                )
                
                embeddings.append(response.data[0].embedding)
                
                # Add delay between requests to avoid rate limiting
                if i < len(texts) - 1:  # Don't delay after the last request
                    await asyncio.sleep(0.5)  # 500ms delay between requests
                    
            except Exception as e:
                print(f"Error generating embedding for text {i+1}: {e}")
                embeddings.append(None)
                
                # If we hit rate limits, add longer delay
                if "429" in str(e) or "Too Many Requests" in str(e):
                    print("Rate limit hit, waiting 10 seconds...")
                    await asyncio.sleep(10)
        
        return embeddings
    
    def test_connection(self) -> bool:
        """Test the OpenAI connection"""
        try:
            client = self._get_client()
            # Try a simple embedding request
            response = client.embeddings.create(
                input="test connection",
                model=self.embedding_deployment
            )
            return len(response.data) > 0
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False


# Global service instance
_openai_service = None


def get_openai_service() -> OpenAIService:
    """Get singleton OpenAI service instance"""
    global _openai_service
    if _openai_service is None:
        _openai_service = OpenAIService()
    return _openai_service


async def main():
    """Test the OpenAI service"""
    print("Testing OpenAI Service...")
    
    try:
        service = get_openai_service()
        
        # Test connection
        print("Testing connection...")
        if service.test_connection():
            print("✅ Connection successful")
        else:
            print("❌ Connection failed")
            return
        
        # Test single embedding
        print("Testing single embedding...")
        embedding = await service.generate_embedding("Hello world")
        if embedding:
            print(f"✅ Single embedding generated (length: {len(embedding)})")
        else:
            print("❌ Single embedding failed")
        
        # Test batch embeddings
        print("Testing batch embeddings...")
        texts = ["Hello", "World", "Test"]
        embeddings = await service.generate_embeddings_batch(texts)
        successful_embeddings = [e for e in embeddings if e is not None]
        print(f"✅ Batch embeddings: {len(successful_embeddings)}/{len(texts)} successful")
        
    except Exception as e:
        print(f"❌ Service test failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
