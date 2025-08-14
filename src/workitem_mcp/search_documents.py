"""
Search and Query Azure Cognitive Search
Test search functionality and query documents

This module now uses the centralized AzureCognitiveSearch class for all operations.
"""

import os
import asyncio
from typing import Dict
from dotenv import load_dotenv
import sys
from pathlib import Path

# ONE simple line to fix all imports - find project root and add src
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'src'))

from common.azure_cognitive_search import get_azure_search_service

# Load environment variables
load_dotenv()


class DocumentSearcher:
    """
    Wrapper class for document search operations
    Uses the centralized AzureCognitiveSearch class for all operations
    """
    
    def __init__(self):
        """Initialize the searcher with Azure Cognitive Search service"""
        self.search_service = get_azure_search_service()
        
        # Keep these properties for backward compatibility
        self.service_name = self.search_service.service_name
        self.admin_key = self.search_service.admin_key
        self.index_name = self.search_service.index_name
    
    # ===== SEARCH METHODS =====
    
    def text_search(self, query: str, filters: Dict[str, any] = None, top_k: int = 5):
        """Perform text search using Azure Cognitive Search"""
        return self.search_service.text_search(query, filters, top_k)

    async def vector_search(self, query: str, filters: Dict[str, any] = None, top_k: int = 5):
        """Perform vector search using Azure Cognitive Search"""
        return await self.search_service.vector_search(query, filters, top_k)

    async def hybrid_search(self, query: str, filters: Dict[str, any] = None, top_k: int = 5):
        """Perform hybrid search using Azure Cognitive Search"""
        return await self.search_service.hybrid_search(query, filters, top_k)

    def semantic_search(self, query: str, filters: Dict[str, any] = None, top_k: int = 5):
        """Perform semantic search using Azure Cognitive Search"""
        return self.search_service.semantic_search(query, filters, top_k)
    
    # ===== UTILITY METHODS =====
    
    def get_work_items(self):
        """Get list of all work item IDs in the index"""
        return self.search_service.get_unique_field_values("context_id")
    
    def get_document_count(self):
        """Get total number of documents in the index"""
        return self.search_service.get_document_count()
    
    def print_search_results(self, results, title="Search Results"):
        """Print search results in a formatted way"""
        self.search_service.print_search_results(results, title)