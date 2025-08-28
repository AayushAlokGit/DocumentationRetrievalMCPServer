"""
Universal Tool Router for MCP Server
====================================

Central router for document search tools supporting both Azure Cognitive Search
and ChromaDB backends. Routes tool calls to appropriate handlers based on 
the search service type.
"""

import logging
from typing import Dict, Any
import mcp.types as types

from src.common.vector_search_services.vector_search_interface import IVectorSearchService

# Azure Cognitive Search handlers
from .azure_cognitive_search.universal_tools_for_azure_cognitive_search import (
    handle_search_documents as azure_handle_search_documents,
    handle_get_document_contexts as azure_handle_get_document_contexts,
    handle_explore_document_structure as azure_handle_explore_document_structure,
    handle_get_index_summary as azure_handle_get_index_summary,
    handle_get_document_content as azure_handle_get_document_content
)

# ChromaDB handlers
from .chroma_db.universal_tools_for_chroma_db import (
    handle_search_documents as chroma_handle_search_documents,
    handle_get_document_contexts as chroma_handle_get_document_contexts,
    handle_explore_document_structure as chroma_handle_explore_document_structure,
    handle_get_index_summary as chroma_handle_get_index_summary,
    handle_get_document_content as chroma_handle_get_document_content
)


logger = logging.getLogger("documentation-retrieval-mcp")


class ToolRouter:
    """Routes MCP tool calls to appropriate handlers based on search service backend"""
    
    def __init__(self, search_service: IVectorSearchService):
        self.search_service = search_service
        
        # Set up all handlers
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup all handlers for both Azure and ChromaDB tools"""
        logger.info("[ROUTER] Setting up all tool handlers")
        self.handlers = {
            # Azure Cognitive Search tools
            "search_documents": azure_handle_search_documents,
            "get_document_contexts": azure_handle_get_document_contexts,
            "explore_document_structure": azure_handle_explore_document_structure,
            "get_index_summary": azure_handle_get_index_summary,
            "get_document_content": azure_handle_get_document_content,
            # ChromaDB tools
            "chromadb_search_documents": chroma_handle_search_documents,
            "chromadb_get_document_contexts": chroma_handle_get_document_contexts,
            "chromadb_explore_document_structure": chroma_handle_explore_document_structure,
            "chromadb_get_index_summary": chroma_handle_get_index_summary,
            "chromadb_get_document_content": chroma_handle_get_document_content,
        }
    
    async def handle_tool_call(self, name: str, arguments: dict) -> list[types.TextContent]:
        """Route tool call to appropriate handler"""
        try:
            if name not in self.handlers:
                return [types.TextContent(
                    type="text", 
                    text=f"[ERROR] Unknown tool: {name}. Available tools: {', '.join(self.handlers.keys())}"
                )]
            
            handler = self.handlers[name]
            
            # Log the routing decision
            logger.info(f"[ROUTER] Routing {name} to handler")
            
            return await handler(self.search_service, arguments)
            
        except Exception as e:
            logger.error(f"Error handling tool call {name}: {e}")
            return [types.TextContent(
                type="text", 
                text=f"[ERROR] Error executing {name}: {str(e)}"
            )]
