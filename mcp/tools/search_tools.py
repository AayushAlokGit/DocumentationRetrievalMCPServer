"""
Search Tool Handlers for MCP Server
===================================

Handlers for all search-related MCP tools including text search, vector search,
hybrid search, and work item filtering.
"""

import logging
from typing import Dict, List, Optional
import mcp.types as types

logger = logging.getLogger("work-items-mcp")


async def handle_search_work_items(searcher, arguments: dict) -> list[types.TextContent]:
    """Handle work item search requests"""
    query = arguments.get("query", "")
    search_type = arguments.get("search_type", "hybrid")
    work_item_id = arguments.get("work_item_id")
    max_results = arguments.get("max_results", 5)
    
    if not query:
        return [types.TextContent(type="text", text="[ERROR] Query parameter is required")]
    
    try:
        # Perform the appropriate search
        if search_type == "text":
            results = searcher.text_search(query, work_item_id, max_results)
        elif search_type == "vector":
            results = await searcher.vector_search(query, work_item_id, max_results)
        elif search_type == "hybrid":
            results = await searcher.hybrid_search(query, work_item_id, max_results)
        else:
            return [types.TextContent(
                type="text",
                text=f"[ERROR] Invalid search type: {search_type}. Must be 'text', 'vector', or 'hybrid'"
            )]
        
        if not results:
            filter_text = f" (filtered to work item: {work_item_id})" if work_item_id else ""
            return [types.TextContent(
                type="text",
                text=f"[SEARCH] No results found for '{query}' using {search_type} search{filter_text}"
            )]
        
        # Format results for LLM consumption
        from .result_formatter import format_search_results
        formatted_results = format_search_results(results, f"{search_type.title()} Search Results", query)
        return [types.TextContent(type="text", text=formatted_results)]
    
    except Exception as e:
        return [types.TextContent(type="text", text=f"[ERROR] Search failed: {str(e)}")]


async def handle_search_by_work_item(searcher, arguments: dict) -> list[types.TextContent]:
    """Handle work item specific search requests"""
    work_item_id = arguments.get("work_item_id", "")
    query = arguments.get("query", "")
    max_results = arguments.get("max_results", 5)
    
    if not work_item_id or not query:
        return [types.TextContent(
            type="text",
            text="[ERROR] Both work_item_id and query parameters are required"
        )]
    
    try:
        # Use hybrid search with work item filter
        results = await searcher.hybrid_search(query, work_item_id, max_results)
        
        if not results:
            return [types.TextContent(
                type="text",
                text=f"[SEARCH] No results found for '{query}' in work item '{work_item_id}'"
            )]
        
        from .result_formatter import format_search_results
        formatted_results = format_search_results(
            results, 
            f"Search Results for Work Item: {work_item_id}", 
            query
        )
        
        return [types.TextContent(type="text", text=formatted_results)]
    
    except Exception as e:
        return [types.TextContent(type="text", text=f"[ERROR] Work item search failed: {str(e)}")]


async def handle_semantic_search(searcher, arguments: dict) -> list[types.TextContent]:
    """Handle semantic/vector search requests"""
    concept = arguments.get("concept", "")
    max_results = arguments.get("max_results", 5)
    
    if not concept:
        return [types.TextContent(type="text", text="[ERROR] concept parameter is required")]
    
    try:
        # Perform vector search for semantic similarity
        results = await searcher.vector_search(concept, None, max_results)
        
        if not results:
            return [types.TextContent(
                type="text",
                text=f"[SEARCH] No semantically similar content found for concept: '{concept}'"
            )]
        
        from .result_formatter import format_search_results
        formatted_results = format_search_results(
            results, 
            f"Semantic Search Results for: {concept}", 
            concept
        )
        
        return [types.TextContent(type="text", text=formatted_results)]
    
    except Exception as e:
        return [types.TextContent(type="text", text=f"[ERROR] Semantic search failed: {str(e)}")]
