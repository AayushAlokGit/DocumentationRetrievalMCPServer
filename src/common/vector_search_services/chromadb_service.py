"""
ChromaDB Service Implementation
=============================

Vector-only search service with persistent storage
"""

import chromadb
from chromadb.config import Settings
import os
from typing import List, Dict, Any, Optional, Tuple
import asyncio
from datetime import datetime

from ..embedding_services.embedding_service_factory import get_embedding_generator
from .vector_search_interface import IVectorSearchService


class ChromaDBFilterBuilder:
    """
    Simplified ChromaDB filter builder for query construction
    """

    @staticmethod
    def build_filter(filters: Dict[str, Any]) -> Optional[Dict]:
        """
        Convert filter dictionary to ChromaDB where clause format

        Args:
            filters: Filter dictionary with field names and values

        Returns:
            ChromaDB where clause dictionary or None

        Examples:
            {"context_name": "docs"} -> {"context_name": "docs"}
            {"file_type": ["pdf", "docx"]} -> {"file_type": {"$in": ["pdf", "docx"]}}
            {"priority": {"gte": 5}} -> {"priority": {"$gte": 5}}
        """
        if not filters:
            return None

        chromadb_where = {}
        filter_conditions = []
        
        for field, value in filters.items():
            if value is None:
                continue
                
            # Handle different value types
            if isinstance(value, list):
                # Multiple values - use $in
                filter_conditions.append({field: {"$in": value}})
            elif isinstance(value, dict):
                # Operator dictionary - ensure $ prefix
                ops = {}
                for op, val in value.items():
                    ops[f"${op}" if not op.startswith('$') else op] = val
                filter_conditions.append({field: ops})
            else:
                # Simple equality
                filter_conditions.append({field: value})

        # If multiple conditions, combine with $and
        if len(filter_conditions) > 1:
            return {"$and": filter_conditions}
        elif len(filter_conditions) == 1:
            return filter_conditions[0]
        else:
            return None

    @staticmethod
    def combine_filters(*filter_dicts: Dict) -> Optional[Dict]:
        """
        Combine multiple filter dictionaries with AND logic

        Args:
            *filter_dicts: Variable number of filter dictionaries

        Returns:
            Combined ChromaDB filter or None
        """
        valid_filters = [f for f in filter_dicts if f]
        
        if not valid_filters:
            return None
        elif len(valid_filters) == 1:
            return valid_filters[0]
        else:
            return {"$and": valid_filters}


