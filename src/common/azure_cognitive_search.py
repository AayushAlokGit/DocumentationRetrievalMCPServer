"""
Azure Cognitive Search Service Class
===================================

A comprehensive class for managing Azure Cognitive Search operations including:
- Index management (create, delete, check existence)
- Document upload and deletion
- Text, vector, and hybrid search operations
- Work item specific operations

This class provides a centralized interface for all Azure Cognitive Search operations
used throughout the Work Item Documentation system.
"""

import os
import json
import hashlib
from datetime import datetime
from pathlib import Path
import sys
from typing import List, Dict, Optional, Any, Tuple
from dotenv import load_dotenv

# Azure Search imports
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SearchField,
    SearchFieldDataType,
    SimpleField,
    SearchableField,
    VectorSearch,
    HnswAlgorithmConfiguration,
    VectorSearchProfile,
    SemanticConfiguration,
    SemanticPrioritizedFields,
    SemanticField,
    SemanticSearch
)
from azure.search.documents.models import VectorizedQuery
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import ResourceNotFoundError

# ONE simple line to fix all imports - find project root and add src
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'src'))

# Import embedding service
from common.embedding_service import get_embedding_generator

# Load environment variables
load_dotenv()


class FilterBuilder:
    """
    Filter builder for Azure Cognitive Search OData expressions
    
    Supported OData Expression Features:
    ===================================
    
    Data Type Support:
    - String values: field_name eq 'string_value'
    - Numeric values (int/float): field_name eq 42 or field_name eq 3.14
    - List values: field_name eq 'value1' or field_name eq 'value2' (wrapped in parentheses)
    
    Logical Operators:
    - Equality (eq): All field types support equality comparison
    - AND logic: Multiple field conditions joined with 'and'
    - OR logic: List values automatically generate OR expressions within parentheses
    
    Expression Examples:
    ===================
    Single field:
        {"context_id": "WORK-123"} → "context_id eq 'WORK-123'"
        
    Multiple fields (AND):
        {"context_id": "WORK-123", "file_type": "md"} → "context_id eq 'WORK-123' and file_type eq 'md'"
        
    Numeric fields:
        {"chunk_index": 5} → "chunk_index eq 5"
        
    List values (OR within field):
        {"context_id": ["WORK-123", "WORK-456"]} → "(context_id eq 'WORK-123' or context_id eq 'WORK-456')"
        
    Mixed example:
        {"context_id": ["WORK-123", "WORK-456"], "file_type": "md"} → 
        "(context_id eq 'WORK-123' or context_id eq 'WORK-456') and file_type eq 'md'"
    
    Current Limitations:
    ===================
    - Only equality (eq) operator supported (no gt, lt, ge, le, ne)
    - No date/time operations or functions
    - No string functions (startswith, endswith, contains)
    - No complex nested expressions or custom parentheses grouping
    - No NOT logic support
    
    TODO: Future Extensions
    ======================
    - Add comparison operators: gt, lt, ge, le, ne
    - Add string functions: startswith(), endswith(), contains()
    - Add date functions and comparisons
    - Add support for complex nested expressions
    - Add NOT operator support
    - Add custom grouping with parentheses
    """

    @staticmethod
    def build_filter(filters: Dict[str, Any]) -> Optional[str]:
        """
        Convert filter dictionary to OData expression

        Args:
            filters: Dictionary of field_name: value pairs

        Returns:
            OData filter string or None
        """
        if not filters:
            return None

        expressions = []
        for field_name, field_value in filters.items():
            if isinstance(field_value, str):
                expressions.append(f"{field_name} eq '{field_value}'")
            elif isinstance(field_value, (int, float)):
                expressions.append(f"{field_name} eq {field_value}")
            elif isinstance(field_value, list):
                # Handle multiple values with OR
                value_exprs = [f"{field_name} eq '{v}'" for v in field_value]
                expressions.append(f"({' or '.join(value_exprs)})")

        return " and ".join(expressions) if expressions else None


