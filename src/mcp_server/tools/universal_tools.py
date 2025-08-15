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
        
        # Handle special chunk_pattern filter by mapping to chunk_index
        processed_filters = {}
        for key, value in filters.items():
            if key == "chunk_pattern":
                # Map chunk_pattern to chunk_index field
                processed_filters["chunk_index"] = value
            else:
                processed_filters[key] = value
        
        # Execute search based on type - pass processed filters dict directly to search methods
        if search_type == "text":
            results = search_service.text_search(query, processed_filters, max_results)
        elif search_type == "vector":
            results = await search_service.vector_search(query, processed_filters, max_results)
        elif search_type == "semantic":
            results = search_service.semantic_search(query, processed_filters, max_results)
        else:  # hybrid (default)
            results = await search_service.hybrid_search(query, processed_filters, max_results)
        
        # Format results
        if not results:
            filter_desc = f" (with filters: {filters})" if filters else ""
            return [types.TextContent(
                type="text",
                text=f"[SEARCH] No documents found for query: '{query}'{filter_desc}"
            )]
        
        formatted_results = []
        for i, result in enumerate(results[:max_results], 1):
            result_text = f"## Result {i}\n"
            result_text += f"**Context:** {result.get('context_name', 'Unknown')}\n"
            result_text += f"**File:** {result.get('file_name', 'Unknown')}\n"
            result_text += f"**Title:** {result.get('title', 'No title')}\n"
            result_text += f"**Chunk:** {result.get('chunk_index', 'N/A')}\n"
            
            if include_content and 'content' in result:
                content = result['content'].strip()
                if len(content) > 400:
                    content = content[:400] + "..."
                result_text += f"**Content:**\n```\n{content}\n```\n"
            
            score = result.get('@search.score', 'N/A')
            if isinstance(score, (int, float)):
                result_text += f"**Relevance Score:** {score:.4f}\n"
            else:
                result_text += f"**Relevance Score:** {score}\n"
            result_text += "\n---\n"
            formatted_results.append(result_text)
        
        response = f"# Search Results\n\n**Query:** \"{query}\"\n**Search Type:** {search_type.upper()}\n**Results Found:** {len(results)}\n\n" + "\n".join(formatted_results)
        
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
        include_stats = arguments.get("include_stats", True)
        max_contexts = arguments.get("max_contexts", 100)
        
        logger.info(f"[CONTEXTS] Getting contexts: stats={include_stats}")
        
        # Use Azure Search facets to get context distribution
        facets = [f"context_name,count:{max_contexts}"]
        
        results = search_service.search_client.search(
            search_text="*",
            facets=facets,
            top=0  # Only need facet data
        )
        
        facet_data = results.get_facets()
        contexts = facet_data.get("context_name", [])
        
        if not contexts:
            return [types.TextContent(
                type="text",
                text="# Document Contexts\n\n**No contexts found in the index**\n\nThis might indicate:\n- Empty search index\n- Connection issues\n- No documents uploaded yet"
            )]
        
        # Format response
        response = f"# Document Contexts\n\n**Total Contexts Found:** {len(contexts)}\n\n"
        
        for i, context in enumerate(contexts[:max_contexts], 1):
            context_name = context["value"]
            doc_count = context["count"] if include_stats else "N/A"
            
            response += f"**{i}. {context_name}**"
            if include_stats:
                response += f" - *{doc_count} documents*"
            response += "\n"
        
        if len(contexts) > max_contexts:
            response += f"\n*... and {len(contexts) - max_contexts} more contexts available*"
        
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
        response = f"# Search Index Summary\n\n"
        response += f"**Total Documents:** {total_count:,}\n\n"
        
        if include_facets:
            # Context distribution
            contexts = facet_data.get("context_name", [])
            response += f"## Contexts Distribution\n"
            response += f"**Found {len(contexts)} contexts:**\n"
            context_names = [c["value"] for c in contexts[:5]]
            for i, ctx in enumerate(contexts[:5], 1):
                response += f"  {i}. **{ctx['value']}** - *{ctx['count']:,} documents*\n"
            if len(contexts) > 5:
                response += f"  ... *and {len(contexts) - 5} more contexts*\n"
            response += "\n"
            
            # File type distribution
            file_types = facet_data.get("file_type", [])
            response += f"## File Types Distribution\n"
            for ft in file_types[:10]:
                response += f"- **{ft['value']}**: {ft['count']:,} files\n"
            response += "\n"
            
            # Category distribution
            categories = facet_data.get("category", [])
            if categories:
                response += f"## Categories\n"
                for cat in categories[:10]:
                    response += f"- **{cat['value']}**: {cat['count']:,} documents\n"
                response += "\n"
            
            # Popular tags
            tags = facet_data.get("tags", [])
            if tags:
                response += f"## Popular Tags\n"
                for tag in tags[:15]:
                    response += f"- `{tag['value']}` ({tag['count']:,}) "
                response += "\n"
        
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
    
    # Use search client directly with facets for file exploration
    results = search_service.search_client.search(
        search_text="*",
        filter=FilterBuilder.build_filter(filters) if filters else None,
        facets=["file_name,count:1000"],
        top=0
    )
    
    facet_data = results.get_facets()
    files = facet_data.get("file_name", [])
    
    context_desc = f" in **{context_name}**" if context_name else ""
    response = f"# File Structure\n\n**Files Found:** {len(files)}{context_desc}\n\n"
    
    for i, file_info in enumerate(files[:max_items], 1):
        file_name = file_info['value']
        chunk_count = file_info['count']
            
        response += f"**{i}. {file_name}**\n"
        response += f"   - *{chunk_count} chunks*\n\n"
    
    if len(files) > max_items:
        response += f"*... and {len(files) - max_items} more files available*\n"
    
    return [types.TextContent(type="text", text=response)]


