"""
Document Upload Module
=====================

Components for processing and uploading work item documentation to Azure Cognitive Search.
Includes document processing, file tracking, and upload utilities.
"""

from .document_utils import discover_markdown_files, read_markdown_file, process_document_chunks, extract_metadata
from .file_tracker import DocumentProcessingTracker

__all__ = [
    'discover_markdown_files',
    'read_markdown_file', 
    'process_document_chunks',
    'extract_metadata',
    'DocumentProcessingTracker'
]
