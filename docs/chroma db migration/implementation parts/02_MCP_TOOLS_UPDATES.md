# Part 2: MCP Tools Updates 🛠️

## Overview

This document covers updating the **MCP (Model Context Protocol) Tools** to work with the new ChromaDB service. This includes replacing Azure-specific filtering throughout the MCP tool handlers and updating all search-related functionality to use ChromaDB's vector search capabilities.

## Why This Component is Critical 🎯

The MCP Tools serve as the **interface layer** between VS Code agents and the search service:

- **User-Facing**: Direct interaction point for VS Code users via MCP protocol
- **Search Operations**: Handles all document search, retrieval, and exploration requests
- **Filter Translation**: Converts user filter requests into ChromaDB-compatible queries
- **Result Formatting**: Formats ChromaDB results for optimal VS Code display

## MCP Tools Architecture 🏗️

### Current MCP Tools Structure

```
src/mcp_server/tools/
├── universal_tools.py          # Main MCP tool handlers
├── tool_router.py             # Tool routing logic
└── __init__.py
```

### Key MCP Tool Functions Requiring Updates

| MCP Tool Function                                | Current Azure Dependencies            | ChromaDB Changes Required               |
| ------------------------------------------------ | ------------------------------------- | --------------------------------------- |
| `mcp_documentation_search_documents()`           | FilterBuilder + multiple search types | ChromaDB filtering + vector-only search |
| `mcp_documentation_get_document_content()`       | OData filtering for content retrieval | ChromaDB metadata filtering             |
| `mcp_documentation_explore_document_structure()` | Azure index exploration               | ChromaDB collection exploration         |
| `mcp_documentation_get_document_contexts()`      | Azure faceting for contexts           | ChromaDB metadata aggregation           |
| `mcp_documentation_get_index_summary()`          | Azure index statistics                | ChromaDB collection statistics          |

## Part 2 Implementation Details 📝

### 2.1 Universal Tools Updates

**File: `src/mcp_server/tools/universal_tools.py`**

The main changes involve:

1. **Import replacements**: Remove Azure imports, add ChromaDB imports
2. **Filter handling**: Replace FilterBuilder with ChromaDBFilterBuilder
3. **Search consolidation**: All search types route to vector search
4. **Result processing**: Handle ChromaDB result format

