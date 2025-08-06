"""
Tool Schema Definitions for MCP Server
======================================

JSON Schema definitions for all MCP tools exposed by the server.
This centralizes tool definitions for easier maintenance and consistency.
"""

import mcp.types as types


def get_search_tools() -> list[types.Tool]:
    """Get all search-related tool definitions"""
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


def get_info_tools() -> list[types.Tool]:
    """Get all information retrieval tool definitions"""
    return [
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
        )
    ]


def get_all_tools() -> list[types.Tool]:
    """Get all tool definitions"""
    tools = []
    tools.extend(get_search_tools())
    tools.extend(get_info_tools())
    return tools