async def _explore_chunks(search_service, arguments: dict) -> list[types.TextContent]:
    """Explore chunk structure with simple retrieval"""
    context_name = arguments.get("context_name")
    file_name = arguments.get("file_name")
    max_items = arguments.get("max_items", 50)
    
    filters = {}
    if context_name:
        filters["context_name"] = context_name
    if file_name:
        filters["file_name"] = file_name
    
    # Use Azure Search with proper sorting
    results = search_service.search_client.search(
        search_text="*",
        filter=FilterBuilder.build_filter(filters) if filters else None,
        select="file_name,chunk_index,context_name,title,content",
        top=max_items
    )
    
    chunks = list(results)
    
    # Sort chunks by file name and chunk index for consistent ordering
    chunks = sorted(chunks, key=lambda x: (x.get('file_name', ''), x.get('chunk_index', '')))
    
    file_desc = f" from **{file_name}**" if file_name else ""
    context_desc = f" in **{context_name}**" if context_name else ""
    
    response = f"# Document Chunks\n\n**Chunks Found:** {len(chunks)}{file_desc}{context_desc}\n\n"
    
    for i, chunk in enumerate(chunks, 1):
        response += f"## Chunk {i}\n"
        response += f"**File:** {chunk.get('file_name', 'Unknown')}\n"
        response += f"**ID:** {chunk.get('chunk_index', 'N/A')}\n"
        response += f"**Title:** {chunk.get('title', 'No title')}\n"
        
        content = chunk.get('content', '').strip()
        if len(content) > 150:
            content = content[:150] + "..."
        response += f"**Preview:**\n```\n{content}\n```\n\n"
        
        if i >= max_items:
            break
    
    return [types.TextContent(type="text", text=response)]


async def _explore_categories(search_service, arguments: dict) -> list[types.TextContent]:
    """Explore category structure"""
    context_name = arguments.get("context_name")
    max_items = arguments.get("max_items", 50)
    
    filters = {}
    if context_name:
        filters["context_name"] = context_name
    
    # Use search client with facets for category exploration
    results = search_service.search_client.search(
        search_text="*",
        filter=FilterBuilder.build_filter(filters) if filters else None,
        facets=["category,count:1000"],
        top=0
    )
    
    facet_data = results.get_facets()
    categories = facet_data.get("category", [])
    
    context_desc = f" in **{context_name}**" if context_name else ""
    response = f"# Document Categories\n\n**Categories Found:** {len(categories)}{context_desc}\n\n"
    
    for i, cat_info in enumerate(categories[:max_items], 1):
        category_name = cat_info['value']
        doc_count = cat_info['count']
        response += f"**{i}. {category_name}**\n"
        response += f"   - *{doc_count:,} documents*\n\n"
    
    if len(categories) > max_items:
        response += f"*... and {len(categories) - max_items} more categories available*\n"
    
    return [types.TextContent(type="text", text=response)]
