#!/usr/bin/env python3
"""
Document Chunking Test Script
============================

This script tests the chunking strategies by reading a file and displaying the generated chunks.

Usage:
    python test_file_chunking.py <file_path> [options]

Examples:
    python test_file_chunking.py document.txt
    python test_file_chunking.py document.docx --chunk-size 2000 --overlap 100
    python test_file_chunking.py document.md --strategy simple --show-overlap
"""

import sys
import argparse
from pathlib import Path
from typing import Optional

# Import chunking strategies
from chunking_strategies import create_chunking_strategy, ChunkingConfig

# Import document reading utilities from processing strategies
from processing_strategies import _read_document_file


def read_file_content(file_path: Path) -> Optional[str]:
    """
    Read content from various file types.
    
    Args:
        file_path: Path to the file to read
        
    Returns:
        Optional[str]: File content or None if failed
    """
    try:
        # Use the existing document reading function
        file_data = _read_document_file(file_path)
        if file_data:
            return file_data['content']
        
        # Fallback for plain text files
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
            
    except Exception as e:
        print(f"❌ Error reading file {file_path}: {e}")
        return None


def analyze_overlap(chunk1: str, chunk2: str, max_check: int = 300) -> Optional[str]:
    """
    Find overlap between two consecutive chunks.
    
    Args:
        chunk1: First chunk
        chunk2: Second chunk
        max_check: Maximum characters to check for overlap
        
    Returns:
        Optional[str]: Overlapping text or None if no overlap found
    """
    # Check for overlap by finding common substrings
    chunk1_clean = chunk1.strip()
    chunk2_clean = chunk2.strip()
    
    if not chunk1_clean or not chunk2_clean:
        return None
    
    # Minimum meaningful overlap threshold
    min_meaningful_overlap = max(20, min(len(chunk1_clean), len(chunk2_clean)) // 10)
    
    # Try different approaches to find overlap
    max_overlap_len = 0
    best_overlap = None
    
    # Approach 1: Check if end of chunk1 appears in beginning of chunk2
    search_len = min(max_check, len(chunk1_clean), len(chunk2_clean))
    
    for length in range(search_len, min_meaningful_overlap, -1):
        chunk1_end = chunk1_clean[-length:]
        
        # Look for this text in the beginning of chunk2
        pos = chunk2_clean.find(chunk1_end)
        if pos != -1 and pos < length:  # Found near the beginning
            if length > max_overlap_len:
                max_overlap_len = length
                best_overlap = chunk1_end
                break
    
    # Approach 2: Check for word-level overlap (more flexible)
    if not best_overlap:
        chunk1_words = chunk1_clean.split()
        chunk2_words = chunk2_clean.split()
        
        if len(chunk1_words) >= 3 and len(chunk2_words) >= 3:
            # Look for overlapping word sequences
            for word_count in range(min(20, len(chunk1_words), len(chunk2_words)), 3, -1):
                chunk1_end_words = chunk1_words[-word_count:]
                chunk1_end_text = ' '.join(chunk1_end_words)
                
                # Check if this word sequence appears in chunk2
                if chunk1_end_text.lower() in chunk2_clean.lower():
                    overlap_len = len(chunk1_end_text)
                    if overlap_len > max_overlap_len and overlap_len >= min_meaningful_overlap:
                        max_overlap_len = overlap_len
                        best_overlap = chunk1_end_text
                        break
    
    return best_overlap


def display_chunks(chunks: list[str], show_overlap: bool = False):
    """
    Display chunks with detailed information.
    
    Args:
        chunks: List of text chunks
        show_overlap: Whether to show overlap analysis
    """
    print(f"\n📊 Generated {len(chunks)} chunks:")
    print("=" * 80)
    
    total_chars = 0
    overlapping_chars = 0
    
    for i, chunk in enumerate(chunks, 1):
        chunk_length = len(chunk)
        total_chars += chunk_length
        
        print(f"\n📝 Chunk {i} ({chunk_length} characters):")
        print("-" * 50)
        
        # Show first and last few lines for context
        lines = chunk.strip().split('\n')
        if len(lines) <= 6:
            # Show all lines if chunk is small
            for line in lines:
                print(f"    {line}")
        else:
            # Show first 3 and last 3 lines for large chunks
            for line in lines[:3]:
                print(f"    {line}")
            print(f"    ... ({len(lines) - 6} more lines) ...")
            for line in lines[-3:]:
                print(f"    {line}")
        
        # Analyze overlap with previous chunk
        if show_overlap and i > 1:
            overlap = analyze_overlap(chunks[i-2], chunk)
            if overlap:
                overlap_length = len(overlap)
                overlapping_chars += overlap_length
                print(f"\n🔗 Overlap with previous chunk ({overlap_length} chars):")
                print(f"    '{overlap[:100]}{'...' if len(overlap) > 100 else ''}'")
            else:
                print(f"\n❌ No overlap detected with previous chunk")
    
    print("\n" + "=" * 80)
    print(f"📈 Summary:")
    print(f"   • Total chunks: {len(chunks)}")
    print(f"   • Total characters: {total_chars:,}")
    print(f"   • Average chunk size: {total_chars // len(chunks) if chunks else 0} characters")
    
    if show_overlap and len(chunks) > 1:
        print(f"   • Overlapping characters: {overlapping_chars:,}")
        print(f"   • Overlap efficiency: {(overlapping_chars / total_chars * 100):.1f}%")
    
    # Show chunk size distribution
    if chunks:
        sizes = [len(chunk) for chunk in chunks]
        print(f"   • Chunk sizes: min={min(sizes)}, max={max(sizes)}, median={sorted(sizes)[len(sizes)//2]}")


def main():
    """Main function to handle command line arguments and run chunking test."""
    parser = argparse.ArgumentParser(
        description="Test document chunking strategies",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s document.txt
  %(prog)s document.docx --chunk-size 2000 --overlap 100
  %(prog)s document.md --strategy simple --show-overlap
        """
    )
    
    parser.add_argument(
        "file_path",
        help="Path to the file to chunk"
    )
    
    parser.add_argument(
        "--chunk-size", "-s",
        type=int,
        default=4000,
        help="Maximum chunk size in characters (default: 4000)"
    )
    
    parser.add_argument(
        "--overlap", "-o",
        type=int,
        default=200,
        help="Overlap size in characters (default: 200)"
    )
    
    parser.add_argument(
        "--strategy",
        choices=["simple", "general"],
        default="simple",
        help="Chunking strategy to use (default: simple)"
    )
    
    parser.add_argument(
        "--show-overlap",
        action="store_true",
        help="Show overlap analysis between chunks"
    )
    
    parser.add_argument(
        "--show-content",
        action="store_true",
        help="Show full content of chunks (default: abbreviated)"
    )
    
    args = parser.parse_args()
    
    # Validate file path
    file_path = Path(args.file_path)
    if not file_path.exists():
        print(f"❌ Error: File '{file_path}' does not exist")
        sys.exit(1)
    
    if not file_path.is_file():
        print(f"❌ Error: '{file_path}' is not a file")
        sys.exit(1)
    
    print(f"🔍 Reading file: {file_path}")
    print(f"📏 File size: {file_path.stat().st_size:,} bytes")
    
    # Read file content
    content = read_file_content(file_path)
    if not content:
        print("❌ Failed to read file content")
        sys.exit(1)
    
    print(f"📖 Content length: {len(content):,} characters")
    print(f"📄 Content lines: {len(content.splitlines()):,}")
    
    # Create chunking strategy
    config = ChunkingConfig(
        max_chunk_size=args.chunk_size,
        overlap=args.overlap
    )
    
    print(f"\n⚙️  Chunking Configuration:")
    print(f"   • Strategy: {args.strategy}")
    print(f"   • Max chunk size: {config.max_chunk_size:,} characters")
    print(f"   • Overlap: {config.overlap:,} characters")
    
    try:
        chunker = create_chunking_strategy(args.strategy, config)
        
        # Generate chunks
        print(f"\n🔄 Chunking content...")
        chunks = chunker.chunk_content(content)
        
        if not chunks:
            print("⚠️  No chunks generated")
            sys.exit(1)
        
        # Display results
        if args.show_content:
            # Show full content mode
            for i, chunk in enumerate(chunks, 1):
                print(f"\n📝 Chunk {i} ({len(chunk)} characters):")
                print("-" * 50)
                print(chunk)
                print("-" * 50)
        else:
            # Show abbreviated mode
            display_chunks(chunks, args.show_overlap)
            
    except Exception as e:
        print(f"❌ Error during chunking: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
