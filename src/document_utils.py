"""
Document Processing Utilities
============================

Utility functions for processing markdown documents, including file discovery,
metadata extraction, and text chunking for the Work Items documentation system.
"""

import re
import json
from pathlib import Path
from typing import List, Dict, Optional
import frontmatter


def discover_markdown_files(work_items_path: str) -> List[Path]:
    """
    Find all markdown files in the Work Items directory structure.
    
    Args:
        work_items_path: Path to the Work Items directory
        
    Returns:
        List[Path]: Sorted list of valid markdown file paths
        
    Raises:
        FileNotFoundError: If the Work Items directory doesn't exist
    """
    work_items_dir = Path(work_items_path)

    if not work_items_dir.exists():
        raise FileNotFoundError(f"Work Items directory does not exist: {work_items_path}")

    markdown_files = []

    # Iterate through each work item subdirectory
    for work_item_dir in work_items_dir.iterdir():
        if work_item_dir.is_dir():
            # Find all .md files in this work item directory
            work_item_md_files = list(work_item_dir.rglob("*.md"))

            # Filter out empty files and add to main list
            valid_files = [f for f in work_item_md_files if f.is_file() and f.stat().st_size > 0]
            markdown_files.extend(valid_files)

    return sorted(markdown_files)


def extract_metadata(content: str, file_path: Path) -> Dict:
    """
    Extract metadata from file content and directory structure.
    
    Extracts information from:
    - YAML frontmatter (title, tags, etc.)
    - First heading in content
    - Directory structure (work item ID)
    - File system metadata
    
    Args:
        content: Raw file content
        file_path: Path to the file
        
    Returns:
        Dict: Extracted metadata including title, work_item_id, tags, etc.
    """
    try:
        # Parse frontmatter if present
        # Note: Frontmatter is YAML metadata at the top of markdown files,
        # enclosed between '---' markers (e.g., title, tags, date)
        post = frontmatter.loads(content)
        metadata = dict(post.metadata) if post.metadata else {}

        # Extract work item ID from directory name
        work_item_dir = file_path.parent
        work_item_id = work_item_dir.name  # Directory name is the work item ID
        metadata['work_item_id'] = work_item_id

        # Extract title (priority: frontmatter > first heading > filename)
        if 'title' not in metadata:
            title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
            metadata['title'] = (
                title_match.group(1).strip() if title_match
                else file_path.stem.replace('_', ' ').replace('-', ' ')
            )

        # Extract tags from frontmatter or content
        if 'tags' not in metadata:
            tags = set()

            # From frontmatter
            if 'tags' in post.metadata:
                fm_tags = post.metadata['tags']
                if isinstance(fm_tags, list):
                    tags.update(str(tag).strip() for tag in fm_tags)
                elif isinstance(fm_tags, str):
                    tags.update(tag.strip() for tag in fm_tags.split(','))

            # From hashtags in content
            hashtags = re.findall(r'#(\w+)', content)
            tags.update(hashtags)

            # Add work item ID as a tag for easier searching
            tags.add(work_item_id)

            metadata['tags'] = sorted(list(tags)) if tags else [work_item_id]

        # File system metadata
        file_stat = file_path.stat()
        metadata['last_modified'] = file_stat.st_mtime
        metadata['work_item_directory'] = str(work_item_dir)

        return metadata

    except Exception as e:
        # Return minimal metadata on error, but always include work item ID
        work_item_id = file_path.parent.name
        return {
            'title': file_path.stem.replace('_', ' ').replace('-', ' '),
            'work_item_id': work_item_id,
            'last_modified': file_path.stat().st_mtime,
            'tags': [work_item_id],
            'work_item_directory': str(file_path.parent)
        }


def read_markdown_file(file_path: Path) -> Optional[Dict]:
    """
    Read and parse a markdown file with metadata extraction.
    
    Args:
        file_path: Path to the markdown file
        
    Returns:
        Optional[Dict]: Dictionary with content, file_path, and metadata, or None if failed
    """
    try:
        # Read file content
        content = file_path.read_text(encoding='utf-8')

        if not content.strip():
            return None  # Skip empty files

        # Extract metadata
        metadata = extract_metadata(content, file_path)

        # Remove frontmatter from content
        post = frontmatter.loads(content)
        clean_content = post.content if post.metadata else content

        return {
            'content': clean_content.strip(),
            'file_path': str(file_path),
            'metadata': metadata
        }

    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None


def simple_chunk_text(content: str, max_chunk_size: int = 4000, overlap: int = 200) -> List[str]:
    """
    Split text into chunks with simple sentence-based splitting.
    
    This function:
    1. Splits by paragraphs first
    2. If paragraphs are too long, splits by sentences  
    3. Creates overlapping chunks to maintain context
    4. Ensures chunks don't exceed max_chunk_size
    
    Args:
        content: Text content to chunk
        max_chunk_size: Maximum characters per chunk
        overlap: Number of words to overlap between chunks
        
    Returns:
        List[str]: List of text chunks
    """
    # Split by paragraphs first
    paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]

    chunks = []
    current_chunk = ""

    for paragraph in paragraphs:
        # If paragraph is too long, split by sentences
        if len(paragraph) > max_chunk_size:
            sentences = re.split(r'(?<=[.!?])\s+', paragraph)

            for sentence in sentences:
                if len(current_chunk) + len(sentence) > max_chunk_size:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                        # Create overlap with last few words
                        overlap_text = ' '.join(current_chunk.split()[-20:]) if current_chunk else ""
                        current_chunk = overlap_text + " " + sentence if overlap_text else sentence
                    else:
                        current_chunk = sentence
                else:
                    current_chunk = current_chunk + " " + sentence if current_chunk else sentence
        else:
            # Check if adding this paragraph exceeds limit
            if len(current_chunk) + len(paragraph) > max_chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    # Create overlap
                    overlap_text = ' '.join(current_chunk.split()[-20:]) if current_chunk else ""
                    current_chunk = overlap_text + "\n\n" + paragraph if overlap_text else paragraph
                else:
                    current_chunk = paragraph
            else:
                current_chunk = current_chunk + "\n\n" + paragraph if current_chunk else paragraph

    # Add final chunk
    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks


def process_document_chunks(file_data: Dict) -> List[str]:
    """
    Process a document and return text chunks.
    
    Args:
        file_data: Dictionary containing document content and metadata
        
    Returns:
        List[str]: List of text chunks ready for embedding
    """
    content = file_data['content']
    return simple_chunk_text(content)
