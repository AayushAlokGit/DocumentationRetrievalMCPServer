"""
Result Formatter for MCP Server
===============================

Utility functions for formatting search results and other output
for optimal LLM consumption.
"""

from typing import Dict, List


def format_search_results(results: List[Dict], title: str, query: str) -> str:
    """Format search results for LLM consumption with rich context."""
    if not results:
        return f"[SEARCH] No results found for '{query}'"
    
    formatted = f"[SEARCH] {title}\n"
    formatted += f"{'='*60}\n"
    formatted += f"Query: '{query}' | Results: {len(results)}\n\n"
    
    for i, result in enumerate(results, 1):
        formatted += f"[DOCUMENT] Result {i}\n"
        formatted += f"{'-'*30}\n"
        
        # Basic metadata
        formatted += f"ID: {result.get('id', 'N/A')}\n"
        formatted += f"Title: {result.get('title', 'Untitled')}\n"
        formatted += f"[INFO] Work Item: {result.get('work_item_id', 'N/A')}\n"
        formatted += f"File: {result.get('file_path', 'N/A')}\n"
        
        # Search score if available
        if '@search.score' in result:
            score = result['@search.score']
            formatted += f"Relevance Score: {score:.2f}\n"
        
        # Tags if available
        tags = result.get('tags', [])
        if tags:
            formatted += f"Tags: {', '.join(tags)}\n"
        
        # Content preview
        content = result.get('content', '')
        if content:
            # Limit content preview for readability
            content_preview = content[:500] + "..." if len(content) > 500 else content
            formatted += f"\n[DOCUMENT] Content:\n{content_preview}\n"
        
        formatted += f"\n"
    
    # Add usage suggestions
    formatted += f"Tips:\n"
    formatted += f"   • Use search_by_work_item to search within specific work items\n"
    formatted += f"   • Try different search types: text, vector, or hybrid\n"
    formatted += f"   • Use semantic_search for concept-based searches\n"
    
    return formatted
