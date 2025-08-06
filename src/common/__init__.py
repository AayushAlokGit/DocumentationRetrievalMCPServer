"""
Common Components
================

Shared components used across both document upload and MCP server functionality.
Includes Azure Cognitive Search integration, embedding services, and OpenAI services.
"""

# Export main classes and functions
from .azure_cognitive_search import AzureCognitiveSearch, get_azure_search_service
from .embedding_service import EmbeddingGenerator, get_embedding_generator, generate_query_embedding
from .openai_service import OpenAIService, get_openai_service

__all__ = [
    'AzureCognitiveSearch',
    'get_azure_search_service', 
    'EmbeddingGenerator',
    'get_embedding_generator',
    'generate_query_embedding',
    'OpenAIService',
    'get_openai_service'
]
