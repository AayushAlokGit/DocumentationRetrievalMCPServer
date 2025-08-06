"""
Tool Router for MCP Server
==========================

Central router that dispatches tool calls to appropriate handlers.
This provides a clean interface between the main server and tool implementations.
"""

import logging
from typing import Dict, Any
import mcp.types as types

from .search_tools import handle_search_work_items, handle_search_by_work_item, handle_semantic_search
from .info_tools import handle_get_work_item_list, handle_get_work_item_summary

logger = logging.getLogger("work-items-mcp")


class ToolRouter:
    """Routes MCP tool calls to appropriate handlers"""
    
    def __init__(self, searcher):
        self.searcher = searcher
        
        # Map tool names to their handlers
        self.tool_handlers = {
            "search_work_items": handle_search_work_items,
            "search_by_work_item": handle_search_by_work_item,
            "semantic_search": handle_semantic_search,
            "get_work_item_list": handle_get_work_item_list,
            "get_work_item_summary": handle_get_work_item_summary,
        }
    
    async def handle_tool_call(self, name: str, arguments: dict) -> list[types.TextContent]:
        """Route tool call to appropriate handler"""
        try:
            if name not in self.tool_handlers:
                return [types.TextContent(
                    type="text", 
                    text=f"[ERROR] Unknown tool: {name}. Available tools: {', '.join(self.tool_handlers.keys())}"
                )]
            
            handler = self.tool_handlers[name]
            
            # Initialize searcher if not already done
            if self.searcher is None:
                from search_documents import DocumentSearcher
                self.searcher = DocumentSearcher()
                logger.info("[SUCCESS] DocumentSearcher initialized")
            
            # Call the appropriate handler
            return await handler(self.searcher, arguments)
            
        except Exception as e:
            logger.error(f"Error handling tool call {name}: {e}")
            return [types.TextContent(
                type="text", 
                text=f"[ERROR] Error executing {name}: {str(e)}"
            )]
    
    def get_available_tools(self) -> list[str]:
        """Get list of available tool names"""
        return list(self.tool_handlers.keys())
