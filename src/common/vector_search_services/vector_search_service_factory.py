"""
Embedding Service Factory
========================

Provides a unified interface to different embedding services.
Automatically handles fallbacks and provider switching.
"""

import os
from typing import List
from dotenv import load_dotenv

from src.common.embedding_services.embedding_service_factory import _get_local_embedding_generator
from src.common.vector_search_services.azure_cognitive_search import get_azure_search_service
from src.common.vector_search_services.chromadb_service import get_chromadb_service
from src.common.vector_search_services.vector_search_interface import IVectorSearchService

load_dotenv()


def get_vector_search_service(provider: str = None) -> IVectorSearchService:
    """
    Factory function to get the appropriate vector search service

    Args:
        provider: Vector search provider to use. Options:
                 - 'chromadb' : Chroma DB
                 - 'azure': Azure Cognitive Search
                 - None: Auto-detect based on environment
    
    Returns:
        Vector search service instance
    """
    # Auto-detect provider if not specified
    if provider is None:
        provider = 'chromadb'

    print(f"[INFO] Using embedding provider: {provider}")

    if provider == 'chromadb':
        return _get_chromdb_search_service()
    elif provider == 'azure':
        return _get_azure_cognitive_search_service()
    else:
        raise ValueError(f"Unknown search service provider: {provider}. Supported: 'chromadb', 'azure'")

def _get_azure_cognitive_search_service():
    """Get Azure Cognitive Search Search service"""
    
    return get_azure_search_service()

def _get_chromdb_search_service():
    """Get Chroma DB search service"""
    return get_chromadb_service()
