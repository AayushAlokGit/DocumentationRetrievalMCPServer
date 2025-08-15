"""
Universal Tool Router for MCP Server
====================================

Central router for the new universal document search tools with legacy compatibility.
Routes tool calls to universal handlers and provides backward compatibility.
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

from .legacy_compatibility import LEGACY_TOOL_HANDLERS

logger = logging.getLogger("work-items-mcp")


class ToolRouter:
    """Routes MCP tool calls to universal handlers with legacy support"""
    
    def __init__(self, search_service):
        self.search_service = search_service
        
        # Map tool names to their universal handlers
        self.universal_handlers = {
            "search_documents": handle_search_documents,
            "get_document_contexts": handle_get_document_contexts,
            "explore_document_structure": handle_explore_document_structure,
            "get_index_summary": handle_get_index_summary,
        }
        
        # Combine universal and legacy handlers
        self.tool_handlers = {
            **self.universal_handlers,
            **LEGACY_TOOL_HANDLERS
        }
    
    async def handle_tool_call(self, name: str, arguments: dict) -> list[types.TextContent]:
        """Route tool call to appropriate universal or legacy handler"""
        try:
            if name not in self.tool_handlers:
                return [types.TextContent(
                    type="text", 
                    text=f"[ERROR] Unknown tool: {name}. Available tools: {', '.join(self.tool_handlers.keys())}"
                )]
            
            handler = self.tool_handlers[name]
            
            # Initialize search service if not already done
            if self.search_service is None:
                from common.azure_cognitive_search import get_azure_search_service
                self.search_service = get_azure_search_service()
                logger.info("[SUCCESS] Azure Search Service initialized")
            
            # Log whether using universal or legacy handler
            if name in self.universal_handlers:
                logger.info(f"[ROUTER] Routing {name} to universal handler")
            else:
                logger.info(f"[ROUTER] Routing {name} to legacy compatibility handler")
            
            return await handler(self.search_service, arguments)
            
        except Exception as e:
            logger.error(f"Error handling tool call {name}: {e}")
            return [types.TextContent(
                type="text", 
                text=f"[ERROR] Error executing {name}: {str(e)}"
            )]
    
    def get_available_tools(self) -> list[str]:
        """Get list of available tool names (universal + legacy)"""
        return list(self.tool_handlers.keys())
    
    def get_universal_tools(self) -> list[str]:
        """Get list of new universal tool names"""
        return list(self.universal_handlers.keys())
    
    def get_legacy_tools(self) -> list[str]:
        """Get list of legacy tool names"""
        return list(LEGACY_TOOL_HANDLERS.keys())
