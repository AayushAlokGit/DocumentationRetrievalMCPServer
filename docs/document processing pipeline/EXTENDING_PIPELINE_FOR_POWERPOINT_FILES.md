# Extending Document Processing Pipeline for PowerPoint Files

## Overview

This document provides a guide for extending the existing document processing pipeline to support Microsoft PowerPoint files (`.pptx` format).

## Current Pipeline Architecture

The document processing pipeline consists of three main phases:

1. **Document Discovery Phase** - Finds and gathers relevant document files
2. **Document Processing Phase** - Extracts metadata, content, and prepares search objects
3. **Search Index Upload Phase** - Uploads processed documents to the search index

The processing phase uses a strategy pattern through the `DocumentProcessingStrategy` abstract base class.

## PowerPoint File Processing Requirements

### Supported File Formats

- `.pptx` - PowerPoint Open XML format (2007+)

### Content Extraction Goals

1. **Slide Text Content** - Extract text from all slides
2. **Speaker Notes** - Extract presenter notes if available
3. **Metadata** - Extract presentation metadata (title, author, creation date, etc.)
4. **Slide-based Chunking** - Option to chunk content by individual slides

### Content Handling Approach

**Text Content**: All readable text from slides and speaker notes will be extracted.

**Images and Media**: Images, charts, and other visual elements will be **ignored**. Only text-based content will be processed.

## Implementation Plan

### Step 1: Add PowerPoint Parsing Library

Add the required dependency:

```bash
pip install python-pptx
```

Update `requirements.txt`:

```
python-pptx>=1.0.0
```

### Step 2: Extend File Type Support

#### 2.1 Update File Type Mapping

Update the `_get_file_type` method:

```python
def _get_file_type(self, file_extension: str) -> str:
    """Map file extension to file type."""
    type_mapping = {
        '.md': 'markdown',
        '.txt': 'text',
        '.docx': 'document',
        '.pptx': 'presentation'
    }
    return type_mapping.get(file_extension, 'unknown')
```

#### 2.2 Add PowerPoint Import Support

Add PowerPoint library import:

```python
# File type specific parsing libraries
try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

try:
    from pptx import Presentation
    PPTX_AVAILABLE = True
except ImportError:
    PPTX_AVAILABLE = False
```

### Step 3: Implement PowerPoint Content Extraction

#### 3.1 Create PowerPoint Content Extraction Function

Add `_extract_pptx_content` function:

```python
def _extract_pptx_content(file_path: Path) -> Optional[Dict[str, Any]]:
    """
    Extract text content and metadata from a PowerPoint file.

    Args:
        file_path: Path to the PPTX file

    Returns:
        Optional[Dict]: Dictionary containing:
            - content: Full text content from all slides
            - slides: List of individual slide content
            - speaker_notes: Combined speaker notes
            - metadata: Presentation metadata
    """
    try:
        prs = Presentation(file_path)

        # Extract slide content
        slides_content = []
        all_text_parts = []
        speaker_notes = []

        for slide_num, slide in enumerate(prs.slides, 1):
            slide_text_parts = []
            slide_text_parts.append(f"=== Slide {slide_num} ===")

            # Extract text from all shapes in the slide (ignoring images)
            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text.strip():
                    slide_text_parts.append(shape.text.strip())
                # Note: Images and embedded objects are ignored in this implementation

            # Extract speaker notes if available
            if slide.has_notes_slide:
                notes_slide = slide.notes_slide
                notes_text_frame = notes_slide.notes_text_frame
                if notes_text_frame.text.strip():
                    speaker_notes.append(f"Slide {slide_num} Notes: {notes_text_frame.text.strip()}")

            # Combine slide content
            slide_content = "\n".join(slide_text_parts)
            slides_content.append(slide_content)
            all_text_parts.extend(slide_text_parts)

        # Combine all content
        full_content = "\n\n".join(all_text_parts)
        combined_notes = "\n\n".join(speaker_notes) if speaker_notes else ""

        # Extract presentation metadata
        core_props = prs.core_properties
        metadata = {
            'title': core_props.title or '',
            'author': core_props.author or '',
            'created': core_props.created.isoformat() if core_props.created else '',
            'modified': core_props.modified.isoformat() if core_props.modified else '',
            'slide_count': len(prs.slides),
            'has_notes': bool(speaker_notes)
        }

        return {
            'content': full_content,
            'slides': slides_content,
            'speaker_notes': combined_notes,
            'metadata': metadata
        } if full_content.strip() else None

    except Exception as e:
        print(f"Error extracting PowerPoint content from {file_path}: {e}")
        return None
```

#### 3.2 Update Main File Reading Function

Modify `_read_document_file` to handle PowerPoint files:

