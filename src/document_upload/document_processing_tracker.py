"""
File Processing Tracker
======================

Handles idempotent file processing by tracking file signatures and processing state.
This ensures that unchanged files are not reprocessed, improving efficiency.
"""

import json
import os
from pathlib import Path
from typing import Dict


def get_file_signature(file_path) -> Dict[str, any]:
    """
    Generate a unique signature for a file based on path, size, and modification time.
    
    This signature is used to detect if a file has changed since last processing.
    Returns the values directly for better visibility instead of a hash.
    
    Args:
        file_path: Path to the file (can be string or Path object)
        
    Returns:
        Dict[str, any]: Dictionary containing path, size, and modification time
    """
    # Convert to Path object if it's a string
    if isinstance(file_path, str):
        file_path = Path(file_path)
    
    stat = file_path.stat()
    return {
        "path": str(file_path),
        "size": stat.st_size,
        "mtime": stat.st_mtime
    }


def load_processed_files(tracking_file: Path) -> Dict[str, Dict[str, any]]:
    """
    Load the processed files tracking data from JSON file.
    
    Args:
        tracking_file: Path to the tracking JSON file
        
    Returns:
        Dict[str, Dict[str, any]]: Mapping of file paths to their signature data
    """
    if tracking_file.exists():
        try:
            with open(tracking_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    return {}


def save_processed_files(tracking_file: Path, processed_files: Dict[str, Dict[str, any]]):
    """
    Save the processed files tracking data to JSON file.
    
    Args:
        tracking_file: Path to the tracking JSON file
        processed_files: Dictionary mapping file paths to signature data
    """
    tracking_file.parent.mkdir(parents=True, exist_ok=True)
    with open(tracking_file, 'w', encoding='utf-8') as f:
        json.dump(processed_files, f, indent=2)


def is_file_already_processed(file_path: Path, processed_files: Dict[str, Dict[str, any]]) -> bool:
    """
    Check if a file has already been processed based on its signature.
    
    Args:
        file_path: Path to the file to check
        processed_files: Dictionary of already processed files
        
    Returns:
        bool: True if file is already processed and unchanged
    """
    file_key = str(file_path)
    current_signature = get_file_signature(file_path)
    
    # If file is in tracking, compare all signature components
    if file_key in processed_files:
        stored_signature = processed_files[file_key]
        return (
            stored_signature.get("size") == current_signature["size"] and
            stored_signature.get("mtime") == current_signature["mtime"] and
            stored_signature.get("path") == current_signature["path"]
        )
    
    return False


def mark_file_as_processed(file_path: Path, processed_files: Dict[str, Dict[str, any]], fileMetadata: Dict[str, any] | None = None):
    """
    Mark a file as processed by storing its signature data and optional metadata.
    
    Args:
        file_path: Path to the file that was processed
        processed_files: Dictionary to update with the file signature data
        fileMetadata: Optional metadata dictionary to store with the file record
    """
    # Ensure file_path is a Path object
    if isinstance(file_path, str):
        file_path = Path(file_path)
        
    file_key = str(file_path)
    file_record = get_file_signature(file_path)
    
    # Add metadata to the file record if provided
    if fileMetadata:
        file_record["metadata"] = fileMetadata
    
    processed_files[file_key] = file_record


class DocumentProcessingTracker:
    """
    Document processing tracker that manages file tracking for document upload pipeline.
    
    This tracker automatically initializes its tracking source from environment configuration
    and provides idempotent file processing capabilities. The tracker ensures that unchanged
    files are not reprocessed, improving efficiency.
    
    Example usage:
        tracker = DocumentProcessingTracker("processed_files.json")
        if not tracker.is_processed(file_path):
            # Process the file...
            tracker.mark_processed(file_path)
            tracker.save()
    """
    
    def __init__(self, tracking_file_name: str = "processed_files.json"):
        """
        Initialize the document processing tracker.
        
        The tracker automatically determines its tracking source from the environment:
        - Primary: Uses PERSONAL_DOCUMENTATION_ROOT_DIRECTORY environment variable
        - Fallback: Uses current working directory
        
        Args:
            tracking_file_name: Name of the JSON tracking file (default: "processed_files.json")
        """
        self.tracking_file_name = tracking_file_name
        self._initialize_tracking_source()
        self.processed_files = load_processed_files(self.tracking_file)
    
    def _initialize_tracking_source(self):
        """
        Initialize the tracking source based on environment configuration.
        
        This method provides future extensibility for different tracking sources
        while currently using the PERSONAL_DOCUMENTATION_ROOT_DIRECTORY environment variable.
        """
        # Primary tracking source: PERSONAL_DOCUMENTATION_ROOT_DIRECTORY environment variable
        PERSONAL_DOCUMENTATION_ROOT_DIRECTORY = os.getenv('PERSONAL_DOCUMENTATION_ROOT_DIRECTORY')
        
        if not PERSONAL_DOCUMENTATION_ROOT_DIRECTORY:
            raise EnvironmentError("PERSONAL_DOCUMENTATION_ROOT_DIRECTORY environment variable is required but not set")
        
        work_items_dir = Path(PERSONAL_DOCUMENTATION_ROOT_DIRECTORY)
        if not work_items_dir.exists():
            raise FileNotFoundError(f"PERSONAL_DOCUMENTATION_ROOT_DIRECTORY directory not found: {PERSONAL_DOCUMENTATION_ROOT_DIRECTORY}")
        
        # Use work items directory as tracking source
        self.tracking_source = work_items_dir
        self.tracking_file = self.tracking_source / self.tracking_file_name
        print(f"[TRACKER] Initialized with work items tracking source: {self.tracking_file}")
    
    def get_tracking_source(self) -> Path:
        """
        Get the current tracking source directory.
        
        Returns:
            Path: The directory where tracking files are stored
        """
        return self.tracking_source
    
    def is_processed(self, file_path: Path) -> bool:
        """Check if a file is already processed."""
        return is_file_already_processed(file_path, self.processed_files)
    
    def mark_processed(self, file_path: Path, fileMetadata: Dict[str, any] | None = None):
        """Mark a file as processed with optional metadata."""
        mark_file_as_processed(file_path, self.processed_files, fileMetadata)
    
    def mark_unprocessed(self, file_path: Path):
        """Mark a file as unprocessed by removing it from tracking."""
        file_key = str(file_path)
        if file_key in self.processed_files:
            del self.processed_files[file_key]
    
    def get_file_metadata(self, file_path: Path) -> Dict[str, any] | None:
        """
        Get the stored metadata for a processed file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dict[str, any] | None: The stored metadata, or None if file not tracked or no metadata stored
        """
        file_key = str(file_path)
        if file_key in self.processed_files:
            return self.processed_files[file_key].get("metadata")
        return None
    
    def reset(self):
        """Reset all tracking data (clears all processed files)."""
        self.processed_files.clear()
    
    def save(self):
        """Save the current tracking state to file."""
        save_processed_files(self.tracking_file, self.processed_files)
    
    def get_stats(self) -> Dict[str, int]:
        """Get statistics about processed files."""
        return {
            'total_processed': len(self.processed_files),
            'tracking_file_exists': self.tracking_file.exists()
        }
    
    def clear(self):
        """Clear all tracking data (use with caution)."""
        self.processed_files.clear()
        if self.tracking_file.exists():
            self.tracking_file.unlink()
