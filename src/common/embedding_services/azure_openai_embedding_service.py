"""
Embedding Generation Service
===========================

Central service for generating embeddings using Azure OpenAI.
Handles both single queries and batch processing with rate limiting and error handling.
"""

import os
import asyncio
from typing import List, Optional
from dotenv import load_dotenv
from ..azure_openai_service import get_azure_openai_service

# Load environment variables
load_dotenv()


class AzureOpenAIEmbeddingGenerator:
    """
    Service for generating embeddings using Azure OpenAI
    Supports both single queries and batch processing
    """
    
    def __init__(self):
        # Load configuration from environment
        self.azure_openai_endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
        self.azure_openai_key = os.getenv('AZURE_OPENAI_KEY')
        self.embedding_deployment = os.getenv('EMBEDDING_DEPLOYMENT', 'text-embedding-ada-002')
        self.embedding_dimension = 1536  # Dimension for text-embedding-ada-002
        
        # Validate required environment variables
        if not all([self.azure_openai_endpoint, self.azure_openai_key]):
            raise ValueError("Missing required Azure OpenAI environment variables: AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_KEY")

        # Initialize Azure OpenAI service
        self.azure_openai_service = get_azure_openai_service()

        print(f"[INFO] AzureOpenAIEmbeddingGenerator initialized:")
        print(f"   - Endpoint: {self.azure_openai_endpoint}")
        print(f"   - Deployment: {self.embedding_deployment}")
        print(f"   - Dimension: {self.embedding_dimension}")
    
    def test_connection(self) -> bool:
        """
        Test the connection to Azure OpenAI service
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            return self.azure_openai_service.test_connection()
        except Exception as e:
            print(f"[ERROR] OpenAIEmbeddingGenerator connection test failed: {e}")
            return False
    
    async def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for a single text query
        
        Args:
            text: Input text to generate embedding for
            
        Returns:
            List of floats representing the embedding vector, or None if failed
        """
        try:
            return await self.azure_openai_service.generate_embedding(text)
        except Exception as e:
            print(f"Error generating embedding for query: {e}")
            return None
    
    async def generate_embeddings_batch(self, texts: List[str], batch_size: int = 16) -> List[List[float]]:
        """
        Generate embeddings for text chunks in batches with rate limiting
        
        Args:
            texts: List of text strings to generate embeddings for
            batch_size: Number of texts to process in each batch (default: 16)
            
        Returns:
            List of embedding vectors (one per input text)
        """
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]

            try:
                # Add delay to respect rate limits
                if i > 0:
                    await asyncio.sleep(1)  # 1 second between batches

                batch_embeddings = await self.azure_openai_service.generate_embeddings_batch(batch)
                
                # Handle None values from failed embeddings
                processed_embeddings = []
                for embedding in batch_embeddings:
                    if embedding is not None:
                        processed_embeddings.append(embedding)
                    else:
                        # Add empty embedding for failed generation
                        empty_embedding = [0.0] * self.embedding_dimension
                        processed_embeddings.append(empty_embedding)
                
                all_embeddings.extend(processed_embeddings)

                print(f"Generated embeddings for batch {i//batch_size + 1}/{(len(texts) + batch_size - 1)//batch_size}")

            except Exception as e:
                print(f"Error generating embeddings for batch {i//batch_size + 1}: {e}")
                # Add empty embeddings for failed batch to maintain alignment
                empty_embedding = [0.0] * self.embedding_dimension
                all_embeddings.extend([empty_embedding] * len(batch))

        return all_embeddings
   
    def get_empty_embedding(self) -> List[float]:
        """Return an empty embedding vector"""
        return [0.0] * self.embedding_dimension
    
    def validate_embedding(self, embedding: Optional[List[float]]) -> bool:
        """
        Validate that an embedding is properly formatted
        
        Args:
            embedding: Embedding vector to validate
            
        Returns:
            True if embedding is valid, False otherwise
        """
        return (
            embedding is not None and
            isinstance(embedding, list) and
            len(embedding) == self.embedding_dimension and
            all(isinstance(x, (int, float)) for x in embedding)
        )
    
    def clean_embedding(self, embedding: Optional[List[float]]) -> List[float]:
        """
        Clean and validate an embedding, returning empty if invalid
        
        Args:
            embedding: Raw embedding to clean
            
        Returns:
            Clean embedding vector or empty embedding if invalid
        """
        if self.validate_embedding(embedding):
            # Ensure all values are floats and not None
            return [float(x) if x is not None else 0.0 for x in embedding]
        else:
            return self.get_empty_embedding()


# Global instance for easy access
_embedding_generator = None

def get_azure_openai_embedding_generator() -> AzureOpenAIEmbeddingGenerator:
    """Get a singleton instance of the AzureOpenAIEmbeddingGenerator"""
    global _embedding_generator
    if _embedding_generator is None:
        _embedding_generator = AzureOpenAIEmbeddingGenerator()
    return _embedding_generator
