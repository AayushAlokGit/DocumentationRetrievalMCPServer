"""
Legacy Tool Compatibility Layer
===============================

Provides backward compatibility for clients still using old tool names.
Maps old tool calls to new universal tool implementations.
"""

import logging
from typing import Dict, Any
import mcp.types as types

from .universal_tools import (
    handle_search_documents,
    handle_get_document_contexts,
    handle_explore_document_structure,
    handle_get_index_summary
)

logger = logging.getLogger("work-items-mcp")


async def handle_legacy_search_work_items(search_service, arguments: dict) -> list[types.TextContent]:
    """Map old search_work_items to new search_documents"""
    new_args = {
        "query": arguments["query"],
        "search_type": arguments.get("search_type", "hybrid"),
        "max_results": arguments.get("max_results", 5)
    }
    
    # Map work_item_id to context_name filter
    if arguments.get("work_item_id"):
        new_args["filters"] = {"context_name": arguments["work_item_id"]}
    
    logger.info(f"[LEGACY] Mapping search_work_items to search_documents")
    return await handle_search_documents(search_service, new_args)


async def handle_legacy_search_by_work_item(search_service, arguments: dict) -> list[types.TextContent]:
    """Map old search_by_work_item to new search_documents"""
    new_args = {
        "query": arguments["query"],
        "search_type": "hybrid",
        "max_results": arguments.get("max_results", 5),
        "filters": {"context_name": arguments["work_item_id"]}
    }
    
    logger.info(f"[LEGACY] Mapping search_by_work_item to search_documents")
    return await handle_search_documents(search_service, new_args)


async def handle_legacy_semantic_search(search_service, arguments: dict) -> list[types.TextContent]:
    """Map old semantic_search to new search_documents"""
    new_args = {
        "query": arguments["concept"],
        "search_type": "vector",
        "max_results": arguments.get("max_results", 5)
    }
    
    logger.info(f"[LEGACY] Mapping semantic_search to search_documents")
    return await handle_search_documents(search_service, new_args)


async def handle_legacy_search_by_chunk(search_service, arguments: dict) -> list[types.TextContent]:
    """Map old search_by_chunk to new search_documents"""
    new_args = {
        "query": arguments.get("query", "*"),
        "search_type": "text",
        "max_results": arguments.get("max_results", 5),
        "filters": {"chunk_pattern": arguments["chunk_pattern"]}
    }
    
    logger.info(f"[LEGACY] Mapping search_by_chunk to search_documents")
    return await handle_search_documents(search_service, new_args)


async def handle_legacy_search_file_chunks(search_service, arguments: dict) -> list[types.TextContent]:
    """Map old search_file_chunks to new explore_document_structure"""
    new_args = {
        "structure_type": "chunks",
        "file_name": arguments["file_name"],
        "max_items": arguments.get("max_results", 10)
    }
    
    if arguments.get("query"):
        # If query provided, use search_documents instead
        search_args = {
            "query": arguments["query"],
            "search_type": "text",
            "max_results": arguments.get("max_results", 10),
            "filters": {"file_name": arguments["file_name"]}
        }
        logger.info(f"[LEGACY] Mapping search_file_chunks to search_documents")
        return await handle_search_documents(search_service, search_args)
    
    logger.info(f"[LEGACY] Mapping search_file_chunks to explore_document_structure")
    return await handle_explore_document_structure(search_service, new_args)


async def handle_legacy_search_chunk_range(search_service, arguments: dict) -> list[types.TextContent]:
    """Map old search_chunk_range to new explore_document_structure"""
    new_args = {
        "structure_type": "chunks",
        "file_name": arguments["file_name"],
        "chunk_range": {
            "start": arguments.get("start_chunk", 0),
            "end": arguments.get("end_chunk")
        },
        "max_items": arguments.get("max_results", 10)
    }
    
    logger.info(f"[LEGACY] Mapping search_chunk_range to explore_document_structure")
    return await handle_explore_document_structure(search_service, new_args)


async def handle_legacy_get_work_item_list(search_service, arguments: dict) -> list[types.TextContent]:
    """Map old get_work_item_list to new get_document_contexts"""
    new_args = {
        "context_type": "work_item",
        "include_stats": True,
        "max_contexts": 1000
    }
    
    logger.info(f"[LEGACY] Mapping get_work_item_list to get_document_contexts")
    return await handle_get_document_contexts(search_service, new_args)


async def handle_legacy_get_work_item_summary(search_service, arguments: dict) -> list[types.TextContent]:
    """Map old get_work_item_summary to new get_index_summary"""
    new_args = {
        "include_facets": True,
        "facet_limit": 50
    }
    
    logger.info(f"[LEGACY] Mapping get_work_item_summary to get_index_summary")
    return await handle_get_index_summary(search_service, new_args)


# Legacy tool handler mapping
LEGACY_TOOL_HANDLERS = {
    "search_work_items": handle_legacy_search_work_items,
    "search_by_work_item": handle_legacy_search_by_work_item,
    "semantic_search": handle_legacy_semantic_search,
    "search_by_chunk": handle_legacy_search_by_chunk,
    "search_file_chunks": handle_legacy_search_file_chunks,
    "search_chunk_range": handle_legacy_search_chunk_range,
    "get_work_item_list": handle_legacy_get_work_item_list,
    "get_work_item_summary": handle_legacy_get_work_item_summary,
}
