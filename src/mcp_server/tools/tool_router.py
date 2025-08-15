"""
Universal Tool Router for MCP Server
====================================

Central router for universal document search tools and work item specific tools.
Routes tool calls to appropriate handlers based on tool type.
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

from .work_item_tools import WORK_ITEM_TOOL_HANDLERS

logger = logging.getLogger("work-items-mcp")


class ToolRouter:
    """Routes MCP tool calls to universal and work item specific handlers"""
    
    def __init__(self, search_service):
        self.search_service = search_service
        
        # Map tool names to their universal handlers
        self.universal_handlers = {
            "search_documents": handle_search_documents,
            "get_document_contexts": handle_get_document_contexts,
            "explore_document_structure": handle_explore_document_structure,
            "get_index_summary": handle_get_index_summary,
        }
        
        # Combine universal and work item specific handlers
        self.tool_handlers = {
            **self.universal_handlers,
            **WORK_ITEM_TOOL_HANDLERS
        }
    
    async def handle_tool_call(self, name: str, arguments: dict) -> list[types.TextContent]:
        """Route tool call to appropriate universal or work item handler"""
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
            
            # Log whether using universal or work item handler
            if name in self.universal_handlers:
                logger.info(f"[ROUTER] Routing {name} to universal handler")
            else:
                logger.info(f"[ROUTER] Routing {name} to work item specific handler")
            
            return await handler(self.search_service, arguments)
            
        except Exception as e:
            logger.error(f"Error handling tool call {name}: {e}")
            return [types.TextContent(
                type="text", 
                text=f"[ERROR] Error executing {name}: {str(e)}"
            )]
    
    def get_available_tools(self) -> list[str]:
        """Get list of available tool names (universal + work item specific)"""
        return list(self.tool_handlers.keys())
    
    def get_universal_tools(self) -> list[str]:
        """Get list of universal tool names"""
        return list(self.universal_handlers.keys())
    
    def get_work_item_tools(self) -> list[str]:
        """Get list of work item specific tool names"""
        return list(WORK_ITEM_TOOL_HANDLERS.keys())