```python
"""
Universal MCP Tools - ChromaDB Version
====================================

Updated MCP tool handlers for ChromaDB vector search backend
"""

import asyncio
from typing import Dict, Any, List, Optional
from mcp import types
import logging

# ChromaDB imports (NEW)
from common.chromadb_service import ChromaDBService
from common.chromadb_filter_builder import ChromaDBFilterBuilder

# Remove Azure imports - these are no longer needed:
# from common.azure_cognitive_search import FilterBuilder

logger = logging.getLogger(__name__)

class ToolRouter:
    """MCP Tool router updated for ChromaDB backend"""

    def __init__(self, search_service: ChromaDBService):
        """Initialize with ChromaDB service"""
        self.search_service = search_service

    async def route_tool_call(self, tool_name: str, arguments: dict) -> list[types.TextContent]:
        """Route MCP tool calls to appropriate handlers"""

        tool_handlers = {
            "mcp_documentation_search_documents": self.handle_search_documents,
            "mcp_documentation_get_document_content": self.handle_get_document_content,
            "mcp_documentation_explore_document_structure": self.handle_explore_document_structure,
            "mcp_documentation_get_document_contexts": self.handle_get_document_contexts,
            "mcp_documentation_get_index_summary": self.handle_get_index_summary,
        }

        handler = tool_handlers.get(tool_name)
        if handler:
            return await handler(arguments)
        else:
            return [types.TextContent(
                type="text",
                text=f"[ERROR] Unknown tool: {tool_name}"
            )]

    # ===== SEARCH DOCUMENTS =====

    async def handle_search_documents(self, arguments: dict) -> list[types.TextContent]:
        """Handle universal document search with ChromaDB filtering"""
        try:
            # Extract parameters
            query = arguments.get("query", "")
            search_type = arguments.get("search_type", "hybrid")  # Default to hybrid (routes to vector)
            filters = arguments.get("filters", {})
            max_results = arguments.get("max_results", 5)
            include_content = arguments.get("include_content", True)

            logger.info(f"[SEARCH] Universal search: query='{query}', type={search_type}, filters={filters}")

            # Process filters for ChromaDB compatibility
            processed_filters = self._process_search_filters(filters)

            # ALL search types now use vector search (ChromaDB limitation)
            # text_search, hybrid_search, semantic_search all route to vector_search
            logger.info(f"[SEARCH] Using vector search (ChromaDB backend)")
            results = await self.search_service.vector_search(query, processed_filters, max_results)

            # Format results for MCP response
            if not results:
                filter_desc = f" (with filters: {filters})" if filters else ""
                return [types.TextContent(
                    type="text",
                    text=f"[SEARCH] No documents found for query: '{query}'{filter_desc}"
                )]

            # Format results for display
            return self._format_search_results(results, include_content, max_results)

        except Exception as e:
            logger.error(f"[ERROR] Search failed: {e}")
            return [types.TextContent(
                type="text",
                text=f"[ERROR] Search failed: {str(e)}"
            )]

    def _process_search_filters(self, filters: dict) -> dict:
        """Process and convert filters for ChromaDB compatibility"""
        if not filters:
            return {}

        processed_filters = {}

        for key, value in filters.items():
            # Handle special filter mappings
            if key == "chunk_pattern":
                # Map chunk_pattern to chunk_index for ChromaDB
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
                    # For list of tags, we need to search within the tags string
                    # This is a limitation - ChromaDB doesn't have contains operator for strings
                    processed_filters["tags"] = value[0] if value else None  # Use first tag only
                else:
                    processed_filters["tags"] = value
            else:
                # Pass through other filters as-is
                processed_filters[key] = value

        return processed_filters

    def _format_search_results(self, results: list, include_content: bool, max_results: int) -> list[types.TextContent]:
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
                result_text += f"\n**Content:**\n{result['content']}\n"

            formatted_results.append(types.TextContent(type="text", text=result_text))

        return formatted_results

    # ===== GET DOCUMENT CONTENT =====

    async def handle_get_document_content(self, arguments: dict) -> list[types.TextContent]:
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
                results = await self.search_service.vector_search("", filters, 50)  # Get more results for content

            elif document_ids:
                # Get specific documents by ID
                if isinstance(document_ids, str):
                    document_ids = [document_ids]

                logger.info(f"[CONTENT] Getting documents by IDs: {document_ids}")

                # ChromaDB get by IDs - we need to use the collection directly
                try:
                    chromadb_results = self.search_service.collection.get(ids=document_ids)
                    results = self.search_service._format_search_results({
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

            return self._format_content_results(results, include_metadata, max_content_length)

        except Exception as e:
            logger.error(f"[ERROR] Content retrieval failed: {e}")
            return [types.TextContent(type="text", text=f"[ERROR] Content retrieval failed: {e}")]

    def _format_content_results(self, results: list, include_metadata: bool, max_content_length: Optional[int]) -> list[types.TextContent]:
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

            formatted_results.append(types.TextContent(type="text", text=content_text))

        return formatted_results

    # ===== EXPLORE DOCUMENT STRUCTURE =====

    async def handle_explore_document_structure(self, arguments: dict) -> list[types.TextContent]:
        """Handle document structure exploration with ChromaDB"""
        try:
            structure_type = arguments.get("structure_type", "contexts")
            context_name = arguments.get("context_name")
            file_name = arguments.get("file_name")
            max_items = arguments.get("max_items", 50)

            logger.info(f"[EXPLORE] Structure type: {structure_type}, context: {context_name}, file: {file_name}")

            if structure_type == "contexts":
                return await self._explore_contexts(max_items)
            elif structure_type == "files":
                return await self._explore_files(context_name, max_items)
            elif structure_type == "chunks":
                return await self._explore_chunks(context_name, file_name, max_items)
            elif structure_type == "categories":
                return await self._explore_categories(context_name, max_items)
            else:
                return [types.TextContent(
                    type="text",
                    text=f"[ERROR] Unknown structure type: {structure_type}"
                )]

        except Exception as e:
            logger.error(f"[ERROR] Structure exploration failed: {e}")
            return [types.TextContent(type="text", text=f"[ERROR] Structure exploration failed: {e}")]

    async def _explore_contexts(self, max_items: int) -> list[types.TextContent]:
        """Explore available contexts in ChromaDB"""
        try:
            # Get sample of documents to analyze contexts
            results = await self.search_service.vector_search("", {}, max_items * 2)  # Get more to find unique contexts

            # Extract unique contexts
            contexts = {}
            for result in results:
                context = result.get('context_name')
                if context:
                    if context not in contexts:
                        contexts[context] = 0
                    contexts[context] += 1

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

    async def _explore_files(self, context_name: Optional[str], max_items: int) -> list[types.TextContent]:
        """Explore files in a specific context"""
        try:
            # Build filter for context
            filters = {}
            if context_name:
                filters["context_name"] = context_name

            # Get documents
            results = await self.search_service.vector_search("", filters, max_items * 2)

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

    async def _explore_chunks(self, context_name: Optional[str], file_name: Optional[str], max_items: int) -> list[types.TextContent]:
        """Explore chunks in a specific file"""
        try:
            # Build filter
            filters = {}
            if context_name:
                filters["context_name"] = context_name
            if file_name:
                filters["file_name"] = file_name

            if not filters:
                return [types.TextContent(
                    type="text",
                    text="[ERROR] Must provide context_name or file_name to explore chunks"
                )]

            # Get document chunks
            results = await self.search_service.vector_search("", filters, max_items)

            if not results:
                return [types.TextContent(
                    type="text",
                    text=f"[EXPLORE] No chunks found matching criteria"
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

    async def _explore_categories(self, context_name: Optional[str], max_items: int) -> list[types.TextContent]:
        """Explore categories in the collection"""
        try:
            # Build filter for context
            filters = {}
            if context_name:
                filters["context_name"] = context_name

            # Get documents
            results = await self.search_service.vector_search("", filters, max_items * 2)

            # Extract unique categories
            categories = {}
            for result in results:
                category = result.get('category')
                if category:
                    if category not in categories:
                        categories[category] = 0
                    categories[category] += 1

            if not categories:
                context_desc = f" in context '{context_name}'" if context_name else ""
                return [types.TextContent(
                    type="text",
                    text=f"[EXPLORE] No categories found{context_desc}"
                )]

            # Format category results
            category_text = f"## Categories{' in ' + context_name if context_name else ''}\n\n"
            for category, count in sorted(categories.items())[:max_items]:
                category_text += f"**{category}:** {count} documents\n"

            return [types.TextContent(type="text", text=category_text)]

        except Exception as e:
            return [types.TextContent(type="text", text=f"[ERROR] Category exploration failed: {e}")]

    # ===== GET DOCUMENT CONTEXTS =====

    async def handle_get_document_contexts(self, arguments: dict) -> list[types.TextContent]:
        """Handle getting document contexts with statistics"""
        try:
            include_stats = arguments.get("include_stats", True)
            max_contexts = arguments.get("max_contexts", 100)

            logger.info(f"[CONTEXTS] Getting contexts, include_stats={include_stats}, max={max_contexts}")

            # Use existing context exploration logic
            context_results = await self._explore_contexts(max_contexts)

            if include_stats:
                # Add collection statistics
                stats = self.search_service.get_index_stats()
                stats_text = f"\n## Collection Statistics\n"
                stats_text += f"**Total Documents:** {stats.get('document_count', 0)}\n"
                stats_text += f"**Collection Name:** {stats.get('collection_name', 'unknown')}\n"
                stats_text += f"**Storage Path:** {stats.get('storage_path', 'unknown')}\n"

                # Append stats to first result
                if context_results:
                    original_text = context_results[0].text
                    context_results[0] = types.TextContent(
                        type="text",
                        text=original_text + stats_text
                    )

            return context_results

        except Exception as e:
            logger.error(f"[ERROR] Get contexts failed: {e}")
            return [types.TextContent(type="text", text=f"[ERROR] Get contexts failed: {e}")]

    # ===== GET INDEX SUMMARY =====

    async def handle_get_index_summary(self, arguments: dict) -> list[types.TextContent]:
        """Handle getting index summary and statistics"""
        try:
            include_facets = arguments.get("include_facets", True)
            facet_limit = arguments.get("facet_limit", 50)

            logger.info(f"[SUMMARY] Getting index summary, facets={include_facets}, limit={facet_limit}")

            # Get basic collection statistics
            stats = self.search_service.get_index_stats()

            summary_text = "## ChromaDB Collection Summary\n\n"
            summary_text += f"**Collection Name:** {stats.get('collection_name')}\n"
            summary_text += f"**Total Documents:** {stats.get('document_count', 0)}\n"
            summary_text += f"**Unique Contexts:** {stats.get('context_count', 0)}\n"
            summary_text += f"**Storage Location:** {stats.get('storage_path')}\n\n"

            # Add facet information if requested
            if include_facets:
                summary_text += "## Document Distribution\n\n"

                # Get sample documents for facet analysis
                sample_results = await self.search_service.vector_search("", {}, facet_limit * 2)

                # Analyze contexts
                contexts = {}
                categories = {}
                file_types = {}

                for result in sample_results:
                    # Count contexts
                    context = result.get('context_name')
                    if context:
                        contexts[context] = contexts.get(context, 0) + 1

                    # Count categories
                    category = result.get('category')
                    if category:
                        categories[category] = categories.get(category, 0) + 1

                    # Count file types
                    file_type = result.get('file_type')
                    if file_type:
                        file_types[file_type] = file_types.get(file_type, 0) + 1

                # Add facet results
                if contexts:
                    summary_text += "### By Context:\n"
                    for context, count in sorted(contexts.items(), key=lambda x: x[1], reverse=True)[:facet_limit]:
                        summary_text += f"- **{context}:** {count} documents\n"
                    summary_text += "\n"

                if categories:
                    summary_text += "### By Category:\n"
                    for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True)[:facet_limit]:
                        summary_text += f"- **{category}:** {count} documents\n"
                    summary_text += "\n"

                if file_types:
                    summary_text += "### By File Type:\n"
                    for file_type, count in sorted(file_types.items(), key=lambda x: x[1], reverse=True)[:facet_limit]:
                        summary_text += f"- **{file_type}:** {count} documents\n"

            return [types.TextContent(type="text", text=summary_text)]

        except Exception as e:
            logger.error(f"[ERROR] Index summary failed: {e}")
            return [types.TextContent(type="text", text=f"[ERROR] Index summary failed: {e}")]


# Standalone handler functions for backwards compatibility
async def handle_search_documents(search_service: ChromaDBService, arguments: dict) -> list[types.TextContent]:
    """Standalone search documents handler"""
    router = ToolRouter(search_service)
    return await router.handle_search_documents(arguments)

async def handle_get_document_content(search_service: ChromaDBService, arguments: dict) -> list[types.TextContent]:
    """Standalone get document content handler"""
    router = ToolRouter(search_service)
    return await router.handle_get_document_content(arguments)

async def handle_explore_document_structure(search_service: ChromaDBService, arguments: dict) -> list[types.TextContent]:
    """Standalone explore document structure handler"""
    router = ToolRouter(search_service)
    return await router.handle_explore_document_structure(arguments)

async def handle_get_document_contexts(search_service: ChromaDBService, arguments: dict) -> list[types.TextContent]:
    """Standalone get document contexts handler"""
    router = ToolRouter(search_service)
    return await router.handle_get_document_contexts(arguments)

async def handle_get_index_summary(search_service: ChromaDBService, arguments: dict) -> list[types.TextContent]:
    """Standalone get index summary handler"""
    router = ToolRouter(search_service)
    return await router.handle_get_index_summary(arguments)
```

