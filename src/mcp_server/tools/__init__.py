"""
MCP Tools
=========

Tool definitions for the MCP server supporting both Azure Cognitive Search
and ChromaDB backends.
"""

import mcp.types as types
from src.mcp_server.tools.azure_cognitive_search.azure_cognitive_search_tool_schemas import get_all_azure_cognitive_search_tools
from src.mcp_server.tools.chroma_db.chroma_db_tool_schemas import get_all_chroma_db_tools


def get_all_tools() -> list[types.Tool]:
    tools = []
    tools.extend(get_all_chroma_db_tools())
    # tools.extend(get_all_azure_cognitive_search_tools())
    return tools