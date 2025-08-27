"""
Embedding Service Factory
========================

Provides a unified interface to different embedding services.
Automatically handles fallbacks and provider switching.
"""

import os
from typing import List
from dotenv import load_dotenv

load_dotenv()


def get_embedding_generator(provider: str = None):
    """
    Factory function to get the appropriate embedding generator
    
    Args:
        provider: Embedding provider to use. Options:
                 - 'local' or 'sentence-transformers': Local Sentence Transformers
                 - 'openai': OpenAI public API  
                 - None: Auto-detect based on environment
    
    Returns:
        Embedding generator instance
    """
    # Auto-detect provider if not specified
    if provider is None:
        provider = os.getenv('EMBEDDING_PROVIDER', 'auto')
    
    if provider == 'auto':
        provider = _auto_detect_provider()
    
    print(f"[INFO] Using embedding provider: {provider}")
    
    if provider in ('local', 'sentence-transformers'):
        return _get_local_embedding_generator()
    elif provider == 'openai':
        return _get_openai_embedding_generator()
    else:
        raise ValueError(f"Unknown embedding provider: {provider}. Supported: 'local', 'openai'")


def _auto_detect_provider() -> str:
    """Auto-detect the best available embedding provider"""
    # Check for OpenAI API key
    if os.getenv('OPENAI_API_KEY'):
        return 'openai'
    # Default to local sentence transformers
    return 'local'


def _get_local_embedding_generator():
    """Get local sentence transformers embedding generator"""
    try:
        from .local_embedding_service import LocalEmbeddingGenerator
        
        # Get model preference from environment
        model_preference = os.getenv('LOCAL_EMBEDDING_MODEL', 'fast')
        model_map = {
            'fast': 'all-MiniLM-L6-v2',
            'quality': 'all-mpnet-base-v2',
            'qa': 'multi-qa-MiniLM-L6-cos-v1',
            'multilingual': 'paraphrase-multilingual-MiniLM-L12-v2'
        }
        
        model_name = model_map.get(model_preference, model_preference)
        return LocalEmbeddingGenerator(model_name=model_name)
        
    except ImportError as e:
        print(f"[ERROR] sentence-transformers not available: {e}")
        print("       Install with: pip install sentence-transformers")
        raise


def _get_openai_embedding_generator():
    """Get OpenAI embedding generator"""
    try:
        from .openai_embedding_service import OpenAIEmbeddingGenerator
        return OpenAIEmbeddingGenerator()
    except ImportError as e:
        print(f"[ERROR] OpenAI dependencies not available: {e}")
        print("       Install with: pip install openai")
        raise
