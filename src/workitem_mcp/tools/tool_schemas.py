"""
Universal Document Search MCP Tools
===================================

New universal tool schemas for document search across all document types.
These replace the old work-item specific tools with universal capabilities.
"""

import mcp.types as types


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
        )
    ]


def get_context_discovery_tools() -> list[types.Tool]:
    """Get context and structure discovery tools"""
    return [
        types.Tool(
            name="get_document_contexts",
            description="Get all available document contexts (work items, projects, etc.) with statistics",
            inputSchema={
                "type": "object",
                "properties": {
                    "context_type": {
                        "type": "string",
                        "enum": ["work_item", "project", "contract", "all"],
                        "description": "Filter by context type (default: all)",
                        "default": "all"
                    },
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
                    "chunk_range": {
                        "type": "object",
                        "properties": {
                            "start": {"type": "integer", "minimum": 0},
                            "end": {"type": "integer", "minimum": 0}
                        },
                        "description": "Optional chunk range for chunk exploration"
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


def get_legacy_tool_schemas() -> list[types.Tool]:
    """Get legacy tool schemas for backward compatibility"""
    return [
        types.Tool(
            name="search_work_items",
            description="[LEGACY] Search work item documentation - use search_documents instead",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "search_type": {"type": "string", "enum": ["text", "vector", "hybrid"], "default": "hybrid"},
                    "work_item_id": {"type": "string", "description": "Optional work item ID"},
                    "max_results": {"type": "integer", "default": 5, "minimum": 1, "maximum": 20}
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="search_by_work_item", 
            description="[LEGACY] Search within specific work item - use search_documents with context_id filter instead",
            inputSchema={
                "type": "object",
                "properties": {
                    "work_item_id": {"type": "string", "description": "Work item ID"},
                    "query": {"type": "string", "description": "Search query"},
                    "max_results": {"type": "integer", "default": 5, "minimum": 1, "maximum": 10}
                },
                "required": ["work_item_id", "query"]
            }
        ),
        types.Tool(
            name="semantic_search",
            description="[LEGACY] Semantic search - use search_documents with search_type='vector' instead", 
            inputSchema={
                "type": "object",
                "properties": {
                    "concept": {"type": "string", "description": "Concept to search for"},
                    "max_results": {"type": "integer", "default": 5, "minimum": 1, "maximum": 15}
                },
                "required": ["concept"]
            }
        ),
        types.Tool(
            name="search_by_chunk",
            description="[LEGACY] Search by chunk pattern - use search_documents with chunk_pattern filter instead",
            inputSchema={
                "type": "object", 
                "properties": {
                    "chunk_pattern": {"type": "string", "description": "Chunk pattern"},
                    "query": {"type": "string", "description": "Optional search query"},
                    "max_results": {"type": "integer", "default": 5, "minimum": 1, "maximum": 15}
                },
                "required": ["chunk_pattern"]
            }
        ),
        types.Tool(
            name="search_file_chunks",
            description="[LEGACY] Search file chunks - use explore_document_structure instead",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_name": {"type": "string", "description": "File name"},
                    "query": {"type": "string", "description": "Optional search query"},
                    "max_results": {"type": "integer", "default": 10, "minimum": 1, "maximum": 20}
                },
                "required": ["file_name"]
            }
        ),
        types.Tool(
            name="search_chunk_range", 
            description="[LEGACY] Search chunk range - use explore_document_structure instead",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_name": {"type": "string", "description": "File name"},
                    "start_chunk": {"type": "integer", "default": 0, "minimum": 0},
                    "end_chunk": {"type": "integer", "minimum": 0},
                    "max_results": {"type": "integer", "default": 10, "minimum": 1, "maximum": 20}
                },
                "required": ["file_name"]
            }
        ),
        types.Tool(
            name="get_work_item_list",
            description="[LEGACY] Get work item list - use get_document_contexts instead", 
            inputSchema={"type": "object", "properties": {}}
        ),
        types.Tool(
            name="get_work_item_summary",
            description="[LEGACY] Get work item summary - use get_index_summary instead",
            inputSchema={"type": "object", "properties": {}}
        )
    ]


def get_all_tools() -> list[types.Tool]:
    """Get all available tool definitions (universal + legacy for compatibility)"""
    tools = []
    tools.extend(get_universal_search_tools())
    tools.extend(get_context_discovery_tools()) 
    tools.extend(get_analytics_tools())
    # Include legacy tools for backward compatibility
    tools.extend(get_legacy_tool_schemas())
    return tools