class AzureCognitiveSearch:
    """
    Comprehensive Azure Cognitive Search service class
    
    Provides all functionality needed for managing work item documentation
    in Azure Cognitive Search including index management, document operations,
    and various search methods.
    """
    
    def __init__(self, 
                 service_name: Optional[str] = None,
                 admin_key: Optional[str] = None,
                 index_name: Optional[str] = None):
        """
        Initialize Azure Cognitive Search service
        
        Args:
            service_name: Azure Search service name (from env if not provided)
            admin_key: Azure Search admin key (from env if not provided)
            index_name: Search index name (from env if not provided)
        """
        self.service_name = service_name or os.getenv('AZURE_SEARCH_SERVICE')
        self.admin_key = admin_key or os.getenv('AZURE_SEARCH_KEY')
        self.index_name = index_name or os.getenv('AZURE_SEARCH_INDEX', 'work-items-index')
        
        if not self.service_name:
            raise ValueError("Azure Search service name not provided or found in environment")
        if not self.admin_key:
            raise ValueError("Azure Search admin key not provided or found in environment")
        
        self.endpoint = f"https://{self.service_name}.search.windows.net"
        self.credential = AzureKeyCredential(self.admin_key)
        
        # Initialize clients
        self.index_client = SearchIndexClient(
            endpoint=self.endpoint,
            credential=self.credential
        )
        
        self.search_client = SearchClient(
            endpoint=self.endpoint,
            index_name=self.index_name,
            credential=self.credential
        )
        
        # Initialize embedding generator
        self.embedding_generator = get_embedding_generator()
    
    # ===== INDEX MANAGEMENT =====
    
    def create_index(self, vector_dimensions: int = 1536) -> bool:
        """
        Create the search index with vector search capabilities
        
        Args:
            vector_dimensions: Dimension of the vector embeddings (default 1536 for OpenAI)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Define the fields for the index - matching create_index.py schema
            fields = [
                SimpleField(
                    name="id",
                    type=SearchFieldDataType.String,
                    key=True,
                    filterable=True,
                    retrievable=True
                ),
                SearchableField(
                    name="content",
                    type=SearchFieldDataType.String,
                    searchable=True,
                    retrievable=True,
                    analyzer_name="standard.lucene"
                ),
                SearchField(
                    name="content_vector",
                    type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                    searchable=True,
                    vector_search_dimensions=vector_dimensions,
                    vector_search_profile_name="vector-profile"
                ),
                # Core file information
                SimpleField(
                    name="file_path",
                    type=SearchFieldDataType.String,
                    filterable=True,
                    retrievable=True,
                    facetable=True
                ),
                SearchableField(
                    name="file_name",
                    type=SearchFieldDataType.String,
                    searchable=True,
                    filterable=True,
                    retrievable=True,
                    facetable=True
                ),
                SimpleField(
                    name="file_type",
                    type=SearchFieldDataType.String,
                    filterable=True,
                    retrievable=True,
                    facetable=True
                ),
                # Document metadata
                SearchableField(
                    name="title",
                    type=SearchFieldDataType.String,
                    searchable=True,
                    retrievable=True
                ),
                SearchableField(
                    name="tags",
                    type=SearchFieldDataType.Collection(SearchFieldDataType.String),
                    searchable=True,
                    filterable=True,
                    retrievable=True,
                    facetable=True
                ),
                SearchableField(
                    name="category",
                    type=SearchFieldDataType.String,
                    searchable=True,
                    filterable=True,
                    retrievable=True,
                    facetable=True
                ),
                # Context/grouping (flexible - can be work_item_id, project, folder, etc.)
                SimpleField(
                    name="context_id",
                    type=SearchFieldDataType.String,
                    filterable=True,
                    retrievable=True,
                    facetable=True
                ),
                SearchableField(
                    name="context_name",
                    type=SearchFieldDataType.String,
                    searchable=True,
                    filterable=True,
                    retrievable=True,
                    facetable=True
                ),
                # Timestamps
                SimpleField(
                    name="last_modified",
                    type=SearchFieldDataType.DateTimeOffset,
                    filterable=True,
                    retrievable=True,
                    sortable=True
                ),
                # Chunk information
                SimpleField(
                    name="chunk_index",
                    type=SearchFieldDataType.Int32,
                    filterable=True,
                    retrievable=True,
                    sortable=True
                ),
                # Optional: Custom metadata as JSON string for strategy-specific data
                SimpleField(
                    name="metadata_json",
                    type=SearchFieldDataType.String,
                    retrievable=True
                )
            ]
            
            # Configure vector search
            vector_search = VectorSearch(
                profiles=[
                    VectorSearchProfile(
                        name="vector-profile",
                        algorithm_configuration_name="hnsw-algorithm"
                    )
                ],
                algorithms=[
                    HnswAlgorithmConfiguration(
                        name="hnsw-algorithm",
                        parameters={
                            "metric": "cosine",
                            "m": 4,
                            "efConstruction": 400,
                            "efSearch": 500
                        }
                    )
                ]
            )
            
            # Configure semantic search - matching create_index.py schema
            semantic_search = SemanticSearch(
                configurations=[
                    SemanticConfiguration(
                        name="general-semantic-config",
                        prioritized_fields=SemanticPrioritizedFields(
                            title_field=SemanticField(field_name="title"),
                            content_fields=[
                                SemanticField(field_name="content"),
                                SemanticField(field_name="file_name")
                            ],
                            keywords_fields=[
                                SemanticField(field_name="tags"),
                                SemanticField(field_name="category"),
                                SemanticField(field_name="context_name")
                            ]
                        )
                    )
                ]
            )
            
            # Create the search index
            index = SearchIndex(
                name=self.index_name,
                fields=fields,
                vector_search=vector_search,
                semantic_search=semantic_search
            )
            
            # Create or update the index
            result = self.index_client.create_or_update_index(index)
            print(f"[SUCCESS] Index '{self.index_name}' created successfully!")
            print(f"   Service: {self.service_name}")
            print(f"   Endpoint: {self.endpoint}")
            print(f"   Fields: {len(fields)} (optimized for general-purpose search)")
            print("   Core Features:")
            print(f"   - Vector search enabled ({vector_dimensions} dimensions)")
            print("   - Semantic search configured")
            print("   - File name and metadata search")
            print("   - Context-based grouping (flexible)")
            print("   - Tag and category filtering")
            print("   - Extensible metadata support")
            return True
            
        except Exception as e:
            print(f"[ERROR] Error creating index: {e}")
            return False
    
    def index_exists(self) -> bool:
        """
        Check if the search index exists
        
        Returns:
            bool: True if index exists, False otherwise
        """
        try:
            index = self.index_client.get_index(self.index_name)
            return True
        except ResourceNotFoundError:
            return False
        except Exception as e:
            print(f"[ERROR] Error checking index existence: {e}")
            return False
    
    def delete_index(self) -> bool:
        """
        Delete the search index (use with caution!)
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.index_client.delete_index(self.index_name)
            print(f"🗑️  Index '{self.index_name}' deleted successfully")
            return True
        except Exception as e:
            print(f"[ERROR] Error deleting index: {e}")
            return False
    
    def get_index_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics about the search index
        
        Returns:
            Dict containing detailed index statistics including document counts,
            context information, file types, categories, and other metadata
        """
        try:
            # Get total document count
            results = self.search_client.search("*", select="id", top=0, include_total_count=True)
            document_count = results.get_count()
            
            # Get statistics for all facetable fields in the new schema
            contexts = self.get_unique_field_values("context_id")
            file_types = self.get_unique_field_values("file_type")
            categories = self.get_unique_field_values("category")
            
            # Get context names for better readability
            context_names = self.get_unique_field_values("context_name")
            
            # Build comprehensive stats
            stats = {
                'index_name': self.index_name,
                'service_name': self.service_name,
                'endpoint': self.endpoint,
                'document_count': document_count,
                'context_count': len(contexts),
                'contexts': sorted(contexts) if contexts else [],
                'context_names': sorted(context_names) if context_names else [],
                'file_types': sorted(file_types) if file_types else [],
                'file_type_count': len(file_types),
                'categories': sorted(categories) if categories else [],
                'category_count': len(categories),
                'schema_version': 'flexible_context_v1',
                'features': {
                    'vector_search': True,
                    'semantic_search': True,
                    'hybrid_search': True,
                    'context_filtering': True,
                    'file_metadata': True,
                    'chunk_indexing': True,
                    'timestamp_tracking': True
                }
            }
            
            return stats
            
        except Exception as e:
            print(f"[ERROR] Error getting index stats: {e}")
            return {
                'index_name': self.index_name,
                'error': str(e),
                'document_count': 0,
                'context_count': 0
            }
    
    # ===== DOCUMENT OPERATIONS =====
    
    def upload_search_objects_batch(self, search_objects: List[Dict[str, Any]]) -> Tuple[int, int]:
        """
        Upload search objects directly to Azure Cognitive Search (new format)
        
        Args:
            search_objects: List of search objects ready for upload
            
        Returns:
            Tuple of (successful_uploads, failed_uploads)
        """
        successful = 0
        failed = 0
        
        for i, search_object in enumerate(search_objects, 1):
            print(f"Uploading document {i}/{len(search_objects)}: {search_object.get('file_name', 'Unknown')}")
            try:
                # Upload the search object directly using Azure SDK
                result = self.search_client.upload_documents(documents=[search_object])
                
                if result[0].succeeded:
                    successful += 1
                else:
                    failed += 1
                    print(f"[ERROR] Upload failed: {result[0].error_message}")
                    
            except Exception as e:
                failed += 1
                print(f"[ERROR] Upload failed: {e}")
        
        return successful, failed

    def delete_document(self, document_id: str) -> bool:
        """
        Delete a specific document by ID
        
        Args:
            document_id: The document ID to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            result = self.search_client.delete_documents(documents=[{"id": document_id}])
            
            if result[0].succeeded:
                print(f"[SUCCESS] Document {document_id} deleted successfully")
                return True
            else:
                print(f"[ERROR] Failed to delete document: {result[0].error_message}")
                return False
                
        except Exception as e:
            print(f"[ERROR] Delete failed for {document_id}: {e}")
            return False
    
    def delete_documents_by_filter(self, filters: Dict[str, Any]) -> int:
        """
        Delete documents matching filter criteria
        
        Args:
            filters: Dictionary of field names and values to filter by
            
        Returns:
            Number of documents deleted
        """
        try:
            # Build filter expression using FilterBuilder
            filter_expr = FilterBuilder.build_filter(filters)
            if not filter_expr:
                print("[ERROR] No valid filter provided")
                return 0
            
            # Find all documents matching the filter
            results = self.search_client.search(
                search_text="*",
                filter=filter_expr,
                select="id"
            )
            
            documents_to_delete = [{"id": result["id"]} for result in results]
            
            if not documents_to_delete:
                print(f"[INFO] No documents found matching filter: {filter_expr}")
                return 0
            
            # Delete the documents
            delete_results = self.search_client.delete_documents(documents=documents_to_delete)
            
            successful_deletes = sum(1 for result in delete_results if result.succeeded)
            print(f"[SUCCESS] Deleted {successful_deletes}/{len(documents_to_delete)} documents matching filter: {filter_expr}")
            
            return successful_deletes
            
        except Exception as e:
            print(f"[ERROR] Failed to delete documents: {e}")
            return 0
    
    def delete_documents_by_filename(self, filename: str) -> int:
        """
        Delete all documents that match a specific filename
        
        Args:
            filename: The filename to search for (can be partial or full path)
            
        Returns:
            int: Number of documents deleted
        """
        try:
            from pathlib import Path
            
            # Get all documents to search through them
            results = self.search_client.search(
                search_text="*",
                select="id,file_path,context_id"
            )
            
            documents_to_delete = []
            matched_files = []
            
            filename_lower = filename.lower()
            
            for result in results:
                file_path = result.get("file_path", "")
                file_basename = Path(file_path).name.lower()
                file_path_lower = file_path.lower()
                
                # Check various matching conditions:
                # 1. Exact filename match
                # 2. Filename contained in the basename
                # 3. Filename contained in the full path
                if (file_basename == filename_lower or 
                    filename_lower in file_basename or
                    filename_lower in file_path_lower):
                    
                    documents_to_delete.append({"id": result["id"]})
                    matched_files.append({
                        "id": result["id"],
                        "file_path": file_path,
                        "context_id": result.get("context_id", "")
                    })
            
            if not documents_to_delete:
                print(f"No documents found matching filename: {filename}")
                return 0
            
            # Show what will be deleted
            print(f"[INFO] Found {len(documents_to_delete)} documents matching '{filename}':")
            for file_info in matched_files:
                print(f"   - {file_info['file_path']} (Context ID: {file_info['context_id']})")
            
            # Delete the documents
            delete_results = self.search_client.delete_documents(documents=documents_to_delete)
            
            successful_deletes = sum(1 for result in delete_results if result.succeeded)
            print(f"[SUCCESS] Deleted {successful_deletes}/{len(documents_to_delete)} documents matching filename '{filename}'")
            
            return successful_deletes
            
        except Exception as e:
            print(f"[ERROR] Delete by filename failed for '{filename}': {e}")
            return 0
    
    def delete_all_documents(self) -> int:
        """
        Delete all documents from the index (use with caution!)
        
        Returns:
            int: Number of documents deleted
        """
        try:
            # Get all document IDs
            results = self.search_client.search(search_text="*", select="id")
            documents_to_delete = [{"id": result["id"]} for result in results]
            
            if not documents_to_delete:
                print("No documents found to delete")
                return 0
            
            # Delete in batches of 1000 (Azure Search limit)
            batch_size = 1000
            total_deleted = 0
            
            for i in range(0, len(documents_to_delete), batch_size):
                batch = documents_to_delete[i:i + batch_size]
                delete_results = self.search_client.delete_documents(documents=batch)
                successful_deletes = sum(1 for result in delete_results if result.succeeded)
                total_deleted += successful_deletes
                print(f"Deleted batch {i//batch_size + 1}: {successful_deletes}/{len(batch)} documents")
            
            print(f"[SUCCESS] Total documents deleted: {total_deleted}")
            return total_deleted
            
        except Exception as e:
            print(f"[ERROR] Delete all failed: {e}")
            return 0
    
    # ===== SEARCH OPERATIONS =====
    
    def text_search(self, query: str, filters: Optional[Dict[str, Any]] = None, top: int = 5) -> List[Dict]:
        """
        Perform text-based search
        
        Args:
            query: Search query string
            filters: Optional dictionary of field filters (e.g., {"context_id": "WORK-123"})
            top: Maximum number of results
            
        Returns:
            List of search result dictionaries
        """
        try:
            # Build filter expression using FilterBuilder
            filter_expr = FilterBuilder.build_filter(filters)
            
            results = self.search_client.search(
                search_text=query,
                filter=filter_expr,
                top=top,
                highlight_fields="content",
                select="*"
            )
            
            return [dict(result) for result in results]
            
        except Exception as e:
            print(f"[ERROR] Text search failed: {e}")
            return []
    
    async def vector_search(self, query: str, filters: Optional[Dict[str, Any]] = None, top: int = 5) -> List[Dict]:
        """
        Perform vector-based semantic search
        
        Args:
            query: Search query string
            filters: Optional dictionary of field filters (e.g., {"context_id": "WORK-123"})
            top: Maximum number of results
            
        Returns:
            List of search result dictionaries
        """
        try:
            # Generate embedding for query
            query_embedding = await self.embedding_generator.generate_embedding(query)
            if not query_embedding:
                print("[ERROR] Failed to generate query embedding")
                return []
            
            # Build filter expression using FilterBuilder
            filter_expr = FilterBuilder.build_filter(filters)
            
            # Create vector query
            vector_query = VectorizedQuery(vector=query_embedding, k_nearest_neighbors=top, fields="content_vector")
            
            results = self.search_client.search(
                search_text=None,
                vector_queries=[vector_query],
                filter=filter_expr,
                select="*",
                top=top
            )
            
            return [dict(result) for result in results]
            
        except Exception as e:
            print(f"[ERROR] Vector search failed: {e}")
            return []
    
    async def hybrid_search(self, query: str, filters: Optional[Dict[str, Any]] = None, top: int = 5) -> List[Dict]:
        """
        Perform hybrid search combining text and vector search
        
        Args:
            query: Search query string
            filters: Optional dictionary of field filters (e.g., {"context_id": "WORK-123"})
            top: Maximum number of results
            
        Returns:
            List of search result dictionaries
        """
        try:
            # Generate embedding for query
            query_embedding = await self.embedding_generator.generate_embedding(query)
            if not query_embedding:
                print("[ERROR] Failed to generate query embedding, falling back to text search")
                return self.text_search(query, filters, top)
            
            # Build filter expression using FilterBuilder
            filter_expr = FilterBuilder.build_filter(filters)
            
            # Create vector query
            vector_query = VectorizedQuery(vector=query_embedding, k_nearest_neighbors=top, fields="content_vector")
            
            results = self.search_client.search(
                search_text=query,
                vector_queries=[vector_query],
                filter=filter_expr,
                select="*",
                top=top
            )
            
            return [dict(result) for result in results]
            
        except Exception as e:
            print(f"[ERROR] Hybrid search failed: {e}")
            return []
    
    def semantic_search(self, query: str, filters: Optional[Dict[str, Any]] = None, top: int = 5) -> List[Dict]:
        """
        Perform semantic search using Azure's semantic capabilities
        
        Args:
            query: Search query string
            filters: Optional dictionary of field filters (e.g., {"context_id": "WORK-123"})
            top: Maximum number of results
            
        Returns:
            List of search result dictionaries
        """
        try:
            # Build filter expression using FilterBuilder
            filter_expr = FilterBuilder.build_filter(filters)
            
            results = self.search_client.search(
                search_text=query,
                filter=filter_expr,
                query_type="semantic",
                semantic_configuration_name="general-semantic-config",
                top=top,
                select="*"
            )
            
            return [dict(result) for result in results]
            
        except Exception as e:
            print(f"[ERROR] Semantic search failed: {e}")
            return []
    
    # ===== UTILITY METHODS =====
    
    def get_unique_field_values(self, field_name: str) -> List[str]:
        """
        Get unique values for any facetable field
        
        Args:
            field_name: Name of the field to get unique values for
            
        Returns:
            List of unique values for the field
        """
        try:
            results = self.search_client.search(
                search_text="*",
                facets=[field_name],
                top=0
            )
            
            unique_values = []
            if hasattr(results, 'get_facets') and results.get_facets():
                facets = results.get_facets()
                if field_name in facets:
                    unique_values = [facet['value'] for facet in facets[field_name]]
            
            return sorted(unique_values)
            
        except Exception as e:
            print(f"[ERROR] Failed to get unique values for field '{field_name}': {e}")
            return []
    
    def get_document_count(self) -> int:
        """
        Get total number of documents in the index
        
        Returns:
            Number of documents
        """
        try:
            results = self.search_client.search("*", top=0, include_total_count=True)
            return results.get_count() or 0
        except Exception as e:
            print(f"[ERROR] Error getting document count: {e}")
            return 0
    
    def test_connection(self) -> bool:
        """
        Test connection to Azure Cognitive Search
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Try to get index stats
            stats = self.get_index_stats()
            return bool(stats)
        except Exception as e:
            print(f"[ERROR] Connection test failed: {e}")
            return False
    
    def print_search_results(self, results: List[Dict], title: str = "Search Results"):
        """
        Print search results in a formatted way
        
        Args:
            results: List of search result dictionaries
            title: Title for the results display
        """
        if not results:
            print(f"[SEARCH] {title}: No results found")
            return
        
        print(f"\n[SEARCH] {title} ({len(results)} results)")
        print("=" * 60)
        
        for i, result in enumerate(results, 1):
            print(f"\n[DOCUMENT] Result {i}:")
            print(f"   ID: {result.get('id', 'N/A')}")
            print(f"   Title: {result.get('title', 'Untitled')}")
            print(f"   Context ID: {result.get('context_id', 'N/A')}")
            print(f"   File: {result.get('file_path', 'N/A')}")
            
            if '@search.score' in result:
                print(f"   Score: {result['@search.score']:.3f}")
            
            content = result.get('content', '')
            if content:
                content_preview = content[:200] + "..." if len(content) > 200 else content
                print(f"   Content: {content_preview}")


# Convenience function to create a search service instance
def get_azure_search_service(service_name: Optional[str] = None,
                           admin_key: Optional[str] = None,
                           index_name: Optional[str] = None) -> AzureCognitiveSearch:
    """
    Factory function to create an AzureCognitiveSearch instance
    
    Args:
        service_name: Azure Search service name (from env if not provided)
        admin_key: Azure Search admin key (from env if not provided)  
        index_name: Search index name (from env if not provided)
        
    Returns:
        AzureCognitiveSearch instance
    """
    return AzureCognitiveSearch(service_name, admin_key, index_name)


if __name__ == "__main__":
    # Simple test of the Azure Cognitive Search service
    try:
        search_service = get_azure_search_service()
        
        print("🧪 Testing Azure Cognitive Search Service")
        print("=" * 50)
        
        # Test connection
        if search_service.test_connection():
            print("[SUCCESS] Connection successful")
            
            # Get comprehensive stats
            stats = search_service.get_index_stats()
            print(f"[SUMMARY] Index Stats:")
            print(f"   Documents: {stats.get('document_count', 0)}")
            print(f"   Contexts: {stats.get('context_count', 0)}")
            print(f"   File Types: {stats.get('file_type_count', 0)}")
            print(f"   Categories: {stats.get('category_count', 0)}")
            print(f"   Schema: {stats.get('schema_version', 'unknown')}")
            
        else:
            print("[ERROR] Connection failed")
            
    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
