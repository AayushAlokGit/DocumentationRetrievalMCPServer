"""
Universal Document Search Tool Handlers
=======================================

Implementation of the new universal MCP tools that work across all document types.
These replace the old work-item specific tools with universal capabilities.
"""

import logging
from typing import Dict, Any, Optional, List
import mcp.types as types

from common.azure_cognitive_search import FilterBuilder

logger = logging.getLogger("work-items-mcp")


async def handle_search_documents(search_service, arguments: dict) -> list[types.TextContent]:
    """Handle universal document search with comprehensive filtering"""
    try:
        query = arguments.get("query", "")
        search_type = arguments.get("search_type", "hybrid")
        filters = arguments.get("filters", {})
        max_results = arguments.get("max_results", 5)
        include_content = arguments.get("include_content", True)
        
        logger.info(f"[SEARCH] Universal search: query='{query}', type={search_type}, filters={filters}")
        
        # Build filter expression using FilterBuilder
        filter_expr = None
        if filters:
            # Check for special field suffixes that require advanced filtering
            if any(key.endswith(('_text_search', '_contains', '_startswith', '_endswith')) for key in filters.keys()):
                filter_expr = FilterBuilder.build_advanced_filter(filters)
            else:
                filter_expr = FilterBuilder.build_filter(filters)
        
        # Execute search based on type
        if search_type == "text":
            results = search_service.text_search(query, filter_expr, max_results)
        elif search_type == "vector":
            results = await search_service.vector_search(query, filter_expr, max_results)
        elif search_type == "semantic":
            results = search_service.semantic_search(query, filter_expr, max_results)
        else:  # hybrid (default)
            results = await search_service.hybrid_search(query, filter_expr, max_results)
        
        # Format results
        if not results:
            return [types.TextContent(
                type="text",
                text=f"[NO RESULTS] No documents found for query: '{query}'"
            )]
        
        # Select fields based on include_content
        select_fields = ["id", "title", "context_name", "file_name", "chunk_index"]
        if include_content:
            select_fields.append("content")
        
        formatted_results = []
        for i, result in enumerate(results[:max_results], 1):
            result_text = f"[RESULT {i}]\n"
            result_text += f"Context: {result.get('context_name', 'Unknown')}\n"
            result_text += f"File: {result.get('file_name', 'Unknown')}\n"
            result_text += f"Title: {result.get('title', 'No title')}\n"
            
            if include_content and 'content' in result:
                content = result['content']
                if len(content) > 500:
                    content = content[:500] + "..."
                result_text += f"Content: {content}\n"
            
            result_text += f"Score: {result.get('@search.score', 'N/A')}\n"
            result_text += "---\n"
            formatted_results.append(result_text)
        
        response = f"[SUCCESS] Found {len(results)} documents\n\n" + "\n".join(formatted_results)
        
        return [types.TextContent(type="text", text=response)]
        
    except Exception as e:
        logger.error(f"Error in search_documents: {e}")
        return [types.TextContent(
            type="text", 
            text=f"[ERROR] Search failed: {str(e)}"
        )]


