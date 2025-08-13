"""
Document Upload Module
=====================

Components for processing and uploading work item documentation to Azure Cognitive Search.
Includes document processing, file tracking, and upload utilities.
"""

from .file_tracker import DocumentProcessingTracker
from .processing_strategies import PersonalDocumentationAssistantProcessingStrategy, DocumentProcessingStrategy
from .discovery_strategies import PersonalDocumentationDiscoveryStrategy, DocumentDiscoveryStrategy

__all__ = [
    'DocumentProcessingTracker',
    'PersonalDocumentationAssistantProcessingStrategy',
    'DocumentProcessingStrategy',
    'PersonalDocumentationDiscoveryStrategy',
    'DocumentDiscoveryStrategy'
]
