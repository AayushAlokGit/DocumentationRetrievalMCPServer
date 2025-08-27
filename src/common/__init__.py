"""
Common Components
================

Shared components used across both document upload and MCP server functionality.
Includes Azure Cognitive Search integration, embedding services, and OpenAI services.
"""

# Export main classes and functions
from .vector_search_services.azure_cognitive_search import AzureCognitiveSearch, get_azure_search_service
from .embedding_services.openai_embedding_service import OpenAIEmbeddingGenerator, get_openai_embedding_generator
from .embedding_services.embedding_service_factory import get_embedding_generator
from .openai_service import OpenAIService, get_openai_service

__all__ = [
    'AzureCognitiveSearch',
    'get_azure_search_service', 
    'OpenAIEmbeddingGenerator',
    'get_openai_embedding_generator',
    'get_embedding_generator',
    'OpenAIService',
    'get_openai_service'
]