### 2.2 Server Configuration Updates

**File: `src/mcp_server/server.py`**

Update the server initialization to use ChromaDB service:

```python
"""
Documentation Retrieval MCP Server - ChromaDB Version
====================================================

Updated for ChromaDB backend with vector-only search capabilities
"""

import asyncio
import logging
from contextual import mcp
from mcp import server, types
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions

# ChromaDB imports (NEW)
from common.chromadb_service import ChromaDBService
from common.embedding_service import get_embedding_generator

# MCP Tools
from mcp_server.tools.universal_tools import ToolRouter

# Remove Azure imports - no longer needed:
# from common.azure_cognitive_search import get_azure_search_service

logger = logging.getLogger(__name__)

# Create the MCP server instance
app = server.Server("documentation-retrieval-chromadb")

# Global instances
search_service = None
embedding_generator = None
tool_router: Optional[ToolRouter] = None

async def initialize_services():
    """Initialize ChromaDB search and embedding services"""
    global search_service, embedding_generator, tool_router

    if search_service is None:
        logger.info("[INFO] Initializing ChromaDB search service...")
        search_service = ChromaDBService()  # Uses environment variables for config

    if embedding_generator is None:
        logger.info("[INFO] Initializing embedding services...")
        embedding_generator = get_embedding_generator()

    if tool_router is None:
        logger.info("[INFO] Initializing tool router...")
        tool_router = ToolRouter(search_service)

    return search_service, embedding_generator, tool_router

@app.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available MCP tools for ChromaDB backend"""
    return [
        types.Tool(
            name="mcp_documentation_search_documents",
            description="Search documents using vector search with comprehensive filtering options",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query for semantic/vector search"
                    },
                    "search_type": {
                        "type": "string",
                        "enum": ["vector", "text", "hybrid", "semantic"],
                        "default": "vector",
                        "description": "Search type (all route to vector search in ChromaDB)"
                    },
                    "filters": {
                        "type": "object",
                        "description": "Metadata filters for document search",
                        "properties": {
                            "context_name": {"type": "string"},
                            "file_name": {"type": "string"},
                            "category": {"type": "string"},
                            "file_type": {"type": "string"},
                            "tags": {"type": "string"}
                        }
                    },
                    "max_results": {
                        "type": "integer",
                        "default": 5,
                        "description": "Maximum number of results to return"
                    },
                    "include_content": {
                        "type": "boolean",
                        "default": True,
                        "description": "Include document content in results"
                    }
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="mcp_documentation_get_document_content",
            description="Get full content of specific documents by ID or context/file",
            inputSchema={
                "type": "object",
                "properties": {
                    "document_ids": {
                        "oneOf": [
                            {"type": "string"},
                            {"type": "array", "items": {"type": "string"}}
                        ],
                        "description": "Document ID(s) to retrieve"
                    },
                    "context_and_file": {
                        "type": "object",
                        "properties": {
                            "context_name": {"type": "string"},
                            "file_name": {"type": "string"}
                        },
                        "description": "Get all chunks for a specific file within a context"
                    },
                    "include_metadata": {
                        "type": "boolean",
                        "default": True,
                        "description": "Include document metadata"
                    },
                    "max_content_length": {
                        "type": "integer",
                        "description": "Maximum content length per document"
                    }
                }
            }
        ),
        types.Tool(
            name="mcp_documentation_explore_document_structure",
            description="Explore document structure - contexts, files, chunks, or categories",
            inputSchema={
                "type": "object",
                "properties": {
                    "structure_type": {
                        "type": "string",
                        "enum": ["contexts", "files", "chunks", "categories"],
                        "default": "contexts",
                        "description": "Type of structure to explore"
                    },
                    "context_name": {
                        "type": "string",
                        "description": "Filter by specific context"
                    },
                    "file_name": {
                        "type": "string",
                        "description": "Filter by specific file"
                    },
                    "max_items": {
                        "type": "integer",
                        "default": 50,
                        "description": "Maximum items to return"
                    }
                },
                "required": ["structure_type"]
            }
        ),
        types.Tool(
            name="mcp_documentation_get_document_contexts",
            description="Get all available document contexts with statistics",
            inputSchema={
                "type": "object",
                "properties": {
                    "include_stats": {
                        "type": "boolean",
                        "default": True,
                        "description": "Include document counts per context"
                    },
                    "max_contexts": {
                        "type": "integer",
                        "default": 100,
                        "description": "Maximum contexts to return"
                    }
                }
            }
        ),
        types.Tool(
            name="mcp_documentation_get_index_summary",
            description="Get comprehensive index statistics and document distribution",
            inputSchema={
                "type": "object",
                "properties": {
                    "include_facets": {
                        "type": "boolean",
                        "default": True,
                        "description": "Include facet distributions"
                    },
                    "facet_limit": {
                        "type": "integer",
                        "default": 50,
                        "description": "Maximum facet values per field"
                    }
                }
            }
        )
    ]

@app.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """Handle MCP tool calls with ChromaDB backend"""
    try:
        # Ensure services are initialized
        await initialize_services()

        # Route tool call through tool router
        return await tool_router.route_tool_call(name, arguments)

    except Exception as e:
        logger.error(f"[ERROR] Tool call failed: {name} - {e}")
        return [types.TextContent(
            type="text",
            text=f"[ERROR] Tool call failed: {str(e)}"
        )]

async def main():
    """Main entry point for the ChromaDB MCP server"""
    logger.info("[START] Starting Documentation Retrieval MCP Server (ChromaDB)")

    try:
        # Test connections on startup
        logger.info("[CONNECT] Testing connections...")

        # Initialize and test ChromaDB functionality
        global search_service, embedding_generator
        search_service = ChromaDBService()
        embedding_generator = get_embedding_generator()

        # Test ChromaDB connection
        if search_service.test_connection():
            logger.info("[SUCCESS] ChromaDB connection successful")

            # Display collection statistics
            stats = search_service.get_index_stats()
            logger.info(f"[INFO] Collection: {stats.get('collection_name')}")
            logger.info(f"[INFO] Documents: {stats.get('document_count', 0)}")
            logger.info(f"[INFO] Contexts: {stats.get('context_count', 0)}")
        else:
            logger.error("[ERROR] ChromaDB connection failed")

        # Test embedding service
        if embedding_generator.test_connection():
            logger.info("[SUCCESS] Embedding service connection successful")
        else:
            logger.error("[ERROR] Embedding service connection failed")

        # Start the MCP server
        logger.info("[READY] MCP Server ready for connections")
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await app.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="documentation-retrieval-chromadb",
                    server_version="2.0.0",
                    capabilities=app.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={}
                    )
                )
            )

    except KeyboardInterrupt:
        logger.info("[STOP] Server stopped by user")
    except Exception as e:
        logger.error(f"[FATAL] Server failed to start: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
```

