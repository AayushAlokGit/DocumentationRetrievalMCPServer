"""
Ollama Embedding Service
=======================

Uses Ollama for local embedding generation.
Completely free and runs entirely on your machine.
"""

import os
import json
import aiohttp
from typing import List, Optional


class OllamaEmbeddingGenerator:
    """
    Local embedding generator using Ollama
    
    Advantages:
    - Completely free and local
    - No internet required after setup
    - Multiple models available
    - Privacy-focused (data never leaves your machine)
    
    Setup:
    1. Install Ollama: https://ollama.ai/
    2. Run: ollama pull nomic-embed-text
    3. Start Ollama service
    """
    
    def __init__(self, 
                 model_name: str = 'nomic-embed-text',
                 base_url: str = 'http://localhost:11434'):
        """
        Initialize Ollama embedding generator
        
        Args:
            model_name: Name of the Ollama embedding model
                       Options:
                       - 'nomic-embed-text' (8192 context, good quality)
                       - 'mxbai-embed-large' (512 dim, fast)
            base_url: Ollama server URL
        """
        self.model_name = model_name
        self.base_url = base_url.rstrip('/')
        self.embedding_dimension = self._get_model_dimension(model_name)
        
        print(f"[INFO] OllamaEmbeddingGenerator initialized:")
        print(f"   - Model: {self.model_name}")
        print(f"   - Base URL: {self.base_url}")
        print(f"   - Estimated Dimension: {self.embedding_dimension}")
        print(f"   - Setup: Ensure 'ollama pull {model_name}' was run")
    
    def _get_model_dimension(self, model_name: str) -> int:
        """Get estimated embedding dimension for model"""
        dimensions = {
            'nomic-embed-text': 768,
            'mxbai-embed-large': 1024,
            'all-minilm': 384
        }
        return dimensions.get(model_name, 768)
    
    async def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding using Ollama API
        
        Args:
            text: Input text to embed
            
        Returns:
            Embedding vector as list of floats, or None if error
        """
        if not text or not text.strip():
            return None
            
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": self.model_name,
                    "prompt": text.strip()
                }
                
                async with session.post(
                    f"{self.base_url}/api/embeddings",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        embedding = result.get('embedding')
                        
                        if embedding:
                            return embedding
                        else:
                            print(f"[ERROR] No embedding in Ollama response: {result}")
                            return None
                    else:
                        error_text = await response.text()
                        print(f"[ERROR] Ollama API error {response.status}: {error_text}")
                        return None
                        
        except aiohttp.ClientError as e:
            print(f"[ERROR] Ollama connection failed: {e}")
            print("      Ensure Ollama is running: ollama serve")
            return None
        except Exception as e:
            print(f"[ERROR] Ollama embedding generation failed: {e}")
            return None
    
    async def generate_embeddings_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """
        Generate embeddings for multiple texts
        Note: Ollama doesn't support batch embedding, so we process sequentially
        
        Args:
            texts: List of input texts
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        embeddings = []
        
        for text in texts:
            embedding = await self.generate_embedding(text)
            embeddings.append(embedding)
        
        return embeddings
    
    async def test_connection(self) -> bool:
        """Test Ollama connection and model availability"""
        try:
            # Test basic connection
            embedding = await self.generate_embedding("test connection")
            
            if embedding and isinstance(embedding, list) and len(embedding) > 0:
                actual_dim = len(embedding)
                print(f"[SUCCESS] Ollama test successful. Actual dimension: {actual_dim}")
                
                # Update dimension if different
                if actual_dim != self.embedding_dimension:
                    print(f"[INFO] Updating dimension from {self.embedding_dimension} to {actual_dim}")
                    self.embedding_dimension = actual_dim
                
                return True
            else:
                print("[ERROR] Ollama test failed - invalid embedding")
                return False
                
        except Exception as e:
            print(f"[ERROR] Ollama test failed: {e}")
            return False
    
    async def list_available_models(self) -> List[str]:
        """List available embedding models in Ollama"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/tags") as response:
                    if response.status == 200:
                        result = await response.json()
                        models = [model['name'] for model in result.get('models', [])]
                        
                        # Filter for embedding models
                        embedding_models = [m for m in models if 'embed' in m.lower()]
                        return embedding_models
                    else:
                        return []
        except:
            return []


# Ollama embedding model recommendations
OLLAMA_MODELS = {
    'nomic-embed-text': {
        'pull_command': 'ollama pull nomic-embed-text',
        'dimension': 768,
        'context_length': 8192,
        'description': 'High-quality embedding model, good for most tasks'
    },
    'mxbai-embed-large': {
        'pull_command': 'ollama pull mxbai-embed-large', 
        'dimension': 1024,
        'context_length': 512,
        'description': 'Fast embedding model, good for shorter texts'
    }
}
