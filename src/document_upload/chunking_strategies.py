"""
Document Chunking Strategies
===========================

Simple, efficient chunking strategies for document processing.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class ChunkingConfig:
    """Configuration for chunking strategies."""
    max_chunk_size: int = 4000
    overlap: int = 200


class ChunkingStrategy(ABC):
    """Abstract base class for document chunking strategies."""
    
    def __init__(self, config: Optional[ChunkingConfig] = None):
        self.config = config or ChunkingConfig()
    
    @abstractmethod
    def chunk_content(self, content: str) -> List[str]:
        """Chunk the given content."""
        pass
    
    @abstractmethod
    def get_strategy_name(self) -> str:
        """Return the name of this chunking strategy."""
        pass


class SimpleChunkingStrategy(ChunkingStrategy):
    """
    Simple chunking strategy with overlap and basic sentence boundary detection.
    
    Features:
    - Configurable chunk size and overlap
    - Basic sentence boundary detection
    - Word-level fallback for edge cases
    """
    
    def get_strategy_name(self) -> str:
        return "SimpleChunking"
    
    def chunk_content(self, content: str) -> List[str]:
        """Split text into overlapping chunks."""
        if not content or len(content) <= self.config.max_chunk_size:
            return [content] if content else []
        
        chunks = []
        start = 0
        
        # Ensure overlap is safe and meaningful
        max_safe_overlap = min(self.config.overlap, self.config.max_chunk_size // 2)
        min_progress = max(self.config.max_chunk_size - max_safe_overlap, 50)  # Ensure we make progress but allow overlap
        
        while start < len(content):
            # Calculate end position
            end = min(start + self.config.max_chunk_size, len(content))
            
            # Try to find a good breaking point if not at the end
            if end < len(content):
                # Look for sentence endings within last 200 chars
                search_start = max(start, end - 200)
                sentence_end = self._find_sentence_end(content, search_start, end)
                if sentence_end and sentence_end > start + min_progress // 2:
                    end = sentence_end
            
            # Extract chunk
            chunk = content[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # If this was the last chunk, break
            if end >= len(content):
                break
                
            # Move start position with overlap, but ensure reasonable progress
            if max_safe_overlap > 0 and end - start >= min_progress:
                next_start = end - max_safe_overlap
            else:
                next_start = end  # No overlap if chunk is too small
                
            # Safety check: ensure we're making progress
            if next_start <= start:
                next_start = start + min_progress
                
            start = next_start
        
        return chunks
    
    def _find_sentence_end(self, content: str, search_start: int, end: int) -> Optional[int]:
        """Find a sentence ending within the search range."""
        for i in range(end - 1, search_start - 1, -1):
            if i < len(content) and content[i] in '.!?':
                # Check if next character is whitespace (good sentence ending)
                if i + 1 < len(content) and content[i + 1] in ' \n\t':
                    # Simple abbreviation check
                    if not self._is_abbreviation(content, i):
                        return i + 1
        return None
    
    def _is_abbreviation(self, content: str, period_pos: int) -> bool:
        """Basic abbreviation detection."""
        if period_pos <= 0:
            return False
        
        # Get the word before the period
        word_start = period_pos - 1
        while word_start > 0 and content[word_start - 1].isalnum():
            word_start -= 1
        
        word = content[word_start:period_pos].lower()
        
        # Common abbreviations
        common_abbrevs = {'mr', 'mrs', 'dr', 'prof', 'inc', 'ltd', 'vs', 'etc', 'i.e', 'e.g'}
        
        # Check for common abbreviations or single letters
        return word in common_abbrevs or (len(word) == 1 and word.isalpha())

# Factory function
def create_chunking_strategy(strategy_name: str = "simple", config: Optional[ChunkingConfig] = None) -> ChunkingStrategy:
    """
    Create a chunking strategy.
    
    Args:
        strategy_name: Name of the strategy ("simple" or "general")
        config: Configuration for the chunking strategy
        
    Returns:
        ChunkingStrategy: The requested chunking strategy
    """
    if strategy_name.lower() in ["simple", "general"]:
        return SimpleChunkingStrategy(config)
    else:
        raise ValueError(f"Unknown chunking strategy: {strategy_name}. Available: ['simple', 'general']")