async def handle_get_document_contexts(search_service, arguments: dict) -> list[types.TextContent]:
    """Handle document context discovery with statistics"""
    try:
        context_type = arguments.get("context_type", "all")
        include_stats = arguments.get("include_stats", True)
        max_contexts = arguments.get("max_contexts", 100)
        
        logger.info(f"[CONTEXTS] Getting contexts: type={context_type}, stats={include_stats}")
        
        # Use Azure Search facets to get context distribution
        facets = [f"context_name,count:{max_contexts}"]
        
        results = search_service.search_client.search(
            search_text="*",
            facets=facets,
            top=0  # Only need facet data
        )
        
        facet_data = results.get_facets()
        contexts = facet_data.get("context_name", [])
        
        # Filter by context type if specified
        if context_type != "all":
            filtered_contexts = []
            for context in contexts:
                context_name = context["value"]
                if context_type == "work_item" and context_name.startswith("WORK-"):
                    filtered_contexts.append(context)
                elif context_type == "project" and context_name.startswith("PROJ-"):
                    filtered_contexts.append(context)
                elif context_type == "contract" and context_name.startswith("CONT-"):
                    filtered_contexts.append(context)
            contexts = filtered_contexts
        
        if not contexts:
            return [types.TextContent(
                type="text",
                text=f"[NO CONTEXTS] No contexts found for type: {context_type}"
            )]
        
        # Format response
        response = f"[SUCCESS] Found {len(contexts)} contexts\n\n"
        
        for i, context in enumerate(contexts[:max_contexts], 1):
            context_name = context["value"]
            doc_count = context["count"] if include_stats else "N/A"
            response += f"{i}. {context_name}"
            if include_stats:
                response += f" ({doc_count} documents)"
            response += "\n"
        
        if len(contexts) > max_contexts:
            response += f"\n... and {len(contexts) - max_contexts} more contexts"
        
        return [types.TextContent(type="text", text=response)]
        
    except Exception as e:
        logger.error(f"Error in get_document_contexts: {e}")
        return [types.TextContent(
            type="text", 
            text=f"[ERROR] Context discovery failed: {str(e)}"
        )]


async def handle_explore_document_structure(search_service, arguments: dict) -> list[types.TextContent]:
    """Handle document structure exploration"""
    try:
        structure_type = arguments.get("structure_type", "contexts")
        context_name = arguments.get("context_name")
        file_name = arguments.get("file_name") 
        chunk_range = arguments.get("chunk_range")
        max_items = arguments.get("max_items", 50)
        
        logger.info(f"[STRUCTURE] Exploring: type={structure_type}, context={context_name}")
        
        if structure_type == "contexts":
            return await _explore_contexts(search_service, arguments)
        elif structure_type == "files":
            return await _explore_files(search_service, arguments)
        elif structure_type == "chunks":
            return await _explore_chunks(search_service, arguments)
        elif structure_type == "categories":
            return await _explore_categories(search_service, arguments)
        else:
            return [types.TextContent(
                type="text",
                text=f"[ERROR] Unknown structure type: {structure_type}"
            )]
            
    except Exception as e:
        logger.error(f"Error in explore_document_structure: {e}")
        return [types.TextContent(
            type="text", 
            text=f"[ERROR] Structure exploration failed: {str(e)}"
        )]


async def handle_get_index_summary(search_service, arguments: dict) -> list[types.TextContent]:
    """Handle index summary and statistics"""
    try:
        include_facets = arguments.get("include_facets", True)
        facet_limit = arguments.get("facet_limit", 50)
        
        logger.info(f"[SUMMARY] Getting index summary: facets={include_facets}")
        
        # Prepare facets for detailed statistics
        facets = []
        if include_facets:
            facets = [
                f"context_name,count:{facet_limit}",
                f"file_type,count:{facet_limit}",
                f"category,count:{facet_limit}",
                f"tags,count:{facet_limit * 2}"  # More tags expected
            ]
        
        # Get comprehensive statistics
        results = search_service.search_client.search(
            search_text="*",
            facets=facets,
            top=0,
            include_total_count=True
        )
        
        total_count = results.get_count()
        facet_data = results.get_facets() if include_facets else {}
        
        # Build response
        response = f"[INDEX SUMMARY]\n"
        response += f"Total Documents: {total_count}\n\n"
        
        if include_facets:
            # Context distribution
            contexts = facet_data.get("context_name", [])
            response += f"Contexts ({len(contexts)}): "
            context_names = [c["value"] for c in contexts[:5]]
            response += ", ".join(context_names)
            if len(contexts) > 5:
                response += f", ... and {len(contexts) - 5} more"
            response += "\n\n"
            
            # File type distribution
            file_types = facet_data.get("file_type", [])
            response += f"File Types ({len(file_types)}): "
            for ft in file_types[:10]:
                response += f"{ft['value']} ({ft['count']}), "
            response = response.rstrip(", ") + "\n\n"
            
            # Category distribution
            categories = facet_data.get("category", [])
            if categories:
                response += f"Categories ({len(categories)}): "
                for cat in categories[:10]:
                    response += f"{cat['value']} ({cat['count']}), "
                response = response.rstrip(", ") + "\n\n"
            
            # Popular tags
            tags = facet_data.get("tags", [])
            if tags:
                response += f"Popular Tags ({len(tags)}): "
                for tag in tags[:15]:
                    response += f"{tag['value']} ({tag['count']}), "
                response = response.rstrip(", ") + "\n"
        
        return [types.TextContent(type="text", text=response)]
        
    except Exception as e:
        logger.error(f"Error in get_index_summary: {e}")
        return [types.TextContent(
            type="text", 
            text=f"[ERROR] Index summary failed: {str(e)}"
        )]


