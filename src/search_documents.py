"""
Search and Query Azure Cognitive Search
Test search functionality and query documents

This module now uses the centralized AzureCognitiveSearch class for all operations.
"""

import os
import asyncio
from dotenv import load_dotenv
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


# ===== INTERACTIVE SEARCH FUNCTIONALITY =====

async def interactive_search():
    """Interactive search mode for testing different search types"""
    
    print("[SEARCH] Interactive Work Item Search")
    print("=" * 40)
    print("Available commands:")
    print("  text <query>          - Text search")
    print("  vector <query>        - Vector search")  
    print("  hybrid <query>        - Hybrid search")
    print("  semantic <query>      - Semantic search")
    print("  work-items            - List all work items")
    print("  stats                 - Show index statistics")
    print("  quit                  - Exit")
    print()
    
    # Initialize searcher
    try:
        searcher = DocumentSearcher()
        print(f"[SUCCESS] Connected to search index: {searcher.index_name}")
        print(f"[SUMMARY] Total documents: {searcher.get_document_count()}")
        print()
    except Exception as e:
        print(f"[ERROR] Failed to connect to search service: {e}")
        return
    
    while True:
        try:
            user_input = input("\n[SEARCH] Enter command: ").strip()
            
            if not user_input:
                continue
                
            if user_input.lower() == 'quit':
                print("👋 Goodbye!")
                break
            
            parts = user_input.split(' ', 1)
            command = parts[0].lower()
            query = parts[1] if len(parts) > 1 else ""
            
            if command == 'work-items':
                work_items = searcher.get_work_items()
                print(f"\nFile: Available Work Items ({len(work_items)}):")
                for wi in work_items:
                    print(f"  • {wi}")
            
            elif command == 'stats':
                doc_count = searcher.get_document_count()
                work_items = searcher.get_work_items()
                print(f"\n[SUMMARY] Index Statistics:")
                print(f"  [DOCUMENT] Total Documents: {doc_count}")
                print(f"  File: Work Items: {len(work_items)}")
                print(f"  [SEARCH] Index Name: {searcher.index_name}")
                print(f"  🌐 Service: {searcher.service_name}")
            
            elif command in ['text', 'vector', 'hybrid', 'semantic']:
                if not query:
                    print("[ERROR] Please provide a search query")
                    continue
                
                print(f"\n[SEARCH] Performing {command} search for: '{query}'")
                
                # Ask for work item filter
                work_item_filter = input("[TARGET] Filter by work item (press Enter for all): ").strip()
                work_item_filter = work_item_filter if work_item_filter else None
                
                # Perform the search
                if command == 'text':
                    results = searcher.text_search(query, work_item_filter)
                elif command == 'vector':
                    results = await searcher.vector_search(query, work_item_filter)
                elif command == 'hybrid':
                    results = await searcher.hybrid_search(query, work_item_filter)
                elif command == 'semantic':
                    results = searcher.semantic_search(query, work_item_filter)
                
                # Display results
                if results:
                    searcher.print_search_results(results, f"{command.title()} Search Results")
                else:
                    print(f"[ERROR] No results found for '{query}'")
            
            else:
                print("[ERROR] Unknown command. Use: text, vector, hybrid, semantic, work-items, stats, or quit")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"[ERROR] Error: {e}")


async def main():
    """Main function for testing search functionality"""
    
    print("[START] Work Item Search Test")
    print("=" * 30)
    
    try:
        # Initialize searcher
        searcher = DocumentSearcher()
        
        # Test connection and get basic stats
        doc_count = searcher.get_document_count()
        work_items = searcher.get_work_items()
        
        print(f"[SUCCESS] Connected to search service")
        print(f"[LIST] Index: {searcher.index_name}")
        print(f"[DOCUMENT] Documents: {doc_count}")
        print(f"File: Work Items: {len(work_items)}")
        
        if work_items:
            print(f"[TARGET] Available Work Items: {', '.join(work_items[:5])}")
            if len(work_items) > 5:
                print(f"   ... and {len(work_items) - 5} more")
        
        # Run sample searches if there are documents
        if doc_count > 0:
            print(f"\n[SEARCH] Running sample searches...")
            
            # Text search
            print(f"\n1️⃣ Text Search:")
            results = searcher.text_search("error", top_k=3)
            searcher.print_search_results(results, "Text Search - 'error'")
            
            # Vector search
            print(f"\n2️⃣ Vector Search:")
            results = await searcher.vector_search("authentication problem", top_k=3)
            searcher.print_search_results(results, "Vector Search - 'authentication problem'")
            
            # Hybrid search
            print(f"\n3️⃣ Hybrid Search:")
            results = await searcher.hybrid_search("database connection", top_k=3)
            searcher.print_search_results(results, "Hybrid Search - 'database connection'")
        
        else:
            print(f"\nTips: No documents found. Upload some documents first using:")
            print(f"   python scripts/upload_work_items.py")
        
        # Start interactive mode
        print(f"\n🎮 Starting interactive search mode...")
        await interactive_search()
        
    except Exception as e:
        print(f"[ERROR] Search test failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
