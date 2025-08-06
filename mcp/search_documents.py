"""
Search and Query Azure Cognitive Search
Test search functionality and query documents

This module now uses the centralized AzureCognitiveSearch class for all operations.
"""

import os
import asyncio
from dotenv import load_dotenv
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "common"))

from azure_cognitive_search import get_azure_search_service

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
    
    def text_search(self, query: str, work_item_id: str = None, top_k: int = 5):
        """Perform text search using Azure Cognitive Search"""
        return self.search_service.text_search(query, work_item_id, top_k)
    
    async def vector_search(self, query: str, work_item_id: str = None, top_k: int = 5):
        """Perform vector search using Azure Cognitive Search"""
        return await self.search_service.vector_search(query, work_item_id, top_k)
    
    async def hybrid_search(self, query: str, work_item_id: str = None, top_k: int = 5):
        """Perform hybrid search using Azure Cognitive Search"""
        return await self.search_service.hybrid_search(query, work_item_id, top_k)
    
    def semantic_search(self, query: str, work_item_id: str = None, top_k: int = 5):
        """Perform semantic search using Azure Cognitive Search"""
        return self.search_service.semantic_search(query, work_item_id, top_k)
    
    # ===== UTILITY METHODS =====
    
    def get_work_items(self):
        """Get list of all work item IDs in the index"""
        return self.search_service.get_work_items()
    
    def get_document_count(self):
        """Get total number of documents in the index"""
        return self.search_service.get_document_count()
    
    def print_search_results(self, results, title="Search Results"):
        """Print search results in a formatted way"""
        self.search_service.print_search_results(results, title)