"""
File Processing Tracker
======================

Handles idempotent file processing by tracking file signatures and processing state.
This ensures that unchanged files are not reprocessed, improving efficiency.
"""

import json
import hashlib
from pathlib import Path
from typing import Dict


def get_file_signature(file_path: Path) -> str:
    """
    Generate a unique signature for a file based on path, size, and modification time.
    
    This signature is used to detect if a file has changed since last processing.
    
    Args:
        file_path: Path to the file
        
    Returns:
        str: MD5 hash of the file's signature data
    """
    stat = file_path.stat()
    signature_data = f"{file_path}:{stat.st_size}:{stat.st_mtime}"
    return hashlib.md5(signature_data.encode()).hexdigest()


def load_processed_files(tracking_file: Path) -> Dict[str, str]:
    """
    Load the processed files tracking data from JSON file.
    
    Args:
        tracking_file: Path to the tracking JSON file
        
    Returns:
        Dict[str, str]: Mapping of file paths to their signatures
    """
    if tracking_file.exists():
        try:
            with open(tracking_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    return {}


def save_processed_files(tracking_file: Path, processed_files: Dict[str, str]):
    """
    Save the processed files tracking data to JSON file.
    
    Args:
        tracking_file: Path to the tracking JSON file
        processed_files: Dictionary mapping file paths to signatures
    """
    tracking_file.parent.mkdir(parents=True, exist_ok=True)
    with open(tracking_file, 'w', encoding='utf-8') as f:
        json.dump(processed_files, f, indent=2)


def is_file_already_processed(file_path: Path, processed_files: Dict[str, str]) -> bool:
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
    
    # If file is in tracking and signature matches, it's already processed
    return file_key in processed_files and processed_files[file_key] == current_signature


def mark_file_as_processed(file_path: Path, processed_files: Dict[str, str]):
    """
    Mark a file as processed by storing its signature.
    
    Args:
        file_path: Path to the file that was processed
        processed_files: Dictionary to update with the file signature
    """
    file_key = str(file_path)
    processed_files[file_key] = get_file_signature(file_path)


class ProcessingTracker:
    """
    Convenient class-based interface for file processing tracking.
    
    Example usage:
        tracker = ProcessingTracker("processed_files.json")
        if not tracker.is_processed(file_path):
            # Process the file...
            tracker.mark_processed(file_path)
            tracker.save()
    """
    
    def __init__(self, tracking_file_path: str):
        """
        Initialize the processing tracker.
        
        Args:
            tracking_file_path: Path to the JSON tracking file
        """
        self.tracking_file = Path(tracking_file_path)
        self.processed_files = load_processed_files(self.tracking_file)
    
    def is_processed(self, file_path: Path) -> bool:
        """Check if a file is already processed."""
        return is_file_already_processed(file_path, self.processed_files)
    
    def mark_processed(self, file_path: Path):
        """Mark a file as processed."""
        mark_file_as_processed(file_path, self.processed_files)
    
    def mark_unprocessed(self, file_path: Path):
        """Mark a file as unprocessed by removing it from tracking."""
        file_key = str(file_path)
        if file_key in self.processed_files:
            del self.processed_files[file_key]
    
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
