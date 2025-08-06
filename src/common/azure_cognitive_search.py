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

# Import embedding service
from common.embedding_service import get_embedding_generator

# Load environment variables
load_dotenv()


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
            # Define the fields for the index
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
                SimpleField(
                    name="file_path",
                    type=SearchFieldDataType.String,
                    filterable=True,
                    retrievable=True,
                    facetable=True
                ),
                SearchableField(
                    name="title",
                    type=SearchFieldDataType.String,
                    searchable=True,
                    retrievable=True
                ),
                SimpleField(
                    name="work_item_id",
                    type=SearchFieldDataType.String,
                    filterable=True,
                    retrievable=True,
                    facetable=True
                ),
                SearchableField(
                    name="tags",
                    type=SearchFieldDataType.String,
                    searchable=True,
                    filterable=True,
                    retrievable=True,
                    facetable=True
                ),
                SimpleField(
                    name="last_modified",
                    type=SearchFieldDataType.DateTimeOffset,
                    filterable=True,
                    retrievable=True,
                    sortable=True
                ),
                SimpleField(
                    name="chunk_index",
                    type=SearchFieldDataType.Int32,
                    filterable=True,
                    retrievable=True,
                    sortable=True
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
            
            # Configure semantic search
            semantic_search = SemanticSearch(
                configurations=[
                    SemanticConfiguration(
                        name="semantic-config",
                        prioritized_fields=SemanticPrioritizedFields(
                            title_field=SemanticField(field_name="title"),
                            content_fields=[
                                SemanticField(field_name="content")
                            ],
                            keywords_fields=[
                                SemanticField(field_name="tags")
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
            print(f"   Fields: {len(fields)}")
            print("   Features:")
            print(f"   - Vector search enabled ({vector_dimensions} dimensions)")
            print("   - Semantic search configured")
            print("   - Work item filtering and faceting")
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
        Get statistics about the search index
        
        Returns:
            Dict containing index statistics
        """
        try:
            # Get document count
            results = self.search_client.search("*", select="id", top=0, include_total_count=True)
            document_count = results.get_count()
            
            # Get work items
            work_items = self.get_work_items()
            
            return {
                'index_name': self.index_name,
                'document_count': document_count,
                'work_item_count': len(work_items),
                'work_items': work_items,
                'service_name': self.service_name,
                'endpoint': self.endpoint
            }
        except Exception as e:
            print(f"[ERROR] Error getting index stats: {e}")
            return {}
    
    # ===== DOCUMENT OPERATIONS =====
    
    def upload_document(self, document: Dict[str, Any]) -> bool:
        """
        Upload a single processed document with chunks to the search index
        
        Args:
            document: Dictionary containing document data with chunks and embeddings
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Prepare document chunks for upload
            search_documents = []
            
            for i, (chunk, embedding) in enumerate(zip(document['chunks'], document['embeddings'])):
                file_name = Path(document['file_path']).stem
                # Create a unique document ID using file path hash
                file_hash = hashlib.md5(document['file_path'].encode()).hexdigest()[:8]
                doc_id = f"{file_hash}_{i}"
                
                # Validate embedding
                if not self.embedding_generator.validate_embedding(embedding):
                    print(f"[ERROR] Invalid embedding for chunk {i}, skipping...")
                    continue
                
                # Create search document
                tags = document['metadata'].get('tags', [])
                tags_str = ', '.join(tags) if isinstance(tags, list) else str(tags) if tags else ''
                
                search_doc = {
                    'id': doc_id,
                    'content': chunk,
                    'content_vector': embedding,
                    'file_path': document['file_path'],
                    'title': document['metadata'].get('title', file_name),
                    'work_item_id': document['metadata'].get('work_item_id', 'Unknown'),
                    'tags': tags_str,
                    'last_modified': document['metadata'].get('last_modified', datetime.utcnow().isoformat() + 'Z'),
                    'chunk_index': i
                }
                
                search_documents.append(search_doc)
            
            if not search_documents:
                print("[ERROR] No valid documents to upload")
                return False
            
            # Upload to search index
            upload_result = self.search_client.upload_documents(documents=search_documents)
            
            # Check results
            success_count = 0
            for result in upload_result:
                if result.succeeded:
                    success_count += 1
                else:
                    print(f"[ERROR] Failed to upload chunk {result.key}: {result.error_message}")
            
            print(f"[SUCCESS] Uploaded {success_count}/{len(search_documents)} chunks successfully")
            return success_count > 0
            
        except Exception as e:
            print(f"[ERROR] Upload failed: {e}")
            return False
    
    def upload_documents_batch(self, documents: List[Dict[str, Any]]) -> Tuple[int, int]:
        """
        Upload multiple documents in batch
        
        Args:
            documents: List of document dictionaries
            
        Returns:
            Tuple of (successful_uploads, total_documents)
        """
        successful = 0
        total = len(documents)
        
        for i, document in enumerate(documents, 1):
            print(f"Uploading document {i}/{total}: {Path(document['file_path']).name}")
            if self.upload_document(document):
                successful += 1
        
        return successful, total
    
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
    
    def delete_documents_by_work_item(self, work_item_id: str) -> int:
        """
        Delete all documents for a specific work item
        
        Args:
            work_item_id: The work item ID
            
        Returns:
            int: Number of documents deleted
        """
        try:
            # Find all documents for the work item
            results = self.search_client.search(
                search_text="*",
                filter=f"work_item_id eq '{work_item_id}'",
                select="id"
            )
            
            documents_to_delete = [{"id": result["id"]} for result in results]
            
            if not documents_to_delete:
                print(f"No documents found for work item: {work_item_id}")
                return 0
            
            # Delete the documents
            delete_results = self.search_client.delete_documents(documents=documents_to_delete)
            
            successful_deletes = sum(1 for result in delete_results if result.succeeded)
            print(f"[SUCCESS] Deleted {successful_deletes}/{len(documents_to_delete)} documents for work item {work_item_id}")
            
            return successful_deletes
            
        except Exception as e:
            print(f"[ERROR] Bulk delete failed for work item {work_item_id}: {e}")
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
                select="id,file_path,work_item_id"
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
                        "work_item_id": result.get("work_item_id", "")
                    })
            
            if not documents_to_delete:
                print(f"No documents found matching filename: {filename}")
                return 0
            
            # Show what will be deleted
            print(f"[INFO] Found {len(documents_to_delete)} documents matching '{filename}':")
            for file_info in matched_files:
                print(f"   - {file_info['file_path']} (Work Item: {file_info['work_item_id']})")
            
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
    
    def text_search(self, query: str, work_item_id: Optional[str] = None, top: int = 5) -> List[Dict]:
        """
        Perform text-based search
        
        Args:
            query: Search query string
            work_item_id: Optional work item filter
            top: Maximum number of results
            
        Returns:
            List of search result dictionaries
        """
        try:
            # Build filter if work item specified
            filter_expr = f"work_item_id eq '{work_item_id}'" if work_item_id else None
            
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
    
    async def vector_search(self, query: str, work_item_id: Optional[str] = None, top: int = 5) -> List[Dict]:
        """
        Perform vector-based semantic search
        
        Args:
            query: Search query string
            work_item_id: Optional work item filter
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
            
            # Build filter if work item specified
            filter_expr = f"work_item_id eq '{work_item_id}'" if work_item_id else None
            
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
    
    async def hybrid_search(self, query: str, work_item_id: Optional[str] = None, top: int = 5) -> List[Dict]:
        """
        Perform hybrid search combining text and vector search
        
        Args:
            query: Search query string
            work_item_id: Optional work item filter
            top: Maximum number of results
            
        Returns:
            List of search result dictionaries
        """
        try:
            # Generate embedding for query
            query_embedding = await self.embedding_generator.generate_embedding(query)
            if not query_embedding:
                print("[ERROR] Failed to generate query embedding, falling back to text search")
                return self.text_search(query, work_item_id, top)
            
            # Build filter if work item specified
            filter_expr = f"work_item_id eq '{work_item_id}'" if work_item_id else None
            
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
    
    def semantic_search(self, query: str, work_item_id: Optional[str] = None, top: int = 5) -> List[Dict]:
        """
        Perform semantic search using Azure's semantic capabilities
        
        Args:
            query: Search query string
            work_item_id: Optional work item filter
            top: Maximum number of results
            
        Returns:
            List of search result dictionaries
        """
        try:
            # Build filter if work item specified
            filter_expr = f"work_item_id eq '{work_item_id}'" if work_item_id else None
            
            results = self.search_client.search(
                search_text=query,
                filter=filter_expr,
                query_type="semantic",
                semantic_configuration_name="semantic-config",
                top=top,
                select="*"
            )
            
            return [dict(result) for result in results]
            
        except Exception as e:
            print(f"[ERROR] Semantic search failed: {e}")
            return []
    
    # ===== UTILITY METHODS =====
    
    def get_work_items(self) -> List[str]:
        """
        Get list of all unique work item IDs in the index
        
        Returns:
            List of work item IDs
        """
        try:
            results = self.search_client.search(
                search_text="*",
                facets=["work_item_id"],
                top=0
            )
            
            work_items = []
            if hasattr(results, 'get_facets') and results.get_facets():
                facets = results.get_facets()
                if 'work_item_id' in facets:
                    work_items = [facet['value'] for facet in facets['work_item_id']]
            
            return sorted(work_items)
            
        except Exception as e:
            print(f"[ERROR] Error getting work items: {e}")
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
    
    def search_by_file_path(self, file_path: str) -> List[Dict]:
        """
        Find documents by file path
        
        Args:
            file_path: File path to search for
            
        Returns:
            List of matching documents
        """
        try:
            results = self.search_client.search(
                search_text="*",
                filter=f"file_path eq '{file_path}'",
                select="*"
            )
            
            return [dict(result) for result in results]
            
        except Exception as e:
            print(f"[ERROR] Error searching by file path: {e}")
            return []
    
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
            print(f"   Work Item: {result.get('work_item_id', 'N/A')}")
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
            
            # Get stats
            stats = search_service.get_index_stats()
            print(f"[SUMMARY] Index Stats:")
            print(f"   Documents: {stats.get('document_count', 0)}")
            print(f"   Work Items: {stats.get('work_item_count', 0)}")
            
        else:
            print("[ERROR] Connection failed")
            
    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
