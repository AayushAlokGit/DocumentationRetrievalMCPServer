"""
Work Item Documentation MCP Server
==================================

Model Context Protocol server that provides search capabilities for Work Item documentation
stored in Azure Cognitive Search. This server exposes tools for searching, retrieving,
and managing work item documentation for LLM interactions.
"""

import asyncio
import logging
from typing import Optional
import sys
from pathlib import Path

# ONE simple line to fix all imports - find project root and add src
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'src'))

# Import the actual MCP server classes (now no naming conflict)
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types

# Import our search functionality
from common.azure_cognitive_search import get_azure_search_service
from common.embedding_service import get_embedding_generator

# Import refactored tool components
from workitem_mcp.tools.tool_schemas import get_all_tools
from workitem_mcp.tools.tool_router import ToolRouter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("work-items-mcp")

# Initialize the MCP server
app = Server("work-items-documentation")

# Global instances
search_service = None
embedding_generator = None
tool_router: Optional[ToolRouter] = None


async def initialize_services():
    """Initialize search and embedding services"""
    global search_service, embedding_generator, tool_router
    
    if search_service is None:
        logger.info("[INFO] Initializing search services...")
        search_service = get_azure_search_service()
        
    if embedding_generator is None:
        logger.info("[INFO] Initializing embedding services...")
        embedding_generator = get_embedding_generator()
    
    if tool_router is None:
        logger.info("[INFO] Initializing tool router...")
        tool_router = ToolRouter(search_service)
        
    return search_service, embedding_generator, tool_router


@app.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available tools for work item documentation search and management."""
    return get_all_tools()


@app.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """Handle tool calls for work item documentation operations."""
    global tool_router
    
    # Initialize tool router if not already done
    if tool_router is None:
        await initialize_services()
    
    return await tool_router.handle_tool_call(name, arguments)


async def main():
    """Main entry point for the MCP server"""
    logger.info("[START] Starting Universal Document Search MCP Server")
    
    try:
        # Test connections on startup
        logger.info("[CONNECT] Testing connections...")
        
        # Initialize and test search functionality
        global search_service, embedding_generator
        search_service = get_azure_search_service()
        embedding_generator = get_embedding_generator()
        
        # Test embedding service
        if embedding_generator.test_connection():
            logger.info("[SUCCESS] Embedding service connection successful")
        else:
            logger.warning("[WARNING]  Embedding service connection failed")
        
        # Test search service
        try:
            doc_count = search_service.get_document_count()
            contexts = search_service.get_unique_field_values("context_name")
            logger.info(f"[SUCCESS] Connected to search index: {doc_count} documents, {len(contexts)} contexts")
        except Exception as e:
            logger.error(f"[ERROR] Search service connection failed: {e}")
        
        logger.info("[TARGET] MCP Server ready for connections")
        
        # Run the server
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await app.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="universal-document-search",
                    server_version="1.0.0",
                    capabilities=app.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={}
                    )
                )
            )
    
    except Exception as e:
        logger.error(f"[ERROR] MCP Server failed to start: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
