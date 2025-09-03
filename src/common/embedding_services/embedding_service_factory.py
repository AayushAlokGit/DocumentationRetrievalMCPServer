"""
Embedding Service Factory
========================

Provides a unified interface to different embedding services.
Automatically handles fallbacks and provider switching.
"""

import os
from typing import List
from dotenv import load_dotenv

from src.common.embedding_services.azure_openai_embedding_service import get_azure_openai_embedding_generator
from src.common.embedding_services.local_embedding_service import get_local_embedding_generator

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
        provider = os.getenv('EMBEDDING_PROVIDER_SERVICE', 'local')

    print(f"[INFO] Using embedding provider: {provider}")
    
    if provider in ('local', 'sentence-transformers'):
        return get_local_embedding_generator()
    elif provider == 'openai':
        return get_azure_openai_embedding_generator()
    else:
        raise ValueError(f"Unknown embedding provider: {provider}. Supported: 'local', 'openai'")


