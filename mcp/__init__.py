"""
MCP Server Module
================

Model Context Protocol server for work item documentation search.
Provides tools for searching and retrieving work item documentation.
"""

from .server import app, main
from .search_documents import DocumentSearcher

__all__ = [
    'app',
    'main', 
    'DocumentSearcher'
]
