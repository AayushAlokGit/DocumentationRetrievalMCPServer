"""
Universal Document Search Tool Handlers for ChromaDB
====================================================

Implementation of MCP tools using ChromaDB as the backend search service.
These tools provide the same functionality as Azure Cognitive Search tools
but use ChromaDB's vector-only search capabilities.

Key differences from Azure version:
- All search types route to vector search (ChromaDB limitation)
- Metadata filtering uses ChromaDB's native where clauses
- Basic statistics only
- Tags stored as comma-separated strings
"""

import logging
from typing import Dict, Any, Optional, List
import mcp.types as types

from src.common.vector_search_services.chromadb_service import ChromaDBService, ChromaDBFilterBuilder

logger = logging.getLogger("chroma-db-mcp")


async def handle_search_documents(search_service: ChromaDBService, arguments: dict) -> list[types.TextContent]:
    """Handle universal document search with ChromaDB vector search"""
    try:
        query = arguments.get("query", "")
        search_type = arguments.get("search_type", "vector")
        filters = arguments.get("filters", {})
        max_results = arguments.get("max_results", 5)
        include_content = arguments.get("include_content", True)
        
        logger.info(f"[SEARCH] ChromaDB search: query='{query}', type={search_type}, filters={filters}")
            
        # ALL search types route to vector search in ChromaDB (no text/hybrid/semantic search)
        logger.info(f"[SEARCH] Using vector search (ChromaDB backend)")
        results = await search_service.vector_search(query, filters, max_results)
        
        # Format results
        if not results:
            filter_desc = f" (with filters: {filters})" if filters else ""
            return [types.TextContent(
                type="text",
                text=f"[SEARCH] No documents found for query: '{query}'{filter_desc}"
            )]
        
        return _format_search_results(results, include_content, max_results)
        
    except Exception as e:
        logger.error(f"[ERROR] ChromaDB search failed: {e}")
        return [types.TextContent(
            type="text",
            text=f"[ERROR] Search failed: {str(e)}"
        )]


async def handle_get_document_content(search_service: ChromaDBService, arguments: dict) -> list[types.TextContent]:
    """Handle document content retrieval with ChromaDB filtering"""
    try:
        context_and_file = arguments.get("context_and_file")
        document_ids = arguments.get("document_ids")
        include_metadata = arguments.get("include_metadata", True)
        max_content_length = arguments.get("max_content_length")

        if context_and_file:
            # Get documents by context and file name
            context_name = context_and_file.get("context_name")
            file_name = context_and_file.get("file_name")

            # Build ChromaDB filter
            filters = {}
            if context_name:
                filters["context_name"] = context_name
            if file_name:
                filters["file_name"] = file_name

            logger.info(f"[CONTENT] Getting documents by context/file: {filters}")

            # Use vector search with empty query to get all matching documents
            results = await search_service.vector_search("", filters, 50)  # Get more results for content

        elif document_ids:
            # Get specific documents by ID
            if isinstance(document_ids, str):
                document_ids = [document_ids]

            logger.info(f"[CONTENT] Getting documents by IDs: {document_ids}")

            # ChromaDB get by IDs - use collection directly
            try:
                chromadb_results = search_service.collection.get(ids=document_ids)
                results = search_service._format_search_results({
                    'ids': [chromadb_results['ids']] if chromadb_results['ids'] else [[]],
                    'documents': [chromadb_results['documents']] if chromadb_results['documents'] else [[]],
                    'metadatas': [chromadb_results['metadatas']] if chromadb_results['metadatas'] else [[]],
                    'distances': [[0.0] * len(chromadb_results['ids'])] if chromadb_results['ids'] else [[]]
                })
            except Exception as e:
                return [types.TextContent(type="text", text=f"[ERROR] Failed to get documents by ID: {e}")]
        else:
            return [types.TextContent(
                type="text",
                text="[ERROR] Must provide either context_and_file or document_ids"
            )]

        # Format content results
        if not results:
            return [types.TextContent(
                type="text",
                text="[CONTENT] No documents found matching the criteria"
            )]

        return _format_content_results(results, include_metadata, max_content_length)

    except Exception as e:
        logger.error(f"[ERROR] Content retrieval failed: {e}")
        return [types.TextContent(type="text", text=f"[ERROR] Content retrieval failed: {e}")]


