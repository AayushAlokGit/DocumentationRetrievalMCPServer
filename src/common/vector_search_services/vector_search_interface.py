"""
Vector Search Service Interface
==============================

Abstract base class defining the interface for vector search services.
Provides a consistent API for different vector search implementations
like Azure Cognitive Search and ChromaDB.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple


class IVectorSearchService(ABC):
    """
    Abstract base class for vector search services
    
    Defines the common interface that all vector search implementations must follow.
    This ensures consistency across different providers (Azure Cognitive Search, ChromaDB, etc.)
    """
    
    # ===== CONNECTION & CONFIGURATION =====
    
    @abstractmethod
    def test_connection(self) -> bool:
        """
        Test connection to the vector search service
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_document_count(self) -> int:
        """
        Get total number of documents in the index/collection
        
        Returns:
            int: Number of documents
        """
        pass
    
    # ===== DOCUMENT OPERATIONS =====
    
    @abstractmethod
    def upload_search_objects_batch(self, search_objects: List[Dict[str, Any]]) -> Tuple[int, int]:
        """
        Upload search objects in batch to the vector search service
        
        Args:
            search_objects: List of search objects to upload
            
        Returns:
            Tuple of (successful_uploads, failed_uploads)
        """
        pass
    
    @abstractmethod
    def delete_document(self, document_id: str) -> bool:
        """
        Delete a specific document by ID
        
        Args:
            document_id: The document ID to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def delete_documents_by_filter(self, filters: Dict[str, Any]) -> int:
        """
        Delete documents matching filter criteria
        
        Args:
            filters: Dictionary of field names and values to filter by
            
        Returns:
            int: Number of documents deleted
        """
        pass
    
    # ===== SEARCH OPERATIONS =====
    
    @abstractmethod
    async def vector_search(self, query: str, filters: Optional[Dict[str, Any]] = None, top: int = 5) -> List[Dict]:
        """
        Perform vector-based semantic search
        
        Args:
            query: Search query string
            filters: Optional dictionary of field filters
            top: Maximum number of results
            
        Returns:
            List of search result dictionaries
        """
        pass
    
    # ===== UTILITY METHODS =====
    
    @abstractmethod
    def get_unique_field_values(self, field_name: str, max_values: int = 1000) -> List[str]:
        """
        Get unique values for any field
        
        Args:
            field_name: Name of the field to get unique values for
            max_values: Maximum number of unique values to return
            
        Returns:
            List of unique values for the field
        """
        pass
