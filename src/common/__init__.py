"""
Common Components
================

Shared components used across both document upload and MCP server functionality.
Includes Azure Cognitive Search integration, embedding services, and OpenAI services.
"""

# Export main classes and functions
from .vector_search_services.azure_cognitive_search import AzureCognitiveSearch, get_azure_search_service
from .embedding_services.azure_openai_embedding_service import AzureOpenAIEmbeddingGenerator, get_azure_openai_embedding_generator
from .embedding_services.embedding_service_factory import get_embedding_generator

__all__ = [
    'AzureCognitiveSearch',
    'get_azure_search_service', 
    'AzureOpenAIEmbeddingGenerator',
    'get_azure_openai_embedding_generator',
    'get_embedding_generator'
]
