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
        # Use new filter-based approach with legacy bridging
        filters = {"context_id": work_item_id} if work_item_id else None
        
        # Perform the appropriate search
        if search_type == "text":
            results = searcher.text_search(query, filters, max_results)
        elif search_type == "vector":
            results = await searcher.vector_search(query, filters, max_results)
        elif search_type == "hybrid":
            results = await searcher.hybrid_search(query, filters, max_results)
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
        # Use hybrid search with work item filter - new filter approach
        filters = {"context_id": work_item_id}
        results = await searcher.hybrid_search(query, filters, max_results)
        
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
        # Perform vector search for semantic similarity - no filters
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


async def handle_search_by_chunk(searcher, arguments: dict) -> list[types.TextContent]:
    """Handle chunk-specific search requests using the enhanced chunk_index field"""
    chunk_pattern = arguments.get("chunk_pattern", "")
    query = arguments.get("query", "")
    max_results = arguments.get("max_results", 5)
    
    if not chunk_pattern:
        return [types.TextContent(
            type="text",
            text="[ERROR] chunk_pattern parameter is required (e.g., 'AppDescription.md_chunk_0' or 'AppDescription.md' for all chunks from that file)"
        )]
    
    try:
        # Search using the enhanced chunk_index field
        if query:
            # Combine content search with chunk filtering
            results = await searcher.hybrid_search(query, {"chunk_index": chunk_pattern}, max_results)
            search_description = f"Content search for '{query}' in chunks matching '{chunk_pattern}'"
        else:
            # Just find chunks matching the pattern
            results = searcher.text_search("*", {"chunk_index": chunk_pattern}, max_results)
            search_description = f"All chunks matching pattern '{chunk_pattern}'"
        
        if not results:
            return [types.TextContent(
                type="text",
                text=f"[SEARCH] No results found for chunk pattern: '{chunk_pattern}'"
            )]
        
        from .result_formatter import format_search_results
        formatted_results = format_search_results(
            results, 
            f"Chunk Search Results: {chunk_pattern}", 
            search_description
        )
        
        return [types.TextContent(type="text", text=formatted_results)]
    
    except Exception as e:
        return [types.TextContent(type="text", text=f"[ERROR] Chunk search failed: {str(e)}")]


async def handle_search_file_chunks(searcher, arguments: dict) -> list[types.TextContent]:
    """Handle searching for all chunks from a specific file"""
    file_name = arguments.get("file_name", "")
    query = arguments.get("query", "")
    max_results = arguments.get("max_results", 10)
    
    if not file_name:
        return [types.TextContent(
            type="text",
            text="[ERROR] file_name parameter is required (e.g., 'AppDescription.md')"
        )]
    
    try:
        # Search for chunks from this specific file using file_name filter
        if query:
            # Search content within the specific file
            results = await searcher.hybrid_search(query, {"file_name": file_name}, max_results)
            search_description = f"Content search for '{query}' in file '{file_name}'"
        else:
            # Get all chunks from this file
            results = searcher.text_search("*", {"file_name": file_name}, max_results)
            search_description = f"All chunks from file '{file_name}'"
        
        if not results:
            return [types.TextContent(
                type="text",
                text=f"[SEARCH] No chunks found for file: '{file_name}'"
            )]
        
        # Sort results by chunk_index for better readability
        sorted_results = sorted(results, key=lambda x: x.get('chunk_index', ''))
        
        from .result_formatter import format_search_results
        formatted_results = format_search_results(
            sorted_results, 
            f"File Chunks: {file_name}", 
            search_description
        )
        
        return [types.TextContent(type="text", text=formatted_results)]
    
    except Exception as e:
        return [types.TextContent(type="text", text=f"[ERROR] File chunks search failed: {str(e)}")]


async def handle_search_chunk_range(searcher, arguments: dict) -> list[types.TextContent]:
    """Handle searching for a range of chunks from a specific file"""
    file_name = arguments.get("file_name", "")
    start_chunk = arguments.get("start_chunk", 0)
    end_chunk = arguments.get("end_chunk", None)
    max_results = arguments.get("max_results", 10)
    
    if not file_name:
        return [types.TextContent(
            type="text",
            text="[ERROR] file_name parameter is required (e.g., 'AppDescription.md')"
        )]
    
    try:
        # Get all chunks from this file first
        all_chunks = searcher.text_search("*", {"file_name": file_name}, 50)  # Get more chunks to filter
        
        if not all_chunks:
            return [types.TextContent(
                type="text",
                text=f"[SEARCH] No chunks found for file: '{file_name}'"
            )]
        
        # Filter chunks by range based on chunk_index
        filtered_chunks = []
        for chunk in all_chunks:
            chunk_index_str = chunk.get('chunk_index', '')
            # Extract chunk number from format like "AppDescription.md_chunk_0"
            if '_chunk_' in chunk_index_str:
                try:
                    chunk_num = int(chunk_index_str.split('_chunk_')[-1])
                    if chunk_num >= start_chunk:
                        if end_chunk is None or chunk_num <= end_chunk:
                            filtered_chunks.append(chunk)
                except ValueError:
                    continue
        
        # Limit results and sort by chunk number
        filtered_chunks = sorted(filtered_chunks, key=lambda x: int(x.get('chunk_index', '').split('_chunk_')[-1]) if '_chunk_' in x.get('chunk_index', '') else 0)
        filtered_chunks = filtered_chunks[:max_results]
        
        if not filtered_chunks:
            range_text = f"chunks {start_chunk}-{end_chunk}" if end_chunk is not None else f"chunks {start_chunk}+"
            return [types.TextContent(
                type="text",
                text=f"[SEARCH] No chunks found in range {range_text} for file: '{file_name}'"
            )]
        
        range_text = f"chunks {start_chunk}-{end_chunk}" if end_chunk is not None else f"chunks {start_chunk}+"
        
        from .result_formatter import format_search_results
        formatted_results = format_search_results(
            filtered_chunks, 
            f"Chunk Range: {file_name} ({range_text})", 
            f"Chunks {start_chunk} to {end_chunk if end_chunk else 'end'} from {file_name}"
        )
        
        return [types.TextContent(type="text", text=formatted_results)]
    
    except Exception as e:
        return [types.TextContent(type="text", text=f"[ERROR] Chunk range search failed: {str(e)}")]