async def handle_explore_document_structure(search_service: ChromaDBService, arguments: dict) -> list[types.TextContent]:
    """Handle document structure exploration using ChromaDB sampling"""
    try:
        structure_type = arguments.get("structure_type", "contexts")
        context_name = arguments.get("context_name")
        file_name = arguments.get("file_name")
        max_items = arguments.get("max_items", 50)

        logger.info(f"[EXPLORE] Structure type: {structure_type}, context: {context_name}, file: {file_name}")

        if structure_type == "contexts":
            return await _explore_contexts(search_service, max_items)
        elif structure_type == "files":
            return await _explore_files(search_service, context_name, max_items)
        elif structure_type == "chunks":
            return await _explore_chunks(search_service, context_name, file_name, max_items)
        elif structure_type == "categories":
            return await _explore_categories(search_service, context_name, max_items)
        else:
            return [types.TextContent(
                type="text",
                text=f"[ERROR] Unknown structure type: {structure_type}"
            )]

    except Exception as e:
        logger.error(f"[ERROR] Structure exploration failed: {e}")
        return [types.TextContent(type="text", text=f"[ERROR] Structure exploration failed: {e}")]


async def handle_get_document_contexts(search_service: ChromaDBService, arguments: dict) -> list[types.TextContent]:
    """Handle document context discovery with statistics"""
    try:
        include_stats = arguments.get("include_stats", True)
        max_contexts = arguments.get("max_contexts", 100)

        logger.info(f"[CONTEXTS] Getting contexts, include_stats={include_stats}, max={max_contexts}")

        # Use sampling approach since ChromaDB doesn't have native faceting
        context_results = await _explore_contexts(search_service, max_contexts)

        if include_stats:
            # Add collection statistics
            stats = search_service.get_collection_stats()
            stats_text = f"\n## Collection Statistics\n"
            stats_text += f"**Total Documents:** {stats.get('document_count', 0)}\n"
            stats_text += f"**Collection Name:** {stats.get('collection_name', 'unknown')}\n"
            stats_text += f"**Storage Path:** {stats.get('storage_path', 'unknown')}\n"

            # Append stats to first result if available
            if context_results:
                original_text = context_results[0].text
                context_results[0] = types.TextContent(
                    type="text", 
                    text=original_text + stats_text
                )

        return context_results

    except Exception as e:
        logger.error(f"[ERROR] Context discovery failed: {e}")
        return [types.TextContent(
            type="text", 
            text=f"[ERROR] Context discovery failed: {str(e)}"
        )]


async def handle_get_index_summary(search_service: ChromaDBService, arguments: dict) -> list[types.TextContent]:
    """Handle ChromaDB collection summary with basic statistics"""
    try:
        logger.info(f"[SUMMARY] Getting collection summary")

        # Get basic collection statistics
        stats = search_service.get_collection_stats()

        summary_text = "## ChromaDB Collection Summary\n\n"
        summary_text += f"**Collection Name:** {stats.get('collection_name')}\n"
        summary_text += f"**Total Documents:** {stats.get('document_count', 0)}\n"
        summary_text += f"**Unique Contexts:** {stats.get('context_count', 0)}\n"
        summary_text += f"**Storage Location:** {stats.get('storage_path')}\n\n"

        return [types.TextContent(type="text", text=summary_text)]

    except Exception as e:
        logger.error(f"[ERROR] Index summary failed: {e}")
        return [types.TextContent(type="text", text=f"[ERROR] Index summary failed: {e}")]


# Helper functions