## Testing Strategy for Part 2 🧪

### Integration Tests for MCP Tools

**File: `tests/integration/test_mcp_tools_chromadb.py`**

```python
import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
from mcp import types

from src.mcp_server.tools.universal_tools import ToolRouter
from src.common.chromadb_service import ChromaDBService

class TestMCPToolsIntegration:

    @pytest.fixture
    def mock_chromadb_service(self):
        """Create mock ChromaDB service for testing"""
        service = Mock(spec=ChromaDBService)

        # Mock vector_search method
        service.vector_search = Mock(return_value=[
            {
                'id': 'doc1',
                'content': 'This is test document content',
                'context_name': 'test_context',
                'file_name': 'test_file.md',
                'title': 'Test Document',
                'category': 'manual',
                'file_type': 'md',
                '@search.score': 0.85
            },
            {
                'id': 'doc2',
                'content': 'Another test document',
                'context_name': 'test_context',
                'file_name': 'test_file2.md',
                'title': 'Second Document',
                'category': 'guide',
                'file_type': 'md',
                '@search.score': 0.72
            }
        ])

        # Mock get_index_stats method
        service.get_index_stats = Mock(return_value={
            'collection_name': 'test_collection',
            'document_count': 100,
            'context_count': 5,
            'storage_path': './test_data'
        })

        # Mock collection for direct access
        mock_collection = MagicMock()
        mock_collection.get.return_value = {
            'ids': ['doc1'],
            'documents': ['Test content'],
            'metadatas': [{'title': 'Test Doc'}]
        }
        service.collection = mock_collection
        service._format_search_results = Mock(return_value=[{
            'id': 'doc1',
            'content': 'Test content',
            'title': 'Test Doc',
            '@search.score': 1.0
        }])

        return service

    @pytest.fixture
    def tool_router(self, mock_chromadb_service):
        """Create tool router with mocked service"""
        return ToolRouter(mock_chromadb_service)

    @pytest.mark.asyncio
    async def test_search_documents_basic(self, tool_router, mock_chromadb_service):
        """Test basic document search functionality"""
        arguments = {
            "query": "test query",
            "search_type": "vector",
            "max_results": 5
        }

        results = await tool_router.handle_search_documents(arguments)

        # Verify results structure
        assert isinstance(results, list)
        assert len(results) == 2  # Two mock documents

        for result in results:
            assert isinstance(result, types.TextContent)
            assert result.type == "text"
            assert "Result" in result.text
            assert "Context:" in result.text
            assert "File:" in result.text

        # Verify service was called correctly
        mock_chromadb_service.vector_search.assert_called_once()
        call_args = mock_chromadb_service.vector_search.call_args
        assert call_args[0][0] == "test query"  # Query parameter
        assert call_args[0][2] == 5  # Max results parameter

    @pytest.mark.asyncio
    async def test_search_documents_with_filters(self, tool_router, mock_chromadb_service):
        """Test document search with filters"""
        arguments = {
            "query": "test query",
            "filters": {
                "context_name": "docs",
                "category": "manual",
                "file_type": "pdf"
            },
            "max_results": 3
        }

        results = await tool_router.handle_search_documents(arguments)

        # Verify filters were processed and passed
        mock_chromadb_service.vector_search.assert_called_once()
        call_args = mock_chromadb_service.vector_search.call_args

        filters_used = call_args[0][1]  # Second parameter (filters)
        assert filters_used["context_name"] == "docs"
        assert filters_used["category"] == "manual"
        assert filters_used["file_type"] == "pdf"

    @pytest.mark.asyncio
    async def test_get_document_content_by_context_file(self, tool_router, mock_chromadb_service):
        """Test getting document content by context and file"""
        arguments = {
            "context_and_file": {
                "context_name": "test_context",
                "file_name": "test_file.md"
            },
            "include_metadata": True
        }

        results = await tool_router.handle_get_document_content(arguments)

        # Verify results
        assert isinstance(results, list)
        assert len(results) == 2  # Two mock documents

        # Verify service was called with empty query (content retrieval)
        mock_chromadb_service.vector_search.assert_called()
        call_args = mock_chromadb_service.vector_search.call_args
        assert call_args[0][0] == ""  # Empty query for content retrieval

    @pytest.mark.asyncio
    async def test_get_document_content_by_ids(self, tool_router, mock_chromadb_service):
        """Test getting document content by IDs"""
        arguments = {
            "document_ids": ["doc1", "doc2"],
            "include_metadata": True
        }

        results = await tool_router.handle_get_document_content(arguments)

        # Verify collection.get was called with IDs
        mock_chromadb_service.collection.get.assert_called_with(ids=["doc1", "doc2"])

        # Verify results formatting
        assert isinstance(results, list)
        for result in results:
            assert isinstance(result, types.TextContent)
            assert "Document" in result.text

    @pytest.mark.asyncio
    async def test_explore_document_structure_contexts(self, tool_router, mock_chromadb_service):
        """Test exploring document contexts"""
        arguments = {
            "structure_type": "contexts",
            "max_items": 50
        }

        results = await tool_router.handle_explore_document_structure(arguments)

        # Verify service was called for context exploration
        mock_chromadb_service.vector_search.assert_called()

        # Verify results
        assert isinstance(results, list)
        assert len(results) == 1  # Single result with context summary
        assert "Available Contexts" in results[0].text

    @pytest.mark.asyncio
    async def test_get_index_summary(self, tool_router, mock_chromadb_service):
        """Test getting index summary"""
        arguments = {
            "include_facets": True,
            "facet_limit": 25
        }

        results = await tool_router.handle_get_index_summary(arguments)

        # Verify get_index_stats was called
        mock_chromadb_service.get_index_stats.assert_called_once()

        # Verify results contain expected information
        assert isinstance(results, list)
        assert len(results) == 1
        result_text = results[0].text
        assert "ChromaDB Collection Summary" in result_text
        assert "Collection Name:" in result_text
        assert "Total Documents:" in result_text

    @pytest.mark.asyncio
    async def test_error_handling(self, tool_router, mock_chromadb_service):
        """Test error handling in MCP tools"""
        # Configure service to raise exception
        mock_chromadb_service.vector_search.side_effect = Exception("Test error")

        arguments = {
            "query": "test query"
        }

        results = await tool_router.handle_search_documents(arguments)

        # Verify error is handled gracefully
        assert isinstance(results, list)
        assert len(results) == 1
        assert results[0].type == "text"
        assert "[ERROR]" in results[0].text
        assert "Test error" in results[0].text

    @pytest.mark.asyncio
    async def test_all_search_types_route_to_vector(self, tool_router, mock_chromadb_service):
        """Test that all search types route to vector search"""
        search_types = ["vector", "text", "hybrid", "semantic"]

        for search_type in search_types:
            # Reset mock
            mock_chromadb_service.vector_search.reset_mock()

            arguments = {
                "query": f"test {search_type} query",
                "search_type": search_type
            }

            await tool_router.handle_search_documents(arguments)

            # Verify vector_search was called regardless of search_type
            mock_chromadb_service.vector_search.assert_called_once()
```

