"""
Document Discovery Strategies
============================

Strategy pattern implementation for different document discovery approaches.
Each strategy defines how to find and filter documents for processing.
The discover_documents method can return any type of data, and the parse_result 
method converts it to the format needed by the pipeline.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class DocumentDiscoveryResult:
    """
    Result of the document discovery phase for Personal Documentation Assistant use case.
    This is the parsed output format for GeneralDocumentDiscoveryStrategy and 
    PersonalDocumentationDiscoveryStrategy.
    """
    total_files: int
    files_by_type: Dict[str, int]
    discovered_files: List[Path]
    discovery_time: float
    errors: List[str]
    strategy_name: str  # Which strategy was used
    strategy_metadata: Optional[Dict] = None  # Strategy-specific metadata


class DocumentDiscoveryStrategy(ABC):
    """
    Abstract base class for document discovery strategies.
    
    Each strategy defines how to discover documents and how to parse the results.
    """
    
    @abstractmethod
    def discover_documents(self, root_path: str, **kwargs) -> Any:
        """
        Discover documents based on the strategy's specific logic.
        
        Args:
            root_path: Root directory to start discovery from
            **kwargs: Additional strategy-specific parameters
            
        Returns:
            Any: Strategy-specific discovery result (could be file paths, cloud references, etc.)
        """
        pass
    
    @abstractmethod
    def parse_result(self, discovery_result: Any, discovery_time: float, **kwargs) -> Any:
        """
        Parse the discovery result into the format needed by the pipeline.
        
        Args:
            discovery_result: Raw result from discover_documents method
            discovery_time: Time taken for discovery
            **kwargs: Additional parsing parameters
            
        Returns:
            Any: Parsed result in the format expected by the pipeline
        """
        pass
    
    @abstractmethod
    def get_strategy_name(self) -> str:
        """
        Get the name of this discovery strategy.
        
        Returns:
            str: Strategy name
        """
        pass
    
    @abstractmethod
    def get_supported_extensions(self) -> List[str]:
        """
        Get the file extensions supported by this strategy.
        
        Returns:
            List[str]: List of supported file extensions (with dots)
        """
        pass
    
    def _filter_valid_files(self, files: List[Path]) -> List[Path]:
        """
        Filter out invalid files (empty, non-existent, etc.).
        
        Args:
            files: List of file paths to filter
            
        Returns:
            List[Path]: List of valid file paths
        """
        valid_files = []
        for file_path in files:
            if (file_path.is_file() and 
                file_path.stat().st_size > 0 and 
                file_path.suffix.lower() in self.get_supported_extensions()):
                valid_files.append(file_path)
        return valid_files


class GeneralDocumentDiscoveryStrategy(DocumentDiscoveryStrategy):
    """
    General-purpose document discovery strategy.
    
    Discovers all supported document types in a directory structure with configurable options.
    For this strategy, discover_documents returns List[Path] and parse_result returns DocumentDiscoveryResult.
    """
    
    def __init__(self, extensions: Optional[List[str]] = None, recursive: bool = True):
        """
        Initialize the general document discovery strategy.
        
        Args:
            extensions: List of file extensions to discover (default: from environment)
            recursive: Whether to search recursively (default: True)
        """
        self.recursive = recursive
        self._extensions = extensions
    
    def get_strategy_name(self) -> str:
        """Get the name of this discovery strategy."""
        return "GeneralDocument"
    
    def get_supported_extensions(self) -> List[str]:
        """
        Get supported file extensions from configuration or environment.
        
        Returns:
            List[str]: List of supported file extensions (with dots)
        """
        if self._extensions:
            return self._extensions
        
        # Get from environment variable
        extensions_str = os.getenv('SUPPORTED_FILE_EXTENSIONS', '.md,.txt,.docx')
        extensions = [ext.strip() for ext in extensions_str.split(',')]
        # Ensure all extensions start with a dot
        extensions = [ext if ext.startswith('.') else f'.{ext}' for ext in extensions]
        return extensions
    
    def discover_documents(self, root_path: str, **kwargs) -> List[Path]:
        """
        Discover all supported document files in the directory structure or process a single file.
        
        Args:
            root_path: Root directory to start discovery from OR path to a single file
            **kwargs: Additional parameters (recursive, max_files, exclude_patterns)
            
        Returns:
            List[Path]: List of discovered file paths
        """
        # Override recursive setting if provided in kwargs
        recursive = kwargs.get('recursive', self.recursive)
        max_files = kwargs.get('max_files', None)
        exclude_patterns = kwargs.get('exclude_patterns', [])
        
        root_path_obj = Path(root_path)
        
        if not root_path_obj.exists():
            raise FileNotFoundError(f"Path does not exist: {root_path}")
        
        document_files = []
        extensions = self.get_supported_extensions()
        
        # Handle single file case
        if root_path_obj.is_file():
            # Check if the single file has a supported extension
            if root_path_obj.suffix.lower() in extensions:
                document_files = [root_path_obj]
            else:
                # File doesn't have supported extension, return empty list
                document_files = []
        else:
            # Handle directory case (existing logic)
            # Find all supported document files
            for ext in extensions:
                if recursive:
                    # Use rglob for recursive search
                    found_files = list(root_path_obj.rglob(f"*{ext}"))
                else:
                    # Use glob for non-recursive search (current directory only)
                    found_files = list(root_path_obj.glob(f"*{ext}"))
                
                document_files.extend(found_files)
        
        # Filter valid files
        valid_files = self._filter_valid_files(document_files)
        
        # Apply exclude patterns
        if exclude_patterns:
            filtered_files = []
            for file_path in valid_files:
                should_exclude = False
                for pattern in exclude_patterns:
                    if pattern in str(file_path):
                        should_exclude = True
                        break
                if not should_exclude:
                    filtered_files.append(file_path)
            valid_files = filtered_files
        
        # Sort files
        valid_files = sorted(valid_files)
        
        # Limit number of files if specified
        if max_files and len(valid_files) > max_files:
            valid_files = valid_files[:max_files]
        
        return valid_files
    
    def parse_result(self, discovery_result: List[Path], discovery_time: float, **kwargs) -> DocumentDiscoveryResult:
        """
        Parse the file paths into DocumentDiscoveryResult format.
        
        Args:
            discovery_result: List of discovered file paths
            discovery_time: Time taken for discovery
            **kwargs: Additional parsing parameters (errors, etc.)
            
        Returns:
            DocumentDiscoveryResult: Parsed result for the pipeline
        """
        errors = kwargs.get('errors', [])
        
        # Analyze file types
        files_by_type = {}
        for file_path in discovery_result:
            file_type = file_path.suffix.lower()
            files_by_type[file_type] = files_by_type.get(file_type, 0) + 1
        
        # Create strategy-specific metadata
        strategy_metadata = {
            'recursive': kwargs.get('recursive', self.recursive),
            'max_files': kwargs.get('max_files'),
            'exclude_patterns': kwargs.get('exclude_patterns', []),
            'extensions_used': self.get_supported_extensions()
        }
        
        return DocumentDiscoveryResult(
            total_files=len(discovery_result),
            files_by_type=files_by_type,
            discovered_files=discovery_result,
            discovery_time=discovery_time,
            errors=errors,
            strategy_name=self.get_strategy_name(),
            strategy_metadata=strategy_metadata
        )


class PersonalDocumentationDiscoveryStrategy(GeneralDocumentDiscoveryStrategy):
    """
    Personal Documentation Assistant specific discovery strategy.
    
    Inherits from GeneralDocumentDiscoveryStrategy and adds work item-specific metadata parsing.
    The work item filtering logic is handled by the calling code (upload scripts) which pass
    the correct root paths for discovery.
    """
    
    def __init__(self):
        """
        Initialize the Personal Documentation Assistant discovery strategy.
        
        Uses default extensions optimized for personal documentation (primarily markdown).
        """
        # Initialize with Personal Documentation specific extensions
        super().__init__(extensions=['.md', '.txt', '.docx'], recursive=True)
    
    def get_strategy_name(self) -> str:
        """Get the name of this discovery strategy."""
        return "PersonalDocumentationAssistant"
    
    def parse_result(self, discovery_result: List[Path], discovery_time: float, **kwargs) -> DocumentDiscoveryResult:
        """
        Parse the file paths into DocumentDiscoveryResult format with work item metadata.
        
        Args:
            discovery_result: List of discovered file paths
            discovery_time: Time taken for discovery
            **kwargs: Additional parsing parameters (errors, work_items, etc.)
            
        Returns:
            DocumentDiscoveryResult: Parsed result for the pipeline with work item metadata
        """
        errors = kwargs.get('errors', [])
        
        # Analyze file types
        files_by_type = {}
        for file_path in discovery_result:
            file_type = file_path.suffix.lower()
            files_by_type[file_type] = files_by_type.get(file_type, 0) + 1
        
        # Extract work items actually found in the discovered files
        work_items_found = set()
        work_items_file_count = {}
        
        for file_path in discovery_result:
            # Try to extract work item ID from the file path
            path_parts = file_path.parts
            for part in path_parts:
                # Look for work item patterns like "Bug 1234567" or "WI-1234567"
                if (part.startswith('Bug ') or part.startswith('WI-') or 
                    part.startswith('wi-') or part.startswith('Task ') or
                    part.startswith('Feature ')):
                    work_item_id = part
                    work_items_found.add(work_item_id)
                    work_items_file_count[work_item_id] = work_items_file_count.get(work_item_id, 0) + 1
                    break
        
        # Create strategy-specific metadata with work item information
        strategy_metadata = {
            'work_items_found': list(work_items_found),
            'work_items_file_count': work_items_file_count,
            'extensions_used': self.get_supported_extensions()
        }
        
        return DocumentDiscoveryResult(
            total_files=len(discovery_result),
            files_by_type=files_by_type,
            discovered_files=discovery_result,
            discovery_time=discovery_time,
            errors=errors,
            strategy_name=self.get_strategy_name(),
            strategy_metadata=strategy_metadata
        )