def _process_search_filters(filters: dict) -> dict:
    """Process and convert filters for ChromaDB compatibility"""
    if not filters:
        return {}

    processed_filters = {}

    for key, value in filters.items():
        # Handle special filter mappings
        if key == "chunk_index":
            processed_filters["chunk_index"] = value
        elif key == "file_name":
            # Direct mapping for file name filtering
            processed_filters["file_name"] = value
        elif key == "context_name":
            # Direct mapping for context filtering
            processed_filters["context_name"] = value
        elif key == "category":
            # Direct mapping for category filtering
            processed_filters["category"] = value
        elif key == "file_type":
            # Direct mapping for file type filtering
            processed_filters["file_type"] = value
        elif key == "tags":
            # Handle tags filtering (stored as comma-separated string in ChromaDB)
            if isinstance(value, list):
                # For list of tags, use first tag only (ChromaDB limitation)
                processed_filters["tags"] = value[0] if value else None
            else:
                processed_filters["tags"] = value
        else:
            # Pass through other filters as-is
            processed_filters[key] = value

    return processed_filters


def _format_search_results(results: list, include_content: bool, max_results: int) -> list[types.TextContent]:
    """Format search results for MCP display"""
    formatted_results = []

    for i, result in enumerate(results[:max_results], 1):
        result_text = f"## Result {i}\n"

        # Core document identification
        result_text += f"**Context:** {result.get('context_name', 'Unknown')}\n"
        result_text += f"**File:** {result.get('file_name', 'Unknown')}\n"
        result_text += f"**Title:** {result.get('title', 'No title')}\n"
        result_text += f"**Chunk:** {result.get('chunk_index', 'N/A')}\n"

        # Search relevance score
        score = result.get('@search.score', 0)
        result_text += f"**Relevance:** {score:.3f}\n"

        # Additional metadata
        if result.get('category'):
            result_text += f"**Category:** {result.get('category')}\n"
        if result.get('file_type'):
            result_text += f"**File Type:** {result.get('file_type')}\n"
        if result.get('tags'):
            result_text += f"**Tags:** {result.get('tags')}\n"

        # Include content if requested
        if include_content and result.get('content'):
            content = result['content']
            if len(content) > 400:
                content = content[:400] + "...[truncated]"
            result_text += f"\n**Content:**\n{content}\n"

        result_text += "\n---\n"
        formatted_results.append(types.TextContent(type="text", text=result_text))

    return formatted_results


def _format_content_results(results: list, include_metadata: bool, max_content_length: Optional[int]) -> list[types.TextContent]:
    """Format content results for MCP display"""
    formatted_results = []

    for i, result in enumerate(results, 1):
        content_text = f"## Document {i}\n"

        # Document identification
        content_text += f"**ID:** {result.get('id', 'Unknown')}\n"
        content_text += f"**File:** {result.get('file_name', 'Unknown')}\n"
        content_text += f"**Context:** {result.get('context_name', 'Unknown')}\n"

        # Metadata if requested
        if include_metadata:
            if result.get('title'):
                content_text += f"**Title:** {result.get('title')}\n"
            if result.get('category'):
                content_text += f"**Category:** {result.get('category')}\n"
            if result.get('file_type'):
                content_text += f"**File Type:** {result.get('file_type')}\n"
            if result.get('last_modified'):
                content_text += f"**Modified:** {result.get('last_modified')}\n"

        # Content with optional length limit
        content = result.get('content', '')
        if max_content_length and len(content) > max_content_length:
            content = content[:max_content_length] + "...[truncated]"

        content_text += f"\n**Content:**\n{content}\n"
        content_text += "\n---\n"

        formatted_results.append(types.TextContent(type="text", text=content_text))

    return formatted_results


async def _explore_contexts(search_service: ChromaDBService, max_items: int) -> list[types.TextContent]:
    """Explore available contexts in ChromaDB using sampling"""
    try:
        # Get sample of documents to analyze contexts
        results = await search_service.vector_search("", {}, max_items * 2)  # Get more to find unique contexts

        # Extract unique contexts
        contexts = {}
        for result in results:
            context = result.get('context_name')
            if context:
                contexts[context] = contexts.get(context, 0) + 1

        if not contexts:
            return [types.TextContent(
                type="text",
                text="[EXPLORE] No contexts found in collection"
            )]

        # Format context results
        context_text = "## Available Contexts\n\n"
        for context, count in sorted(contexts.items())[:max_items]:
            context_text += f"**{context}:** {count} documents\n"

        return [types.TextContent(type="text", text=context_text)]

    except Exception as e:
        return [types.TextContent(type="text", text=f"[ERROR] Context exploration failed: {e}")]


