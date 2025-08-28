"""
ChromaDB Document Search MCP Tools
==================================

Tool schemas for ChromaDB-based document search with vector-only capabilities.
These tools provide the same functionality as Azure Cognitive Search tools
but use ChromaDB as the underlying search service.

This module contains:
1. Universal tools - work across any document context using ChromaDB
2. ChromaDB-specific optimizations - vector-only search capabilities
3. Metadata filtering - using ChromaDB's native filtering
"""

import mcp.types as types


def get_universal_search_tools() -> list[types.Tool]:
    """Get universal search tool definitions for ChromaDB backend"""
    return [
        types.Tool(
            name="chromadb_search_documents",
            description="Search documents using ChromaDB vector search with comprehensive filtering options",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query for semantic/vector search"
                    },
                    "search_type": {
                        "type": "string",
                        "enum": ["vector"],
                        "default": "vector",
                        "description": "Search type (all route to vector search in ChromaDB)"
                    },
                    "filters": {
                        "type": "object",
                        "description": "Metadata filters for document search",
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
                            "file_name": {
                                "type": "string",
                                "description": "Filter by specific file name"
                            },
                            "category": {
                                "oneOf": [
                                    {"type": "string"},
                                    {"type": "array", "items": {"type": "string"}}
                                ],
                                "description": "Filter by document category"
                            },
                            "tags": {
                                "oneOf": [
                                    {"type": "string"},
                                    {"type": "array", "items": {"type": "string"}}
                                ],
                                "description": "Filter by document tags"
                            },
                            "chunk_index": {
                                "type": "string",
                                "description": "Filter by chunk index (e.g., 'file.md_chunk_0')"
                            }
                        }
                    },
                    "max_results": {
                        "type": "integer",
                        "default": 5,
                        "description": "Maximum number of results to return"
                    },
                    "include_content": {
                        "type": "boolean",
                        "default": True,
                        "description": "Include document content in results"
                    }
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="chromadb_get_document_content",
            description="Get full content of specific documents by ID or context/file",
            inputSchema={
                "type": "object",
                "properties": {
                    "document_ids": {
                        "oneOf": [
                            {"type": "string"},
                            {"type": "array", "items": {"type": "string"}}
                        ],
                        "description": "Document ID(s) to retrieve"
                    },
                    "context_and_file": {
                        "type": "object",
                        "properties": {
                            "context_name": {"type": "string"},
                            "file_name": {"type": "string"}
                        },
                        "description": "Get all chunks for a specific file within a context"
                    },
                    "include_metadata": {
                        "type": "boolean",
                        "default": True,
                        "description": "Include document metadata"
                    },
                    "max_content_length": {
                        "type": "integer",
                        "description": "Maximum content length per document"
                    }
                }
            }
        ),
        types.Tool(
            name="chromadb_explore_document_structure",
            description="Explore document structure - contexts, files, chunks, or categories",
            inputSchema={
                "type": "object",
                "properties": {
                    "structure_type": {
                        "type": "string",
                        "enum": ["contexts", "files", "chunks", "categories"],
                        "default": "contexts",
                        "description": "Type of structure to explore"
                    },
                    "context_name": {
                        "type": "string",
                        "description": "Filter by specific context"
                    },
                    "file_name": {
                        "type": "string",
                        "description": "Filter by specific file"
                    },
                    "max_items": {
                        "type": "integer",
                        "default": 50,
                        "description": "Maximum items to return"
                    }
                },
                "required": ["structure_type"]
            }
        ),
        types.Tool(
            name="chromadb_get_document_contexts",
            description="Get all available document contexts with statistics",
            inputSchema={
                "type": "object",
                "properties": {
                    "include_stats": {
                        "type": "boolean",
                        "default": True,
                        "description": "Include document counts per context"
                    },
                    "max_contexts": {
                        "type": "integer",
                        "default": 100,
                        "description": "Maximum contexts to return"
                    }
                }
            }
        ),
        types.Tool(
            name="chromadb_get_index_summary",
            description="Get comprehensive ChromaDB collection statistics and document distribution",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]


def get_all_chroma_db_tools() -> list[types.Tool]:
    """Get all ChromaDB tool definitions (universal tools)"""
    tools = []
    tools.extend(get_universal_search_tools())
    return tools
