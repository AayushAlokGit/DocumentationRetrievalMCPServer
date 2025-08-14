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
        formatted += f"[INFO] Work Item: {result.get('context_id', 'N/A')}\n"
        formatted += f"File: {result.get('file_path', 'N/A')}\n"
        
        # Additional file information if available
        file_name = result.get('file_name')
        if file_name:
            formatted += f"File Name: {file_name}\n"
        
        file_type = result.get('file_type')
        if file_type:
            formatted += f"File Type: {file_type}\n"
        
        # Context information
        context_name = result.get('context_name')
        if context_name:
            formatted += f"Context: {context_name}\n"
        
        # Category information
        category = result.get('category')
        if category:
            formatted += f"Category: {category}\n"
        
        # Search score if available
        if '@search.score' in result:
            score = result['@search.score']
            formatted += f"Relevance Score: {score:.2f}\n"
        
        # Chunk information if available (enhanced display)
        chunk_index = result.get('chunk_index')
        if chunk_index is not None:
            formatted += f"Chunk Index: {chunk_index}\n"
            # Extract chunk number and file for easier reference
            if '_chunk_' in str(chunk_index):
                try:
                    file_part, chunk_part = str(chunk_index).split('_chunk_')
                    chunk_num = int(chunk_part)
                    formatted += f"   → File: {file_part}, Chunk #: {chunk_num}\n"
                except (ValueError, IndexError):
                    pass
        
        # Timestamp information
        last_modified = result.get('last_modified')
        if last_modified:
            formatted += f"Last Modified: {last_modified}\n"
        
        # Tags if available
        tags = result.get('tags', "")
        if tags:
            formatted += f"Tags: {tags}\n"
        
        # Content preview
        content = result.get('content', '')
        if content:
            # Limit content preview for readability
            content_preview = content[:500] + "..." if len(content) > 500 else content
            formatted += f"\n[DOCUMENT] Content:\n{content_preview}\n"
        
        formatted += f"\n"
    
    # Add usage suggestions with new chunk-based tools
    formatted += f"Tips:\n"
    formatted += f"   • Use search_by_work_item to search within specific work items\n"
    formatted += f"   • Try different search types: text, vector, or hybrid\n"
    formatted += f"   • Use semantic_search for concept-based searches\n"
    formatted += f"   • Use search_file_chunks to get all chunks from a specific file\n"
    formatted += f"   • Use search_by_chunk to find specific chunks by their index\n"
    formatted += f"   • Use search_chunk_range to get a sequence of chunks from a file\n"
    
    return formatted