# Helper functions for structure exploration

async def _explore_contexts(search_service, arguments: dict) -> list[types.TextContent]:
    """Explore context hierarchy"""
    # Implementation using facets similar to get_document_contexts
    return await handle_get_document_contexts(search_service, arguments)


async def _explore_files(search_service, arguments: dict) -> list[types.TextContent]:
    """Explore file structure"""
    context_name = arguments.get("context_name")
    max_items = arguments.get("max_items", 50)
    
    filters = {}
    if context_name:
        filters["context_name"] = context_name
    
    filter_expr = FilterBuilder.build_filter(filters) if filters else None
    
    results = search_service.search_client.search(
        search_text="*",
        filter=filter_expr,
        facets=["file_name,count:1000"],
        top=0
    )
    
    facet_data = results.get_facets()
    files = facet_data.get("file_name", [])
    
    response = f"[FILES] Found {len(files)} files\n\n"
    for i, file_info in enumerate(files[:max_items], 1):
        response += f"{i}. {file_info['value']} ({file_info['count']} chunks)\n"
    
    return [types.TextContent(type="text", text=response)]


async def _explore_chunks(search_service, arguments: dict) -> list[types.TextContent]:
    """Explore chunk structure with ordered retrieval"""
    context_name = arguments.get("context_name")
    file_name = arguments.get("file_name")
    chunk_range = arguments.get("chunk_range")
    max_items = arguments.get("max_items", 50)
    
    filters = {}
    if context_name:
        filters["context_name"] = context_name
    if file_name:
        filters["file_name"] = file_name
    
    filter_expr = FilterBuilder.build_filter(filters) if filters else None
    
    # Build orderby clause for chunk navigation
    orderby = "file_name,chunk_index"
    
    results = search_service.search_client.search(
        search_text="*",
        filter=filter_expr,
        select="file_name,chunk_index,context_name,title,content",
        orderby=orderby,
        top=max_items
    )
    
    chunks = list(results)
    
    response = f"[CHUNKS] Found {len(chunks)} chunks\n\n"
    for i, chunk in enumerate(chunks, 1):
        response += f"{i}. {chunk.get('file_name', 'Unknown')} - Chunk {chunk.get('chunk_index', 'N/A')}\n"
        response += f"   Title: {chunk.get('title', 'No title')}\n"
        content = chunk.get('content', '')
        if len(content) > 100:
            content = content[:100] + "..."
        response += f"   Content: {content}\n\n"
    
    return [types.TextContent(type="text", text=response)]


async def _explore_categories(search_service, arguments: dict) -> list[types.TextContent]:
    """Explore category structure"""
    context_name = arguments.get("context_name")
    max_items = arguments.get("max_items", 50)
    
    filters = {}
    if context_name:
        filters["context_name"] = context_name
    
    filter_expr = FilterBuilder.build_filter(filters) if filters else None
    
    results = search_service.search_client.search(
        search_text="*",
        filter=filter_expr,
        facets=["category,count:1000"],
        top=0
    )
    
    facet_data = results.get_facets()
    categories = facet_data.get("category", [])
    
    response = f"[CATEGORIES] Found {len(categories)} categories\n\n"
    for i, cat_info in enumerate(categories[:max_items], 1):
        response += f"{i}. {cat_info['value']} ({cat_info['count']} documents)\n"
    
    return [types.TextContent(type="text", text=response)]
