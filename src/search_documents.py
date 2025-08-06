"""
Search and Query Azure Cognitive Search
Test search functionality and query documents
"""

import os
import asyncio
from dotenv import load_dotenv
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from src.openai_service import get_openai_service

# Load environment variables
load_dotenv()


class DocumentSearcher:
    def __init__(self):
        # Configuration from environment
        self.service_name = os.getenv('AZURE_SEARCH_SERVICE')
        self.admin_key = os.getenv('AZURE_SEARCH_KEY')
        self.index_name = os.getenv('AZURE_SEARCH_INDEX', 'work-items-index')
        self.azure_openai_endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
        self.azure_openai_key = os.getenv('AZURE_OPENAI_KEY')
        self.embedding_deployment = os.getenv('EMBEDDING_DEPLOYMENT', 'text-embedding-ada-002')
        
        # Initialize clients
        self.search_client = SearchClient(
            endpoint=f"https://{self.service_name}.search.windows.net",
            index_name=self.index_name,
            credential=AzureKeyCredential(self.admin_key)
        )
        
        self.openai_service = get_openai_service()
    
    async def get_query_embedding(self, query: str):
        """Generate embedding for search query"""
        try:
            return await self.openai_service.generate_embedding(query)
        except Exception as e:
            print(f"Error generating query embedding: {e}")
            return None
    
    async def vector_search(self, query: str, work_item_id: str = None, top_k: int = 5):
        """Perform vector search"""
        query_embedding = await self.get_query_embedding(query)
        
        if not query_embedding:
            return None
        
        # Build search parameters
        search_params = {
            "search_text": None,  # Pure vector search
            "vector_queries": [{
                "vector": query_embedding,
                "k_nearest_neighbors": top_k,
                "fields": "content_vector"
            }],
            "select": ["id", "content", "title", "work_item_id", "file_path", "tags", "chunk_index"],
            "top": top_k
        }
        
        # Add work item filter if specified
        if work_item_id:
            search_params["filter"] = f"work_item_id eq '{work_item_id}'"
        
        try:
            results = self.search_client.search(**search_params)
            return list(results)
        except Exception as e:
            print(f"Error performing vector search: {e}")
            return None
    
    async def hybrid_search(self, query: str, work_item_id: str = None, top_k: int = 5):
        """Perform hybrid search (text + vector)"""
        query_embedding = await self.get_query_embedding(query)
        
        if not query_embedding:
            return None
        
        # Build search parameters
        search_params = {
            "search_text": query,
            "vector_queries": [{
                "vector": query_embedding,
                "k_nearest_neighbors": top_k,
                "fields": "content_vector"
            }],
            "select": ["id", "content", "title", "work_item_id", "file_path", "tags", "chunk_index"],
            "top": top_k
        }
        
        # Add work item filter if specified
        if work_item_id:
            search_params["filter"] = f"work_item_id eq '{work_item_id}'"
        
        try:
            results = self.search_client.search(**search_params)
            return list(results)
        except Exception as e:
            print(f"Error performing hybrid search: {e}")
            return None
    
    def text_search(self, query: str, work_item_id: str = None, top_k: int = 5):
        """Perform traditional text search"""
        search_params = {
            "search_text": query,
            "select": ["id", "content", "title", "work_item_id", "file_path", "tags", "chunk_index"],
            "top": top_k,
            "highlight_fields": "content"
        }
        
        # Add work item filter if specified
        if work_item_id:
            search_params["filter"] = f"work_item_id eq '{work_item_id}'"
        
        try:
            results = self.search_client.search(**search_params)
            return list(results)
        except Exception as e:
            print(f"Error performing text search: {e}")
            return None
    
    def get_work_items(self):
        """Get list of all work item IDs"""
        try:
            results = self.search_client.search(
                search_text="*",
                facets=["work_item_id"],
                top=1
            )
            
            # Extract work items from facets
            facets = results.get_facets()
            if "work_item_id" in facets:
                work_items = [facet["value"] for facet in facets["work_item_id"]]
                return work_items
            return []
        except Exception as e:
            print(f"Error getting work items: {e}")
            return []
    
    def get_document_count(self):
        """Get total number of documents in the index"""
        try:
            results = self.search_client.search(
                search_text="*",
                include_total_count=True,
                top=0
            )
            return results.get_count()
        except Exception as e:
            print(f"Error getting document count: {e}")
            return 0


def print_search_results(results, title="Search Results"):
    """Pretty print search results"""
    if not results:
        print("No results found.")
        return
    
    print(f"\n{title}")
    print("=" * 50)
    
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result.get('title', 'Untitled')}")
        print(f"   Work Item: {result.get('work_item_id', 'N/A')}")
        print(f"   File: {result.get('file_path', 'N/A')}")
        print(f"   Chunk: {result.get('chunk_index', 'N/A')}")
        print(f"   Score: {result.get('@search.score', 'N/A')}")
        
        # Show content preview
        content = result.get('content', '')
        content_preview = content[:200] + "..." if len(content) > 200 else content
        print(f"   Content: {content_preview}")
        
        # Show tags
        tags = result.get('tags', [])
        if tags:
            print(f"   Tags: {', '.join(tags)}")


async def interactive_search():
    """Interactive search interface"""
    searcher = DocumentSearcher()
    
    print("Document Search Interface")
    print("=" * 40)
    
    # Show index statistics
    doc_count = searcher.get_document_count()
    work_items = searcher.get_work_items()
    
    print(f"Index: {searcher.index_name}")
    print(f"Documents: {doc_count}")
    print(f"Work Items: {len(work_items)}")
    
    if work_items:
        print(f"Available Work Items: {', '.join(work_items)}")
    
    print("\nCommands:")
    print("- search <query>                  : Text search")
    print("- vector <query>                  : Vector search")
    print("- hybrid <query>                  : Hybrid search")
    print("- filter <work_item_id> <query>   : Search within work item")
    print("- stats                           : Show index statistics")
    print("- quit                            : Exit")
    
    while True:
        try:
            user_input = input("\n> ").strip()
            
            if not user_input or user_input.lower() in ['quit', 'exit', 'q']:
                break
            
            parts = user_input.split(' ', 2)
            command = parts[0].lower()
            
            if command == 'stats':
                doc_count = searcher.get_document_count()
                work_items = searcher.get_work_items()
                print(f"\nIndex Statistics:")
                print(f"- Documents: {doc_count}")
                print(f"- Work Items: {len(work_items)}")
                if work_items:
                    print(f"- Available: {', '.join(work_items)}")
            
            elif command == 'search' and len(parts) > 1:
                query = ' '.join(parts[1:])
                results = searcher.text_search(query)
                print_search_results(results, "Text Search Results")
            
            elif command == 'vector' and len(parts) > 1:
                query = ' '.join(parts[1:])
                results = await searcher.vector_search(query)
                print_search_results(results, "Vector Search Results")
            
            elif command == 'hybrid' and len(parts) > 1:
                query = ' '.join(parts[1:])
                results = await searcher.hybrid_search(query)
                print_search_results(results, "Hybrid Search Results")
            
            elif command == 'filter' and len(parts) > 2:
                work_item_id = parts[1]
                query = ' '.join(parts[2:])
                results = await searcher.hybrid_search(query, work_item_id)
                print_search_results(results, f"Search Results for Work Item: {work_item_id}")
            
            else:
                print("Invalid command. Type 'quit' to exit.")
        
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")
    
    print("\nGoodbye!")


async def main():
    """Main function"""
    await interactive_search()


if __name__ == "__main__":
    asyncio.run(main())