class ChromaDBService(IVectorSearchService):
    """
    ChromaDB service implementation for vector search

    Provides vector-only search with document management capabilities
    """

    def __init__(self,
                 collection_name: str = None,
                 persist_directory: str = None):
        """
        Initialize ChromaDB service with persistent storage

        Args:
            collection_name: Name of the ChromaDB collection (from env if None)
            persist_directory: Directory for persistent storage (from env if None)
        """
        # Configuration from environment variables
        self.collection_name = collection_name or os.getenv('CHROMADB_COLLECTION_NAME', 'documentation_collection')
        self.persist_directory = persist_directory or os.getenv('CHROMADB_PERSIST_DIRECTORY', './chromadb_data')

        # Lazy initialization for embedding service
        self._embedding_generator = None

        # Initialize ChromaDB client with persistence
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        # Get or create collection
        try:
            self.collection = self.client.get_collection(name=self.collection_name)
            print(f"[INFO] Connected to existing ChromaDB collection: {self.collection_name}")
        except Exception:
            # Collection doesn't exist, create it
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "Documentation retrieval collection"}
            )
            print(f"[INFO] Created new ChromaDB collection: {self.collection_name}")

    @property
    def embedding_generator(self):
        """Lazy initialization of embedding generator"""
        if self._embedding_generator is None:
            self._embedding_generator = get_embedding_generator(provider="local")
        return self._embedding_generator

    def test_connection(self) -> bool:
        """Test ChromaDB connection and collection access"""
        try:
            # Try to count documents in collection
            count = self.collection.count()
            print(f"[SUCCESS] ChromaDB connection successful. Documents: {count}")
            return True
        except Exception as e:
            print(f"[ERROR] ChromaDB connection failed: {e}")
            return False

    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get collection statistics

        Returns:
            Dictionary with collection statistics
        """
        try:
            # Get basic stats
            document_count = self.collection.count()

            # Get sample documents to analyze contexts
            sample_results = self.collection.get(limit=100)
            contexts = set()

            if sample_results['metadatas']:
                for metadata in sample_results['metadatas']:
                    if metadata and 'context_name' in metadata:
                        contexts.add(metadata['context_name'])

            return {
                'collection_name': self.collection_name,
                'document_count': document_count,
                'context_count': len(contexts),
                'storage_path': self.persist_directory
            }

        except Exception as e:
            print(f"[ERROR] Failed to get index stats: {e}")
            return {
                'collection_name': self.collection_name,
                'document_count': 0,
                'context_count': 0,
                'storage_path': self.persist_directory
            }

    def get_document_count(self) -> int:
        """
        Get total number of documents in the collection
        
        Returns:
            Number of documents
        """
        try:
            return self.collection.count()
        except Exception as e:
            print(f"[ERROR] Error getting document count: {e}")
            return 0

    # ===== DOCUMENT UPLOAD OPERATIONS =====

    def upload_search_objects_batch(self, search_objects: List[Dict[str, Any]]) -> Tuple[int, int]:
        """
        Upload search objects in batch to ChromaDB

        Converts document objects to ChromaDB format automatically

        Args:
            search_objects: List of search objects to upload

        Returns:
            Tuple of (successful_uploads, failed_uploads)
        """
        if not search_objects:
            return 0, 0

        try:
            # Convert document format to ChromaDB format
            ids = []
            documents = []  # Text content
            embeddings = []  # Vector embeddings
            metadatas = []  # Metadata dicts

            for obj in search_objects:
                # Extract required fields
                doc_id = obj.get('id', '')
                content = obj.get('content', '')
                embedding = obj.get('content_vector', [])

                if not doc_id or not content or not embedding:
                    continue  # Skip invalid objects

                ids.append(doc_id)
                documents.append(content)
                embeddings.append(embedding)

                # Create metadata (exclude ChromaDB reserved fields)
                metadata = {k: v for k, v in obj.items()
                          if k not in ['id', 'content', 'content_vector']
                          and v is not None}
                metadatas.append(metadata)

            # Batch upload to ChromaDB
            if ids:
                self.collection.add(
                    ids=ids,
                    documents=documents,
                    embeddings=embeddings,
                    metadatas=metadatas
                )
                print(f"[SUCCESS] Uploaded {len(ids)} documents to ChromaDB")
                return len(ids), 0
            else:
                return 0, len(search_objects)

        except Exception as e:
            print(f"[ERROR] Batch upload failed: {e}")
            return 0, len(search_objects)

    def delete_document(self, document_id: str) -> bool:
        """Delete single document by ID"""
        try:
            self.collection.delete(ids=[document_id])
            return True
        except Exception as e:
            print(f"[ERROR] Delete failed for {document_id}: {e}")
            return False

    def delete_documents_by_filter(self, filters: Dict[str, Any]) -> int:
        """Delete documents matching filter criteria"""
        try:
            # ChromaDB requires getting IDs first, then deleting
            chromadb_filters = self._convert_filters_to_chromadb(filters)
            results = self.collection.get(where=chromadb_filters)
            ids_to_delete = results.get('ids', [])

            if ids_to_delete:
                self.collection.delete(ids=ids_to_delete)
                return len(ids_to_delete)
            return 0

        except Exception as e:
            print(f"[ERROR] Filter-based delete failed: {e}")
            return 0

    async def delete_documents(self, document_ids: List[str]) -> int:
        """Delete multiple documents by their IDs"""
        try:
            if not document_ids:
                return 0
                
            self.collection.delete(ids=document_ids)
            return len(document_ids)
            
        except Exception as e:
            print(f"[ERROR] Multiple document delete failed: {e}")
            return 0

    # ===== SEARCH OPERATIONS =====

    def get_documents_by_filter(self, filters: Dict[str, Any]) -> List[Dict]:
        """Get documents matching filter criteria without vector search"""
        try:
            # Convert filters to ChromaDB format
            chromadb_filters = self._convert_filters_to_chromadb(filters) if filters else None

            # Get documents using ChromaDB collection get method
            results = self.collection.get(
                where=chromadb_filters,
                include=['metadatas', 'documents']
            )

            # Format results to match expected structure
            formatted_results = []
            if results and 'ids' in results:
                for i, doc_id in enumerate(results['ids']):
                    doc_data = {
                        'id': doc_id,
                        'content': results['documents'][i] if i < len(results['documents']) else '',
                        'metadata': results['metadatas'][i] if i < len(results['metadatas']) else {}
                    }
                    
                    # Extract common metadata fields
                    metadata = doc_data['metadata']
                    doc_data.update({
                        'file_name': metadata.get('file_name', ''),
                        'context_name': metadata.get('context_name', ''),
                        'file_path': metadata.get('file_path', ''),
                        'title': metadata.get('title', ''),
                        'chunk_index': metadata.get('chunk_index', 0)
                    })
                    
                    formatted_results.append(doc_data)

            return formatted_results

        except Exception as e:
            print(f"[ERROR] Get documents by filter failed: {e}")
            return []

    async def vector_search(self, query: str, filters: Optional[Dict[str, Any]] = None, top: int = 5) -> List[Dict]:
        """Core vector search implementation"""
        try:
            # Generate embedding for query
            query_embedding = await self.embedding_generator.generate_embedding(query)

            # Convert filters to ChromaDB format
            chromadb_filters = self._convert_filters_to_chromadb(filters) if filters else None

            # Perform vector search
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top,
                where=chromadb_filters
            )

            return self._format_search_results(results)

        except Exception as e:
            print(f"[ERROR] Vector search failed: {e}")
            return []

    # ===== UTILITY METHODS =====

    def _convert_filters_to_chromadb(self, filters: Dict[str, Any]) -> Optional[Dict]:
        """
        Delegates filter conversion to ChromaDBFilterBuilder for ChromaDB where clause format.

        Args:
            filters: Filter dictionary with field names and values

        Returns:
            ChromaDB where clause dictionary
        """
        if not filters:
            return None
        return ChromaDBFilterBuilder.build_filter(filters)

    def _format_search_results(self, chromadb_results: Dict) -> List[Dict]:
        """
        Format ChromaDB results for consistent API response

        Args:
            chromadb_results: Raw results from ChromaDB query

        Returns:
            List of formatted document dictionaries
        """
        formatted_results = []

        if not chromadb_results or 'ids' not in chromadb_results:
            return formatted_results

        # ChromaDB returns nested lists, flatten them
        ids = chromadb_results['ids'][0] if chromadb_results['ids'] else []
        documents = chromadb_results['documents'][0] if chromadb_results['documents'] else []
        metadatas = chromadb_results['metadatas'][0] if chromadb_results['metadatas'] else []
        distances = chromadb_results['distances'][0] if chromadb_results['distances'] else []

        # Combine into result documents
        for i, doc_id in enumerate(ids):
            doc = {
                'id': doc_id,
                'content': documents[i] if i < len(documents) else '',
            }

            # Add metadata fields
            if i < len(metadatas) and metadatas[i]:
                doc.update(metadatas[i])

            # Add search relevance score (convert distance to similarity)
            if i < len(distances):
                # Convert distance to similarity score (lower distance = higher similarity)
                score = max(0.0, 1.0 - distances[i])  # Simple conversion
                doc['@search.score'] = round(score, 4)  # Search relevance score
            else:
                doc['@search.score'] = 1.0

            formatted_results.append(doc)

        return formatted_results

    def get_unique_field_values(self, field_name: str, max_values: int = 1000) -> List[str]:
        """
        Get unique values for any field by querying all documents
        
        Args:
            field_name: Name of the field to get unique values for
            max_values: Maximum number of unique values to return (default: 1000)
            
        Returns:
            List of unique values for the field
        """
        try:
            # Get all documents with their metadata
            all_results = self.collection.get()
            
            unique_values_set = set()
            
            # Extract unique values from metadata
            if all_results['metadatas']:
                for metadata in all_results['metadatas']:
                    if metadata and field_name in metadata:
                        value = metadata[field_name]
                        if value is not None:
                            if isinstance(value, list):
                                # Handle array fields (like tags)
                                unique_values_set.update(str(item).strip() for item in value if item is not None)
                            elif isinstance(value, str):
                                # Handle comma-separated string fields (like tags stored as strings)
                                if ',' in value:
                                    # Split comma-separated values
                                    values = [v.strip() for v in value.split(',') if v.strip()]
                                    unique_values_set.update(values)
                                else:
                                    unique_values_set.add(value.strip())
                            else:
                                # Handle single value fields
                                unique_values_set.add(str(value).strip())
            
            # Convert to sorted list and apply limit
            unique_values = sorted(list(unique_values_set))[:max_values]
            
            print(f"[DEBUG] Found {len(unique_values)} unique values for '{field_name}'")
            return unique_values
            
        except Exception as e:
            print(f"[ERROR] Failed to get unique values for field '{field_name}': {e}")
            return []


def get_chromadb_service(collection_name: Optional[str] = None,
                              persist_directory: Optional[str] = None) -> ChromaDBService:
    """
    Factory function to create a ChromaDBService instance
    
    Args:
        collection_name: Collection name (from env if not provided)
        persist_directory: Directory for persistent storage (from env if not provided)
        
    Returns:
        ChromaDBService instance
    """
    return ChromaDBService(collection_name, persist_directory)