## Integration Points with Other Components 🔗

### Dependencies from Part 1 (ChromaDB Service)

- **ChromaDBService**: Must be fully implemented before MCP tools can work
- **ChromaDBFilterBuilder**: Required for filter conversion in MCP tools
- **Service Interface**: MCP tools depend on consistent method signatures

### Provides to Part 3 (Document Processing)

- **Search Verification**: MCP tools can verify document uploads are searchable
- **Filter Testing**: Validates that document metadata is properly filterable
- **User Interface**: Provides the interface users will interact with

## Completion Criteria ✅

Part 2 is complete when:

1. **✅ All MCP tool functions updated** to use ChromaDB service
2. **✅ Azure imports removed** from MCP tools
3. **✅ Filter conversion working** throughout all tools
4. **✅ Search consolidation complete** - all search types route to vector
5. **✅ Integration tests passing** for all MCP tool functions
6. **✅ Error handling robust** for ChromaDB-specific issues
7. **✅ Result formatting optimized** for ChromaDB output structure
8. **✅ Server configuration updated** to use ChromaDB service

## Known Limitations 🚨

### ChromaDB-Specific Constraints

1. **Tags Filtering**: ChromaDB stores tags as comma-separated strings, limiting complex tag queries
2. **Text Search**: No native text/keyword search - all searches are semantic/vector
3. **Complex Filters**: OData expressions with OR logic require manual conversion
4. **Faceting**: Limited faceting capabilities compared to Azure's dynamic faceting

### Workarounds Implemented

1. **Tag Search**: Use first tag only for filtering, or implement contains-like logic
2. **Search Types**: All search types route to vector search transparently
3. **Filter Fallbacks**: Complex filters fall back to basic equality matching
4. **Manual Faceting**: Calculate facets by sampling documents rather than native aggregation

## Next Steps ➡️

After completing Part 2:

1. **Part 3**: Update Document Processing Pipeline to work with ChromaDB
2. **End-to-End Testing**: Test complete workflow from upload to search
3. **Performance Optimization**: Tune ChromaDB parameters for optimal search speed
4. **User Documentation**: Update MCP tool usage guides for ChromaDB backend

---

**🛠️ Part 2 provides the user interface layer that depends on Part 1 and enables Part 3 testing. Complete Part 1 first, then implement Part 2 before tackling document processing updates.**
