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

# Load environment variables
load_dotenv()


class AzureOpenAIEmbeddingGenerator:
    """
    Service for generating embeddings using Azure OpenAI
    Supports both single queries and batch processing
    """
    
    def __init__(self):
        # Load configuration from environment - Azure AI Foundry
        self.azure_ai_foundry_endpoint = os.getenv('AZURE_AI_FOUNDRY_ENDPOINT')
        self.azure_ai_foundry_embedding_model_key = os.getenv('AZURE_AI_FOUNDRY_EMBEDDING_MODEL_KEY') 
        self.embedding_deployment = os.getenv('EMBEDDING_DEPLOYMENT', 'text-embedding-3-large')
        self.api_version = os.getenv('OPENAI_API_VERSION', '2024-05-01-preview')
        
        # Dynamic embedding dimensions based on model
        embedding_dims = os.getenv('EMBEDDING_DIMENSIONS', '3072')
        self.embedding_dimension = int(embedding_dims)
        
        # OpenAI client will be initialized on first use
        self._client = None
        
        # Validate required environment variables
        if not all([self.azure_ai_foundry_endpoint, self.azure_ai_foundry_embedding_model_key]):
            raise ValueError("Missing required Azure AI Foundry environment variables: AZURE_AI_FOUNDRY_ENDPOINT, AZURE_AI_FOUNDRY_EMBEDDING_MODEL_KEY")

        print(f"[INFO] AzureOpenAIEmbeddingGenerator initialized:")
        print(f"   - AI Foundry Endpoint: {self.azure_ai_foundry_endpoint}")
        print(f"   - Deployment: {self.embedding_deployment}")
        print(f"   - Dimension: {self.embedding_dimension}")
    
    def _get_client(self):
        """Get or create OpenAI client with error handling"""
        if self._client is None:
            try:
                from openai import AzureOpenAI
                self._client = AzureOpenAI(
                    azure_endpoint=self.azure_ai_foundry_endpoint,
                    api_key=self.azure_ai_foundry_embedding_model_key,
                    api_version=self.api_version
                )
            except ImportError as e:
                print(f"Failed to import OpenAI library: {e}")
                raise e
        return self._client
    
    def test_connection(self) -> bool:
        """
        Test the connection to Azure OpenAI service
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            client = self._get_client()
            # Test with a simple embedding request
            response = client.embeddings.create(
                model=self.embedding_deployment,
                input=["test connection"]
            )
            return response and len(response.data) > 0
        except Exception as e:
            print(f"[ERROR] Connection test failed: {e}")
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
            client = self._get_client()
            response = client.embeddings.create(
                model=self.embedding_deployment,
                input=[text]
            )
            
            if response and response.data and len(response.data) > 0:
                return response.data[0].embedding
            return None
            
        except Exception as e:
            print(f"Error generating embedding for text: {e}")
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

                client = self._get_client()
                response = client.embeddings.create(
                    model=self.embedding_deployment,
                    input=batch
                )
                
                # Handle response and extract embeddings
                batch_embeddings = []
                if response and response.data:
                    for embedding_data in response.data:
                        if embedding_data and embedding_data.embedding:
                            batch_embeddings.append(embedding_data.embedding)
                        else:
                            # Add empty embedding for failed generation
                            empty_embedding = [0.0] * self.embedding_dimension
                            batch_embeddings.append(empty_embedding)
                else:
                    # Add empty embeddings for failed batch
                    empty_embedding = [0.0] * self.embedding_dimension
                    batch_embeddings = [empty_embedding] * len(batch)
                
                all_embeddings.extend(batch_embeddings)
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
