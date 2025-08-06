"""
Work Item Documentation MCP Server
==================================

Model Context Protocol server that provides search capabilities for Work Item documentation
stored in Azure Cognitive Search. This server exposes tools for searching, retrieving,
and managing work item documentation for LLM interactions.
"""

import asyncio
import json
import logging
from typing import Any, Sequence, Optional, Dict, List
import sys
import os
from pathlib import Path

# Add src directory to path for imports
sys.path.append(str(Path(__file__).parent / "src"))

from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types

# Import our search functionality
from search_documents import DocumentSearcher
from azure_cognitive_search import get_azure_search_service
from embedding_service import get_embedding_generator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("work-items-mcp")

# Initialize the MCP server
app = Server("work-items-documentation")

# Global instances
searcher: Optional[DocumentSearcher] = None
embedding_generator = None


async def initialize_services():
    """Initialize search and embedding services"""
    global searcher, embedding_generator
    
    if searcher is None:
        logger.info("🔧 Initializing search services...")
        searcher = DocumentSearcher()
        
    if embedding_generator is None:
        logger.info("🔧 Initializing embedding services...")
        embedding_generator = get_embedding_generator()
        
    return searcher, embedding_generator


@app.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available tools for work item documentation search and management."""
    return [
        types.Tool(
            name="search_work_items",
            description="Search work item documentation using text, vector, or hybrid search",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query - can be keywords, questions, or concepts"
                    },
                    "search_type": {
                        "type": "string",
                        "enum": ["text", "vector", "hybrid"],
                        "description": "Type of search to perform (default: hybrid)",
                        "default": "hybrid"
                    },
                    "work_item_id": {
                        "type": "string",
                        "description": "Optional work item ID to filter results to specific work item"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default: 5)",
                        "default": 5,
                        "minimum": 1,
                        "maximum": 20
                    }
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="get_work_item_list",
            description="Get a list of all available work item IDs in the documentation index",
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        ),
        types.Tool(
            name="get_work_item_summary",
            description="Get summary information about work items including document counts",
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False
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
                        "description": "Search query for the work item"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default: 5)",
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
            description="Perform semantic/vector search to find conceptually similar content",
            inputSchema={
                "type": "object",
                "properties": {
                    "concept": {
                        "type": "string",
                        "description": "Concept, idea, or question to search for semantically"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default: 5)",
                        "default": 5,
                        "minimum": 1,
                        "maximum": 15
                    }
                },
                "required": ["concept"]
            }
        )
    ]


@app.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """Handle tool calls for work item documentation operations."""
    global searcher
    
    try:
        # Initialize searcher if not already done
        if searcher is None:
            searcher = DocumentSearcher()
            logger.info("✅ DocumentSearcher initialized")
        
        if name == "search_work_items":
            return await _handle_search_work_items(arguments)
        elif name == "get_work_item_list":
            return await _handle_get_work_item_list(arguments)
        elif name == "get_work_item_summary":
            return await _handle_get_work_item_summary(arguments)
        elif name == "search_by_work_item":
            return await _handle_search_by_work_item(arguments)
        elif name == "semantic_search":
            return await _handle_semantic_search(arguments)
        else:
            return [types.TextContent(type="text", text=f"❌ Unknown tool: {name}")]
    
    except Exception as e:
        logger.error(f"Error handling tool call {name}: {e}")
        return [types.TextContent(type="text", text=f"❌ Error executing {name}: {str(e)}")]


async def _handle_search_work_items(arguments: dict) -> list[types.TextContent]:
    """Handle work item search requests"""
    query = arguments.get("query", "")
    search_type = arguments.get("search_type", "hybrid")
    work_item_id = arguments.get("work_item_id")
    max_results = arguments.get("max_results", 5)
    
    if not query:
        return [types.TextContent(type="text", text="❌ Query parameter is required")]
    
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
                text=f"❌ Invalid search type: {search_type}. Must be 'text', 'vector', or 'hybrid'"
            )]
        
        if not results:
            filter_text = f" (filtered to work item: {work_item_id})" if work_item_id else ""
            return [types.TextContent(
                type="text",
                text=f"🔍 No results found for '{query}' using {search_type} search{filter_text}"
            )]
        
        # Format results for LLM consumption
        formatted_results = _format_search_results(results, f"{search_type.title()} Search Results", query)
        return [types.TextContent(type="text", text=formatted_results)]
    
    except Exception as e:
        return [types.TextContent(type="text", text=f"❌ Search failed: {str(e)}")]


async def _handle_get_work_item_list(arguments: dict) -> list[types.TextContent]:
    """Handle work item list requests"""
    try:
        work_items = searcher.get_work_items()
        
        if not work_items:
            return [types.TextContent(type="text", text="📋 No work items found in the index")]
        
        work_items_list = "\n".join([f"• {item}" for item in sorted(work_items)])
        return [types.TextContent(
            type="text",
            text=f"📋 Available Work Items ({len(work_items)} total):\n\n{work_items_list}"
        )]
    
    except Exception as e:
        return [types.TextContent(type="text", text=f"❌ Failed to retrieve work items: {str(e)}")]


async def _handle_get_work_item_summary(arguments: dict) -> list[types.TextContent]:
    """Handle work item summary requests"""
    try:
        work_items = searcher.get_work_items()
        total_docs = searcher.get_document_count()
        
        summary = f"📊 Work Item Documentation Summary\n"
        summary += f"{'='*50}\n\n"
        summary += f"📁 Total Work Items: {len(work_items)}\n"
        summary += f"📄 Total Documents: {total_docs}\n"
        summary += f"🔍 Search Index: {searcher.index_name}\n\n"
        
        if work_items:
            summary += f"📋 Available Work Items:\n"
            for item in sorted(work_items):
                summary += f"   • {item}\n"
        
        summary += f"\n💡 Use the search_work_items tool to find specific information"
        summary += f"\n💡 Use search_by_work_item to search within a specific work item"
        
        return [types.TextContent(type="text", text=summary)]
    
    except Exception as e:
        return [types.TextContent(type="text", text=f"❌ Failed to generate summary: {str(e)}")]


async def _handle_search_by_work_item(arguments: dict) -> list[types.TextContent]:
    """Handle work item specific search requests"""
    work_item_id = arguments.get("work_item_id", "")
    query = arguments.get("query", "")
    max_results = arguments.get("max_results", 5)
    
    if not work_item_id or not query:
        return [types.TextContent(
            type="text",
            text="❌ Both work_item_id and query parameters are required"
        )]
    
    try:
        # Use hybrid search with work item filter
        results = await searcher.hybrid_search(query, work_item_id, max_results)
        
        if not results:
            return [types.TextContent(
                type="text",
                text=f"🔍 No results found for '{query}' in work item '{work_item_id}'"
            )]
        
        formatted_results = _format_search_results(
            results, 
            f"Search Results for Work Item: {work_item_id}", 
            query
        )
        
        return [types.TextContent(type="text", text=formatted_results)]
    
    except Exception as e:
        return [types.TextContent(type="text", text=f"❌ Work item search failed: {str(e)}")]


async def _handle_semantic_search(arguments: dict) -> list[types.TextContent]:
    """Handle semantic/vector search requests"""
    concept = arguments.get("concept", "")
    max_results = arguments.get("max_results", 5)
    
    if not concept:
        return [types.TextContent(type="text", text="❌ concept parameter is required")]
    
    try:
        # Perform vector search for semantic similarity
        results = await searcher.vector_search(concept, None, max_results)
        
        if not results:
            return [types.TextContent(
                type="text",
                text=f"🔍 No semantically similar content found for concept: '{concept}'"
            )]
        
        formatted_results = _format_search_results(
            results, 
            f"Semantic Search Results for: {concept}", 
            concept
        )
        
        return [types.TextContent(type="text", text=formatted_results)]
    
    except Exception as e:
        return [types.TextContent(type="text", text=f"❌ Semantic search failed: {str(e)}")]


def _format_search_results(results: List[Dict], title: str, query: str) -> str:
    """Format search results for LLM consumption with rich context."""
    if not results:
        return f"🔍 No results found for '{query}'"
    
    formatted = f"🔍 {title}\n"
    formatted += f"{'='*60}\n"
    formatted += f"Query: '{query}' | Results: {len(results)}\n\n"
    
    for i, result in enumerate(results, 1):
        formatted += f"📄 Result {i}\n"
        formatted += f"{'-'*30}\n"
        
        # Basic metadata
        formatted += f"🆔 ID: {result.get('id', 'N/A')}\n"
        formatted += f"📝 Title: {result.get('title', 'Untitled')}\n"
        formatted += f"🔧 Work Item: {result.get('work_item_id', 'N/A')}\n"
        formatted += f"📂 File: {result.get('file_path', 'N/A')}\n"
        
        # Search score if available
        if '@search.score' in result:
            score = result['@search.score']
            formatted += f"⭐ Relevance Score: {score:.2f}\n"
        
        # Tags if available
        tags = result.get('tags', [])
        if tags:
            formatted += f"🏷️  Tags: {', '.join(tags)}\n"
        
        # Content preview
        content = result.get('content', '')
        if content:
            # Limit content preview for readability
            content_preview = content[:500] + "..." if len(content) > 500 else content
            formatted += f"\n📄 Content:\n{content_preview}\n"
        
        formatted += f"\n"
    
    # Add usage suggestions
    formatted += f"💡 Tips:\n"
    formatted += f"   • Use search_by_work_item to search within specific work items\n"
    formatted += f"   • Try different search types: text, vector, or hybrid\n"
    formatted += f"   • Use semantic_search for concept-based searches\n"
    
    return formatted


async def main():
    """Main entry point for the MCP server"""
    logger.info("🚀 Starting Work Item Documentation MCP Server")
    
    try:
        # Test connections on startup
        logger.info("🔌 Testing connections...")
        
        # Initialize and test search functionality
        global searcher, embedding_generator
        searcher = DocumentSearcher()
        embedding_generator = get_embedding_generator()
        
        # Test embedding service
        if embedding_generator.test_connection():
            logger.info("✅ Embedding service connection successful")
        else:
            logger.warning("⚠️  Embedding service connection failed")
        
        # Test search service
        try:
            doc_count = searcher.get_document_count()
            work_items = searcher.get_work_items()
            logger.info(f"✅ Connected to search index: {doc_count} documents, {len(work_items)} work items")
        except Exception as e:
            logger.error(f"❌ Search service connection failed: {e}")
        
        logger.info("🎯 MCP Server ready for connections")
        
        # Run the server
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await app.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="work-items-documentation",
                    server_version="1.0.0",
                    capabilities=app.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={}
                    )
                )
            )
    
    except Exception as e:
        logger.error(f"❌ MCP Server failed to start: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
