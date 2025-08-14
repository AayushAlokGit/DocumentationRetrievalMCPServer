"""
Information Tool Handlers for MCP Server
========================================

Handlers for information retrieval tools including work item lists,
summaries, and metadata operations.
"""

import logging
import mcp.types as types

logger = logging.getLogger("work-items-mcp")


async def handle_get_work_item_list(searcher, arguments: dict) -> list[types.TextContent]:
    """Handle work item list requests"""
    try:
        # Use the correct method from DocumentSearcher
        work_items = searcher.get_work_items()
        
        if not work_items:
            return [types.TextContent(type="text", text="[LIST] No work items found in the index")]
        
        work_items_list = "\n".join([f"• {item}" for item in sorted(work_items)])
        return [types.TextContent(
            type="text",
            text=f"[LIST] Available Work Items ({len(work_items)} total):\n\n{work_items_list}"
        )]
    
    except Exception as e:
        return [types.TextContent(type="text", text=f"[ERROR] Failed to retrieve work items: {str(e)}")]


async def handle_get_work_item_summary(searcher, arguments: dict) -> list[types.TextContent]:
    """Handle work item summary requests"""
    try:
        # Use the correct methods from DocumentSearcher
        work_items = searcher.get_work_items()
        total_docs = searcher.get_document_count()
        
        summary = f"[SUMMARY] Work Item Documentation Summary\n"
        summary += f"{'='*50}\n\n"
        summary += f"[FOLDER] Total Work Items: {len(work_items)}\n"
        summary += f"[DOCUMENT] Total Documents: {total_docs}\n"
        summary += f"[SEARCH] Search Index: {searcher.index_name}\n\n"
        
        if work_items:
            summary += f"[LIST] Available Work Items:\n"
            for item in sorted(work_items):
                summary += f"   • {item}\n"
        
        summary += f"\nTips: Use the search_work_items tool to find specific information"
        summary += f"\nTips: Use search_by_work_item to search within a specific work item"
        
        return [types.TextContent(type="text", text=summary)]
    
    except Exception as e:
        return [types.TextContent(type="text", text=f"[ERROR] Failed to generate summary: {str(e)}")]
