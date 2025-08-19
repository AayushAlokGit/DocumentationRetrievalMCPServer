"""
Universal Document Search MCP Tools
===================================

New universal tool schemas for document search across all document types.
These replace the old work-item specific tools with universal capabilities.

This module contains:
1. Universal tools - work across any document context
2. Work item tools - imported from dedicated work item tools module
3. Legacy compatibility - for backward compatibility
"""

import mcp.types as types
from .work_item_tools import get_work_item_tool_schemas


def get_universal_search_tools() -> list[types.Tool]:
    """Get universal search tool definitions"""
    return [
        types.Tool(
            name="search_documents",
            description="Universal document search with multiple search types and comprehensive filtering",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query - can be keywords, questions, or concepts"
                    },
                    "search_type": {
                        "type": "string",
                        "enum": ["text", "vector", "semantic", "hybrid"],
                        "description": "Type of search to perform (default: hybrid)",
                        "default": "hybrid"
                    },
                    "filters": {
                        "type": "object",
                        "description": "Document filters",
                        "properties": {
                            "context_name": {
                                "oneOf": [
                                    {"type": "string"},
                                    {"type": "array", "items": {"type": "string"}}
                                ],
                                "description": "Filter by context name(s) - work items, projects, etc."
                            },
                            "file_type": {
                                "oneOf": [
                                    {"type": "string"},
                                    {"type": "array", "items": {"type": "string"}}
                                ],
                                "description": "Filter by file type(s) - md, pdf, docx, etc."
                            },
                            "category": {
                                "oneOf": [
                                    {"type": "string"},
                                    {"type": "array", "items": {"type": "string"}}
                                ],
                                "description": "Filter by document category"
                            },
                            "file_name": {
                                "type": "string",
                                "description": "Filter by specific file name"
                            },
                            "chunk_pattern": {
                                "type": "string",
                                "description": "Filter by chunk pattern (e.g., 'file.md_chunk_0')"
                            },
                            "tags": {
                                "oneOf": [
                                    {"type": "string"},
                                    {"type": "array", "items": {"type": "string"}}
                                ],
                                "description": "Filter by document tags"
                            }
                        }
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default: 5)",
                        "default": 5,
                        "minimum": 1,
                        "maximum": 50
                    },
                    "include_content": {
                        "type": "boolean",
                        "description": "Include full content in results (default: true)",
                        "default": True
                    }
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="get_document_content",
            description="Retrieve full content of specific documents by their identifiers",
            inputSchema={
                "type": "object",
                "properties": {
                    "document_ids": {
                        "oneOf": [
                            {"type": "string"},
                            {"type": "array", "items": {"type": "string"}}
                        ],
                        "description": "Document ID(s) to retrieve full content for"
                    },
                    "context_and_file": {
                        "type": "object",
                        "properties": {
                            "context_name": {"type": "string"},
                            "file_name": {"type": "string"}
                        },
                        "description": "Retrieve all chunks for a specific file within a context"
                    },
                    "max_content_length": {
                        "type": "integer",
                        "description": "Maximum content length per chunk (default: unlimited)",
                        "minimum": 100
                    },
                    "include_metadata": {
                        "type": "boolean",
                        "description": "Include document metadata (default: true)",
                        "default": True
                    }
                },
                "anyOf": [
                    {"required": ["document_ids"]},
                    {"required": ["context_and_file"]}
                ]
            }
        )
    ]


def get_context_discovery_tools() -> list[types.Tool]:
    """Get context and structure discovery tools"""
    return [
        types.Tool(
            name="get_document_contexts",
            description="Get all available document contexts with statistics",
            inputSchema={
                "type": "object",
                "properties": {
                    "include_stats": {
                        "type": "boolean",
                        "description": "Include document counts per context (default: true)",
                        "default": True
                    },
                    "max_contexts": {
                        "type": "integer",
                        "description": "Maximum number of contexts to return (default: 100)",
                        "default": 100,
                        "minimum": 1,
                        "maximum": 1000
                    }
                }
            }
        ),
        types.Tool(
            name="explore_document_structure",
            description="Explore document structure and navigate through contexts, files, and chunks",
            inputSchema={
                "type": "object",
                "properties": {
                    "structure_type": {
                        "type": "string",
                        "enum": ["contexts", "files", "chunks", "categories"],
                        "description": "Type of structure to explore",
                        "default": "contexts"
                    },
                    "context_name": {
                        "type": "string",
                        "description": "Optional context name to filter exploration"
                    },
                    "file_name": {
                        "type": "string", 
                        "description": "Optional file name to filter exploration"
                    },
                    "max_items": {
                        "type": "integer",
                        "description": "Maximum number of items to return (default: 50)",
                        "default": 50,
                        "minimum": 1,
                        "maximum": 200
                    }
                },
                "required": ["structure_type"]
            }
        )
    ]


def get_analytics_tools() -> list[types.Tool]:
    """Get document analytics and summary tools"""
    return [
        types.Tool(
            name="get_index_summary",
            description="Get comprehensive index statistics and document distribution",
            inputSchema={
                "type": "object",
                "properties": {
                    "include_facets": {
                        "type": "boolean",
                        "description": "Include facet distributions (default: true)",
                        "default": True
                    },
                    "facet_limit": {
                        "type": "integer",
                        "description": "Maximum facet values per field (default: 50)",
                        "default": 50,
                        "minimum": 1,
                        "maximum": 200
                    }
                }
            }
        )
    ]


def get_work_item_specific_tools() -> list[types.Tool]:
    """Get work item specific tool definitions"""
    return get_work_item_tool_schemas()


def get_all_tools() -> list[types.Tool]:
    """Get all available tool definitions (universal + work item specific)"""
    tools = []
    tools.extend(get_universal_search_tools())
    tools.extend(get_context_discovery_tools()) 
    tools.extend(get_analytics_tools())
    # Include work item specific tools
    # tools.extend(get_work_item_specific_tools())
    return tools