async def _explore_files(search_service: ChromaDBService, context_name: str, max_items: int) -> list[types.TextContent]:
    """Explore files in a context using ChromaDB sampling"""
    try:
        # Build filter for context
        filters = {}
        if context_name:
            filters["context_name"] = context_name

        # Get sample of documents
        results = await search_service.vector_search("", filters, max_items * 2)

        # Extract unique files
        files = {}
        for result in results:
            file_name = result.get('file_name')
            if file_name:
                if file_name not in files:
                    files[file_name] = {
                        'count': 0,
                        'file_type': result.get('file_type', 'unknown'),
                        'title': result.get('title', 'No title')
                    }
                files[file_name]['count'] += 1

        if not files:
            context_desc = f" in context '{context_name}'" if context_name else ""
            return [types.TextContent(
                type="text",
                text=f"[EXPLORE] No files found{context_desc}"
            )]

        # Format file results
        files_text = f"## Files{' in ' + context_name if context_name else ''}\n\n"
        for file_name, info in sorted(files.items())[:max_items]:
            files_text += f"**{file_name}** ({info['file_type']}): {info['count']} chunks\n"
            files_text += f"  Title: {info['title']}\n\n"

        return [types.TextContent(type="text", text=files_text)]

    except Exception as e:
        return [types.TextContent(type="text", text=f"[ERROR] File exploration failed: {e}")]


async def _explore_chunks(search_service: ChromaDBService, context_name: str, file_name: str, max_items: int) -> list[types.TextContent]:
    """Explore chunks for a specific file"""
    try:
        # Build filters
        filters = {}
        if context_name:
            filters["context_name"] = context_name
        if file_name:
            filters["file_name"] = file_name

        # Get chunks
        results = await search_service.vector_search("", filters, max_items)

        if not results:
            return [types.TextContent(
                type="text",
                text="[EXPLORE] No chunks found matching the criteria"
            )]

        # Format chunk results
        chunks_text = f"## Document Chunks\n\n"
        for i, result in enumerate(results, 1):
            chunks_text += f"**Chunk {i}** ({result.get('chunk_index', 'unknown')})\n"
            chunks_text += f"  File: {result.get('file_name', 'unknown')}\n"
            chunks_text += f"  Context: {result.get('context_name', 'unknown')}\n"

            # Show content preview
            content = result.get('content', '')
            preview = content[:200] + "..." if len(content) > 200 else content
            chunks_text += f"  Preview: {preview}\n\n"

        return [types.TextContent(type="text", text=chunks_text)]

    except Exception as e:
        return [types.TextContent(type="text", text=f"[ERROR] Chunk exploration failed: {e}")]


async def _explore_categories(search_service: ChromaDBService, context_name: str, max_items: int) -> list[types.TextContent]:
    """Explore categories using ChromaDB sampling"""
    try:
        # Build filter for context if specified
        filters = {}
        if context_name:
            filters["context_name"] = context_name

        # Get sample of documents
        results = await search_service.vector_search("", filters, max_items * 2)

        # Extract unique categories
        categories = {}
        for result in results:
            category = result.get('category')
            if category:
                categories[category] = categories.get(category, 0) + 1

        if not categories:
            context_desc = f" in context '{context_name}'" if context_name else ""
            return [types.TextContent(
                type="text",
                text=f"[EXPLORE] No categories found{context_desc}"
            )]

        # Format category results
        categories_text = f"## Categories{' in ' + context_name if context_name else ''}\n\n"
        for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True)[:max_items]:
            categories_text += f"**{category}:** {count} documents\n"

        return [types.TextContent(type="text", text=categories_text)]

    except Exception as e:
        return [types.TextContent(type="text", text=f"[ERROR] Category exploration failed: {e}")]
