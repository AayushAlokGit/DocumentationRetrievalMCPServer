"""
Azure Cognitive Search Index Creation
Creates the search index with vector search capabilities
"""

import os
import json
from dotenv import load_dotenv
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
from azure.core.credentials import AzureKeyCredential

# Load environment variables
load_dotenv()


def create_search_index():
    """Create the Azure Cognitive Search index with vector search capabilities"""
    
    # Get configuration from environment
    service_name = os.getenv('AZURE_SEARCH_SERVICE')
    admin_key = os.getenv('AZURE_SEARCH_KEY')
    index_name = os.getenv('AZURE_SEARCH_INDEX', 'work-items-index')
    
    # Initialize the search index client
    index_client = SearchIndexClient(
        endpoint=f"https://{service_name}.search.windows.net",
        credential=AzureKeyCredential(admin_key)
    )
    
    # Define the fields for the index - optimized for general-purpose document search
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
            vector_search_dimensions=1536,
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
    
    # Configure semantic search - simplified for general-purpose use
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
        name=index_name,
        fields=fields,
        vector_search=vector_search,
        semantic_search=semantic_search
    )
    
    try:
        # Create or update the index
        result = index_client.create_or_update_index(index)
        print(f"[SUCCESS] Optimized document search index '{index_name}' created successfully!")
        print(f"   Service: {service_name}")
        print(f"   Endpoint: https://{service_name}.search.windows.net")
        print(f"   Fields: {len(fields)} (optimized for general-purpose search)")
        print("   Core Features:")
        print("   - Vector search enabled (1536 dimensions)")
        print("   - Semantic search configured")
        print("   - File name and metadata search")
        print("   - Context-based grouping (flexible)")
        print("   - Tag and category filtering")
        print("   - Extensible metadata support")
        return True
        
    except Exception as e:
        print(f"[ERROR] Error creating index: {e}")
        return False


def check_index_exists():
    """Check if the search index already exists"""
    
    service_name = os.getenv('AZURE_SEARCH_SERVICE')
    admin_key = os.getenv('AZURE_SEARCH_KEY')
    index_name = os.getenv('AZURE_SEARCH_INDEX', 'work-items-index')
    
    index_client = SearchIndexClient(
        endpoint=f"https://{service_name}.search.windows.net",
        credential=AzureKeyCredential(admin_key)
    )
    
    try:
        index = index_client.get_index(index_name)
        print(f"[SUCCESS] Index '{index_name}' already exists")
        print(f"   Fields: {len(index.fields)}")
        return True
    except Exception:
        print(f"[ERROR] Index '{index_name}' does not exist")
        return False


def delete_index():
    """Delete the search index (use with caution!)"""
    
    service_name = os.getenv('AZURE_SEARCH_SERVICE')
    admin_key = os.getenv('AZURE_SEARCH_KEY')
    index_name = os.getenv('AZURE_SEARCH_INDEX', 'work-items-index')
    
    index_client = SearchIndexClient(
        endpoint=f"https://{service_name}.search.windows.net",
        credential=AzureKeyCredential(admin_key)
    )
    
    try:
        index_client.delete_index(index_name)
        print(f"🗑️  Index '{index_name}' deleted successfully")
        return True
    except Exception as e:
        print(f"[ERROR] Error deleting index: {e}")
        return False


def main():
    """Main function to create the search index"""
    
    print("Azure Cognitive Search Index Setup")
    print("=" * 40)
    
    # Check if index exists
    if check_index_exists():
        response = input("Index already exists. Recreate? (y/N): ")
        if response.lower() == 'y':
            print("Deleting existing index...")
            delete_index()
        else:
            print("Keeping existing index.")
            return
    
    # Create the index
    print("Creating search index...")
    success = create_search_index()
    
    if success:
        print("\n🎉 Setup complete! You can now upload documents.")
    else:
        print("\n[ERROR] Setup failed. Check your credentials and try again.")


if __name__ == "__main__":
    main()