```python
def _read_document_file(file_path: Path) -> Optional[Dict]:
    """
    Read and parse a document file with file-type specific parsing.
    Supports different file types with appropriate parsing libraries.

    Supports: .md (markdown), .txt (text), .docx (Word documents), .pptx (PowerPoint)

    Args:
        file_path: Path to the document file

    Returns:
        Optional[Dict]: Dictionary with content and file_path, or None if failed
    """
    try:
        file_extension = file_path.suffix.lower()

        if file_extension == '.docx':
            # Parse DOCX files using python-docx
            if not DOCX_AVAILABLE:
                print(f"Warning: python-docx not available, cannot parse {file_path}")
                return None

            content = _extract_docx_content(file_path)
            if not content:
                return None

        elif file_extension == '.pptx':
            # Parse PowerPoint files using python-pptx
            if not PPTX_AVAILABLE:
                print(f"Warning: python-pptx not available, cannot parse {file_path}")
                return None

            pptx_data = _extract_pptx_content(file_path)
            if not pptx_data:
                return None

            # Use the full content for processing
            content = pptx_data['content']

            # Store additional PowerPoint-specific data for metadata extraction
            return {
                'content': content.strip(),
                'file_path': str(file_path),
                'pptx_data': pptx_data  # Additional PowerPoint-specific information
            }

        elif file_extension in ['.md', '.txt']:
            # Parse markdown and text files as UTF-8
            content = file_path.read_text(encoding='utf-8')

        else:
            # Unsupported file type
            print(f"Warning: Unsupported file type {file_extension} for {file_path}")
            return None

        if not content or not content.strip():
            return None  # Skip empty files

        return {
            'content': content.strip(),
            'file_path': str(file_path)
        }

    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None
```

### Step 4: Enhance Metadata Extraction for PowerPoint

#### 4.1 Update Metadata Extraction Strategy

Modify the `extract_metadata` method in `PersonalDocumentationAssistantAzureCognitiveSearchProcessingStrategy` to handle PowerPoint metadata:

```python
def extract_metadata(self, content: str, file_path: Path) -> Dict:
    """
    Extract comprehensive metadata using Personal Documentation Assistant strategy.
    Enhanced to support PowerPoint presentations.
    """
    try:
        # Determine file type
        file_extension = file_path.suffix.lower()
        file_type = self._get_file_type(file_extension)

        # Initialize metadata
        metadata = {}

        # Handle PowerPoint-specific metadata extraction
        if file_type == 'presentation':
            # PowerPoint files have additional structured data
            metadata = self._extract_powerpoint_metadata(content, file_path)
        else:
            # Handle other file types (existing logic)
            # ... existing code for markdown, text, docx ...

        # Common metadata extraction continues...
        work_item_id = self._extract_work_item_id(file_path)
        metadata['work_item_id'] = work_item_id
        metadata['file_type'] = file_type

        # Rest of existing metadata extraction logic...

        return metadata

    except Exception as e:
        return self._get_error_metadata(file_path, str(e))
```

#### 4.2 Add PowerPoint-Specific Metadata Extraction

```python
def _extract_powerpoint_metadata(self, content: str, file_path: Path) -> Dict:
    """
    Extract metadata specific to PowerPoint presentations.

    Args:
        content: Extracted text content from the presentation
        file_path: Path to the PowerPoint file

    Returns:
        Dict: PowerPoint-specific metadata
    """
    metadata = {'content': content}

    # Re-extract PowerPoint data for detailed metadata
    pptx_data = _extract_pptx_content(file_path)
    if pptx_data:
        # Add PowerPoint-specific metadata
        ppt_metadata = pptx_data['metadata']
        metadata.update({
            'slide_count': ppt_metadata.get('slide_count', 0),
            'presentation_title': ppt_metadata.get('title', ''),
            'presentation_author': ppt_metadata.get('author', ''),
            'has_speaker_notes': ppt_metadata.get('has_notes', False),
            'presentation_created': ppt_metadata.get('created', ''),
            'presentation_modified': ppt_metadata.get('modified', ''),
        })

        # Include speaker notes in content if available
        if pptx_data['speaker_notes']:
            metadata['speaker_notes'] = pptx_data['speaker_notes']
            # Optionally combine with main content
            metadata['content'] = content + "\n\n=== Speaker Notes ===\n" + pptx_data['speaker_notes']

        # Store individual slides for potential slide-based chunking
        metadata['slides_content'] = pptx_data['slides']

    return metadata
```

### Step 5: Implement Slide-Based Chunking (Optional Enhancement)

Create a specialized chunking strategy for PowerPoint files:

