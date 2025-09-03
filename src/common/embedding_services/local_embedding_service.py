"""
Local Embedding Service using Sentence Transformers
==================================================

Free, local embedding generation using Hugging Face transformers.
No API keys or internet required after initial model download.
"""

import os
from typing import List, Optional
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False


class LocalEmbeddingGenerator:
    """
    Local embedding generator using Sentence Transformers
    
    Advantages:
    - Completely free
    - No API keys required
    - Works offline after model download
    - Fast inference on CPU
    - Multiple model options
    """
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initialize local embedding generator
        
        Args:
            model_name: Name of the sentence transformer model
                       Options:
                       - 'all-MiniLM-L6-v2' (384 dim, fast, good quality)
                       - 'all-mpnet-base-v2' (768 dim, slower, better quality)  
                       - 'multi-qa-MiniLM-L6-cos-v1' (384 dim, optimized for QA)
        """
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError(
                "sentence-transformers not installed. "
                "Install with: pip install sentence-transformers"
            )
        
        self.model_name = model_name
        print(f"[INFO] Loading local embedding model: {model_name}")
        
        # Load the model (downloads automatically if not cached)
        self.model = SentenceTransformer(model_name)
        self.embedding_dimension = self.model.get_sentence_embedding_dimension()
        
        print(f"[INFO] LocalEmbeddingGenerator initialized:")
        print(f"   - Model: {self.model_name}")
        print(f"   - Dimension: {self.embedding_dimension}")
        print(f"   - Device: {self.model.device}")
    
    async def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for a single text
        
        Args:
            text: Input text to embed
            
        Returns:
            Embedding vector as list of floats, or None if error
        """
        if not text or not text.strip():
            return None
            
        try:
            # Generate embedding (runs in thread pool to avoid blocking)
            import asyncio
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(
                None, 
                lambda: self.model.encode(text.strip(), convert_to_numpy=True)
            )
            
            return embedding.tolist()
            
        except Exception as e:
            print(f"[ERROR] Failed to generate embedding: {e}")
            return None
    
    async def generate_embeddings_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """
        Generate embeddings for multiple texts in batch
        
        Args:
            texts: List of input texts
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        try:
            # Clean texts
            clean_texts = [text.strip() for text in texts if text and text.strip()]
            
            if not clean_texts:
                return [None] * len(texts)
            
            # Generate embeddings in batch (more efficient)
            import asyncio
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                None,
                lambda: self.model.encode(clean_texts, convert_to_numpy=True, show_progress_bar=True)
            )
            
            return [emb.tolist() for emb in embeddings]
            
        except Exception as e:
            print(f"[ERROR] Batch embedding generation failed: {e}")
            return [None] * len(texts)
    
    def test_connection(self) -> bool:
        """Test the embedding generator"""
        try:
            test_embedding = self.model.encode("test text")
            print(f"[SUCCESS] Local embedding test successful. Dimension: {len(test_embedding)}")
            return True
        except Exception as e:
            print(f"[ERROR] Local embedding test failed: {e}")
            return False


# Model recommendations by use case
EMBEDDING_MODELS = {
    'fast': {
        'model': 'all-MiniLM-L6-v2',
        'dimension': 384,
        'description': 'Fast, lightweight, good for most use cases'
    },
    'quality': {
        'model': 'all-mpnet-base-v2', 
        'dimension': 768,
        'description': 'Better quality, slower, larger embeddings'
    },
    'qa': {
        'model': 'multi-qa-MiniLM-L6-cos-v1',
        'dimension': 384, 
        'description': 'Optimized for question-answering tasks'
    },
    'multilingual': {
        'model': 'paraphrase-multilingual-MiniLM-L12-v2',
        'dimension': 768,
        'description': 'Supports multiple languages'
    }
}

def get_local_embedding_generator():
    """Get local sentence transformers embedding generator"""
    try:
        from .local_embedding_service import LocalEmbeddingGenerator
        
        # Get model preference from environment
        model_preference = os.getenv('LOCAL_EMBEDDING_MODEL', 'fast')
        model_name = EMBEDDING_MODELS.get(model_preference)['model']
        return LocalEmbeddingGenerator(model_name=model_name)
        
    except ImportError as e:
        print(f"[ERROR] sentence-transformers not available: {e}")
        print("       Install with: pip install sentence-transformers")
        raise