"""
Logging Utility for ChromaDB Scripts
===================================

Centralized logging utility that duplicates console output to a file when specified.
Preserves existing print() statements while adding file logging capability.

Usage:
    from logging_utils import ScriptLogger, setup_script_logging
    
    # Initialize logger (console + optional file)
    logger = setup_script_logging(log_file="upload.log")
    
    # Use alongside existing print statements
    print("🔧 Initializing ChromaDB services...")
    logger.log("🔧 Initializing ChromaDB services...")
    
    # Or use the combined method
    logger.print_and_log("✅ Upload completed successfully")
"""

import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

# Constant log directory path
DEFAULT_LOG_DIRECTORY = r"C:\Users\aayushalok\OneDrive - Microsoft\Desktop\Personal Projects\DocumentationRetrievalMCPServer\ScriptExecutionLogs"

# IST timezone (UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))


class ScriptLogger:
    """
    A logger that duplicates console output to a file when specified.
    Designed to work alongside existing print() statements.
    """
    
    def __init__(self, log_file: Optional[str] = None, script_path: Optional[str] = None):
        """
        Initialize the logger.
        
        Args:
            log_file: Path to log file. If None, auto-generates based on script_path and IST timestamp.
            script_path: Path to the script that's being logged (for auto-generated log names).
        """
        if log_file is None and script_path:
            # Auto-generate log file name based on script path and IST timestamp
            ist_time = datetime.now(IST)
            timestamp = ist_time.strftime('%Y%m%d_%H%M%S_IST')
            
            # Extract script name from path
            script_name = Path(script_path).stem
            log_filename = f"{script_name}_{timestamp}.log"
            
            # Use default log directory
            self.log_file = str(Path(DEFAULT_LOG_DIRECTORY) / log_filename)
        else:
            self.log_file = log_file
        
        # Create log file if specified
        if self.log_file:
            log_path = Path(self.log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write header to log file
            ist_time = datetime.now(IST)
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(f"\n{'='*80}\n")
                f.write(f"ChromaDB Script Execution Log\n")
                f.write(f"Script: {script_path or 'Unknown'}\n")
                f.write(f"Started: {ist_time.isoformat()}\n")
                f.write(f"{'='*80}\n")
    
    def log(self, message: str, end: str = '\n'):
        """
        Log a message to file only (assumes console output already happened via print).
        
        Args:
            message: The message to log
            end: String appended after the message (default: newline)
        """
        # Output to file if specified
        if self.log_file:
            try:
                with open(self.log_file, 'a', encoding='utf-8') as f:
                    # Create clean version for file (remove ANSI codes if any)
                    clean_message = self._clean_message(message)
                    ist_time = datetime.now(IST)
                    timestamp = ist_time.strftime('%H:%M:%S IST')
                    f.write(f"{timestamp} | {clean_message}{end}")
            except Exception as e:
                # Fallback warning to console if file write fails
                print(f"⚠️  Log file write failed: {e}")
    
    def print_and_log(self, message: str, end: str = '\n'):
        """
        Print to console AND log to file in one call.
        
        Args:
            message: The message to print and log
            end: String appended after the message (default: newline)
        """
        # Print to console
        print(message, end=end)
        
        # Log to file
        self.log(message, end=end)
    
    def _clean_message(self, message: str) -> str:
        """Remove ANSI escape codes for clean file output"""
        import re
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', message)
    
    def close_log(self):
        """Close the log with a footer"""
        if self.log_file:
            try:
                with open(self.log_file, 'a', encoding='utf-8') as f:
                    ist_time = datetime.now(IST)
                    f.write(f"\nScript completed at {ist_time.isoformat()}\n")
                    f.write(f"{'='*80}\n\n")
            except Exception:
                pass


def setup_script_logging(log_file: Optional[str] = None, script_path: Optional[str] = None) -> ScriptLogger:
    """
    Convenience function to set up script logging that works with existing print statements.
    
    Args:
        log_file: Path to log file. If None, auto-generates based on script_path and IST timestamp.
        script_path: Path to the script being logged (used for auto-generated log names).
    
    Returns:
        Configured ScriptLogger instance
    """
    # Auto-detect script path if not provided
    if script_path is None:
        # Get the calling script's path from stack frame
        import inspect
        frame = inspect.currentframe()
        try:
            # Go up the call stack to find the main script
            while frame.f_back:
                frame = frame.f_back
                if '__file__' in frame.f_globals:
                    script_path = frame.f_globals['__file__']
                    break
        finally:
            del frame
    
    # If log_file is provided and relative, make it relative to DEFAULT_LOG_DIRECTORY
    if log_file and not Path(log_file).is_absolute():
        log_file = str(Path(DEFAULT_LOG_DIRECTORY) / log_file)
    
    return ScriptLogger(log_file=log_file, script_path=script_path)


# Utility functions for common logging patterns
def create_timestamped_logger(script_path: str) -> ScriptLogger:
    """Create a logger with auto-generated timestamped filename based on script path"""
    return setup_script_logging(script_path=script_path)


def create_custom_logger(script_path: str, log_filename: str) -> ScriptLogger:
    """Create a logger with custom filename in the default log directory"""
    log_file = str(Path(DEFAULT_LOG_DIRECTORY) / log_filename)
    return ScriptLogger(log_file=log_file, script_path=script_path)


def get_caller_script_path() -> str:
    """Get the path of the calling script"""
    import inspect
    frame = inspect.currentframe()
    try:
        # Go up the call stack to find the main script
        while frame.f_back:
            frame = frame.f_back
            if '__file__' in frame.f_globals:
                return frame.f_globals['__file__']
    finally:
        del frame
    return "unknown_script"