```python
class PowerPointSlideChunkingStrategy:
    """
    Chunking strategy that treats each slide as a separate chunk.
    Useful for PowerPoint presentations where each slide represents a distinct concept.
    """

    def __init__(self, include_speaker_notes: bool = True):
        self.include_speaker_notes = include_speaker_notes

    def chunk_powerpoint_content(self, pptx_data: Dict) -> List[str]:
        """
        Create chunks based on individual slides.

        Args:
            pptx_data: PowerPoint data from _extract_pptx_content

        Returns:
            List[str]: List of slide-based chunks
        """
        chunks = []

        slides = pptx_data.get('slides', [])
        speaker_notes = pptx_data.get('speaker_notes', '')

        # Parse speaker notes by slide if available
        notes_by_slide = {}
        if speaker_notes and self.include_speaker_notes:
            # Parse notes by slide using regex pattern
            import re
            # Pattern matches "Slide X Notes: content" and captures both slide number and content
            note_matches = re.findall(r'Slide (\d+) Notes: (.*?)(?=Slide \d+ Notes:|$)', speaker_notes, re.DOTALL)
            notes_by_slide = {int(slide_num): note.strip() for slide_num, note in note_matches}

        for i, slide_content in enumerate(slides, 1):
            chunk = slide_content

            # Add speaker notes if available for this slide
            if i in notes_by_slide:
                chunk += f"\n\nSpeaker Notes: {notes_by_slide[i]}"

            chunks.append(chunk)

        return chunks if chunks else [pptx_data.get('content', '')]
```

### Step 6: Update Processing Strategy

Modify the `process_single_document` method to use slide-based chunking for PowerPoint files:

```python
def process_single_document(self, file_path: Path) -> Optional[ProcessedDocument]:
    """
    Process a single document file with enhanced PowerPoint support.
    """
    # Read the document
    file_data = _read_document_file(file_path)
    if not file_data:
        return None

    content = file_data['content']
    file_extension = file_path.suffix.lower()

    # Extract metadata using strategy-specific logic
    metadata = self.extract_metadata(content, file_path)

    # Generate chunks - use slide-based chunking for PowerPoint
    if file_extension == '.pptx' and 'pptx_data' in file_data:
        slide_chunker = PowerPointSlideChunkingStrategy()
        chunks = slide_chunker.chunk_powerpoint_content(file_data['pptx_data'])
    else:
        # Use standard chunking strategy for other file types
        chunks = self.chunking_strategy.chunk_content(content)

    # Continue with existing processing logic...
    context_name = self.extract_context_info(metadata)
    additional_metadata = self.prepare_additional_metadata(metadata)

    return ProcessedDocument(
        document_id=self.generate_document_id(file_path),
        file_path=str(file_path),
        file_name=file_path.name,
        file_type=metadata.get('file_type', 'unknown'),
        title=metadata.get('title', file_path.stem),
        content=content,
        content_chunks=chunks,
        tags=metadata.get('tags', []),
        category=metadata.get('category', metadata.get('document_category')),
        context_name=context_name,
        last_modified=metadata.get('last_modified', datetime.now().isoformat() + 'Z'),
        chunk_count=len(chunks),
        processing_strategy=self.get_strategy_name(),
        metadata_json=json.dumps(additional_metadata) if additional_metadata else None
    )
```

## Testing Strategy

Create sample PowerPoint files and implement unit tests for content extraction, file reading, and chunking strategies.

## Error Handling

Handle common issues:

1. **Missing python-pptx Library** - Skip PowerPoint files if library unavailable
2. **Corrupted PowerPoint Files** - Catch parsing exceptions
3. **Empty Presentations** - Handle presentations with no extractable text content
4. **Large Presentations** - Monitor memory usage for presentations with many slides

Use specific exception handling for better error management:

```python
def _extract_pptx_content(file_path: Path) -> Optional[Dict[str, Any]]:
    """Enhanced with better error handling"""
    try:
        from pptx.exc import PackageNotFoundError, InvalidXmlError
        prs = Presentation(file_path)
        # ... existing extraction logic ...

    except PackageNotFoundError:
        print(f"PowerPoint file not found: {file_path}")
        return None
    except InvalidXmlError:
        print(f"Invalid or corrupted PowerPoint file: {file_path}")
        return None
    except Exception as e:
        print(f"Error extracting PowerPoint content from {file_path}: {e}")
        # Log detailed error for debugging
        import traceback
        print(f"Detailed error: {traceback.format_exc()}")
        return None
```

## Performance Considerations

PowerPoint files can be memory-intensive. Consider:

- Monitoring memory usage during processing
- Setting limits on concurrent PowerPoint processing
- Implementing cleanup after processing each file

## Future Enhancements

Potential improvements include:

- **Chart Data Extraction**: Extract data from embedded charts and tables
- **Image Text Extraction**: Use OCR to extract text from slide images
- **AI-Powered Enhancements**: Use LLM for slide summarization and topic extraction

## Conclusion

This implementation extends the document processing pipeline for PowerPoint files while maintaining consistency with existing file processing approaches.
