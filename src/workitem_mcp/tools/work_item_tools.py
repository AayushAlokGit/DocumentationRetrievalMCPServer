"""
Work Item Documentation Tools
============================

Consolidated work item specific tools that were previously scattered across 
legacy compatibility layer. These tools are specifically designed for work item
documentation retrieval and management use cases.

This module contains:
1. Work item specific tool schemas
2. Work item specific tool handlers
3. Work item context-aware implementations

These tools provide work-item-centric functionality while leveraging the 
universal search infrastructure underneath.
"""

import logging
from typing import Dict, List, Optional, Any
import mcp.types as types

# Import universal tools for underlying functionality
from .universal_tools import (
    handle_search_documents,
    handle_get_document_contexts,
    handle_explore_document_structure,
    handle_get_index_summary
)

logger = logging.getLogger("documentation-retrieval-mcp")


# ===== WORK ITEM TOOL SCHEMAS =====

def get_work_item_tool_schemas() -> list[types.Tool]:
    """Get work item specific tool schemas"""
    return [
        types.Tool(
            name="search_work_items",
            description="Search work item documentation with work-item-aware filtering and results",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query for work item content - can be keywords, questions, or concepts"
                    },
                    "search_type": {
                        "type": "string",
                        "enum": ["text", "vector", "hybrid"],
                        "description": "Search method: 'text' for keyword matching, 'vector' for semantic similarity, 'hybrid' for best results",
                        "default": "hybrid"
                    },
                    "work_item_id": {
                        "type": "string",
                        "description": "Optional: Filter results to specific work item ID"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                        "default": 5,
                        "minimum": 1,
                        "maximum": 20
                    }
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="search_by_work_item",
            description="Search within a specific work item's documentation",
            inputSchema={
                "type": "object",
                "properties": {
                    "work_item_id": {
                        "type": "string",
                        "description": "Work item ID to search within"
                    },
                    "query": {
                        "type": "string",
                        "description": "Search query within the work item"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                        "default": 5,
                        "minimum": 1,
                        "maximum": 10
                    }
                },
                "required": ["work_item_id", "query"]
            }
        ),
        types.Tool(
            name="semantic_search",
            description="Perform semantic/conceptual search across work item documentation",
            inputSchema={
                "type": "object",
                "properties": {
                    "concept": {
                        "type": "string",
                        "description": "Concept, idea, or theme to search for semantically"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                        "default": 5,
                        "minimum": 1,
                        "maximum": 15
                    }
                },
                "required": ["concept"]
            }
        ),
        types.Tool(
            name="search_by_chunk",
            description="Search for specific document chunks using chunk patterns",
            inputSchema={
                "type": "object",
                "properties": {
                    "chunk_pattern": {
                        "type": "string",
                        "description": "Chunk pattern to search for (e.g., 'AppDescription.md_chunk_0')"
                    },
                    "query": {
                        "type": "string",
                        "description": "Optional search query within matching chunks"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                        "default": 5,
                        "minimum": 1,
                        "maximum": 15
                    }
                },
                "required": ["chunk_pattern"]
            }
        ),
        types.Tool(
            name="search_file_chunks",
            description="Search all chunks from a specific file in work item documentation",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_name": {
                        "type": "string",
                        "description": "Name of the file to search chunks from (e.g., 'AppDescription.md')"
                    },
                    "query": {
                        "type": "string",
                        "description": "Optional search query to filter chunks"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of chunks to return",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 20
                    }
                },
                "required": ["file_name"]
            }
        ),
        types.Tool(
            name="get_work_item_list",
            description="Get list of all available work items with document counts",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        types.Tool(
            name="get_work_item_summary",
            description="Get comprehensive summary of work item documentation index",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]


# ===== WORK ITEM TOOL HANDLERS =====

async def handle_work_item_search_work_items(search_service, arguments: dict) -> list[types.TextContent]:
    """Handle work item search with work-item-specific formatting"""
    query = arguments["query"]
    search_type = arguments.get("search_type", "hybrid")
    work_item_id = arguments.get("work_item_id")
    max_results = arguments.get("max_results", 5)
    
    # Build search arguments for universal handler
    new_args = {
        "query": query,
        "search_type": search_type,
        "max_results": max_results
    }
    
    # Add work item filtering if specified
    if work_item_id:
        new_args["filters"] = {"context_name": work_item_id}
    
    logger.info(f"[WORK_ITEM] Searching work items with query: '{query}', type: {search_type}")
    if work_item_id:
        logger.info(f"[WORK_ITEM] Filtering to work item: {work_item_id}")
    
    # Use universal search but add work-item context to results
    results = await handle_search_documents(search_service, new_args)
    
    # Add work-item specific header to results
    if results and results[0].text:
        original_text = results[0].text
        work_item_context = f" (Work Item Context)" if work_item_id else " (All Work Items)"
        enhanced_text = original_text.replace("[SEARCH]", f"[WORK_ITEM_SEARCH]{work_item_context}")
        results[0] = types.TextContent(type="text", text=enhanced_text)
    
    return results


async def handle_work_item_search_by_work_item(search_service, arguments: dict) -> list[types.TextContent]:
    """Search within specific work item with work-item-focused results"""
    work_item_id = arguments["work_item_id"]
    query = arguments["query"]
    max_results = arguments.get("max_results", 5)
    
    new_args = {
        "query": query,
        "search_type": "hybrid",
        "max_results": max_results,
        "filters": {"context_name": work_item_id}
    }
    
    logger.info(f"[WORK_ITEM] Searching within work item '{work_item_id}' for: '{query}'")
    
    results = await handle_search_documents(search_service, new_args)
    
    # Add work item specific context to results
    if results and results[0].text:
        original_text = results[0].text
        enhanced_text = original_text.replace("[SEARCH]", f"[WORK_ITEM: {work_item_id}]")
        results[0] = types.TextContent(type="text", text=enhanced_text)
    
    return results


async def handle_work_item_semantic_search(search_service, arguments: dict) -> list[types.TextContent]:
    """Semantic search with work-item-focused results"""
    concept = arguments["concept"]
    max_results = arguments.get("max_results", 5)
    
    new_args = {
        "query": concept,
        "search_type": "vector",
        "max_results": max_results
    }
    
    logger.info(f"[WORK_ITEM] Semantic search for concept: '{concept}'")
    
    results = await handle_search_documents(search_service, new_args)
    
    # Add semantic search context
    if results and results[0].text:
        original_text = results[0].text
        enhanced_text = original_text.replace("[SEARCH]", f"[SEMANTIC_SEARCH] Concept: '{concept}'")
        results[0] = types.TextContent(type="text", text=enhanced_text)
    
    return results


async def handle_work_item_search_by_chunk(search_service, arguments: dict) -> list[types.TextContent]:
    """Search by chunk pattern with work-item context"""
    chunk_pattern = arguments["chunk_pattern"]
    query = arguments.get("query", "*")
    max_results = arguments.get("max_results", 5)
    
    new_args = {
        "query": query,
        "search_type": "text" if query != "*" else "hybrid",
        "max_results": max_results,
        "filters": {"chunk_pattern": chunk_pattern}
    }
    
    logger.info(f"[WORK_ITEM] Searching by chunk pattern: '{chunk_pattern}'")
    
    results = await handle_search_documents(search_service, new_args)
    
    # Add chunk pattern context
    if results and results[0].text:
        original_text = results[0].text
        enhanced_text = original_text.replace("[SEARCH]", f"[CHUNK_SEARCH] Pattern: '{chunk_pattern}'")
        results[0] = types.TextContent(type="text", text=enhanced_text)
    
    return results


async def handle_work_item_search_file_chunks(search_service, arguments: dict) -> list[types.TextContent]:
    """Search file chunks with work-item-aware formatting"""
    file_name = arguments["file_name"]
    query = arguments.get("query")
    max_results = arguments.get("max_results", 10)
    
    if query:
        # If query provided, use search with file filter
        new_args = {
            "query": query,
            "search_type": "text",
            "max_results": max_results,
            "filters": {"file_name": file_name}
        }
        logger.info(f"[WORK_ITEM] Searching file '{file_name}' with query: '{query}'")
        results = await handle_search_documents(search_service, new_args)
        
        # Add file search context
        if results and results[0].text:
            original_text = results[0].text
            enhanced_text = original_text.replace("[SEARCH]", f"[FILE_SEARCH] File: '{file_name}'")
            results[0] = types.TextContent(type="text", text=enhanced_text)
    else:
        # If no query, explore file structure
        new_args = {
            "structure_type": "chunks",
            "file_name": file_name,
            "max_items": max_results
        }
        logger.info(f"[WORK_ITEM] Exploring chunks in file: '{file_name}'")
        results = await handle_explore_document_structure(search_service, new_args)
        
        # Add file exploration context
        if results and results[0].text:
            original_text = results[0].text
            enhanced_text = original_text.replace("[STRUCTURE]", f"[FILE_CHUNKS] File: '{file_name}'")
            results[0] = types.TextContent(type="text", text=enhanced_text)
    
    return results


async def handle_work_item_get_work_item_list(search_service, arguments: dict) -> list[types.TextContent]:
    """Get work item list with work-item-specific formatting"""
    new_args = {
        "include_stats": True,
        "max_contexts": 1000
    }
    
    logger.info("[WORK_ITEM] Retrieving work item list")
    
    results = await handle_get_document_contexts(search_service, new_args)
    
    # Enhance with work-item specific formatting
    if results and results[0].text:
        original_text = results[0].text
        enhanced_text = original_text.replace("[CONTEXTS]", "[WORK_ITEMS]")
        enhanced_text = enhanced_text.replace("contexts", "work items")
        enhanced_text = enhanced_text.replace("Documents", "Work Item Documents")
        results[0] = types.TextContent(type="text", text=enhanced_text)
    
    return results


async def handle_work_item_get_work_item_summary(search_service, arguments: dict) -> list[types.TextContent]:
    """Get work item summary with work-item-focused presentation"""
    new_args = {
        "include_facets": True,
        "facet_limit": 50
    }
    
    logger.info("[WORK_ITEM] Retrieving work item summary")
    
    results = await handle_get_index_summary(search_service, new_args)
    
    # Enhance with work-item specific context
    if results and results[0].text:
        original_text = results[0].text
        enhanced_text = original_text.replace("[INDEX_SUMMARY]", "[WORK_ITEM_SUMMARY]")
        enhanced_text = enhanced_text.replace("Document Index", "Work Item Documentation Index")
        enhanced_text = enhanced_text.replace("documents", "work item documents")
        results[0] = types.TextContent(type="text", text=enhanced_text)
    
    return results


# ===== WORK ITEM TOOL HANDLER MAPPING =====

WORK_ITEM_TOOL_HANDLERS = {
    "search_work_items": handle_work_item_search_work_items,
    "search_by_work_item": handle_work_item_search_by_work_item,
    "semantic_search": handle_work_item_semantic_search,
    "search_by_chunk": handle_work_item_search_by_chunk,
    "search_file_chunks": handle_work_item_search_file_chunks,
    "get_work_item_list": handle_work_item_get_work_item_list,
    "get_work_item_summary": handle_work_item_get_work_item_summary,
}
