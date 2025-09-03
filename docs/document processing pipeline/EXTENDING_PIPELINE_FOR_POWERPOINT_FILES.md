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

### Content Handling Approach

**Text Content**: All readable text from slides and speaker notes will be extracted.

**Images and Media**: Images, charts, and other visual elements will be **ignored**. Only text-based content will be processed.

## Implementation Plan

### Architectural Principle: Separation of Concerns

This implementation follows a key architectural principle: **separation of content extraction from metadata processing**. This approach provides:

1. **Cleaner Code Organization** - Content extraction functions focus solely on extracting text and structural data
2. **Better Reusability** - Content extraction can be reused across different processing strategies
3. **Strategy Flexibility** - Different processing strategies can interpret the same content differently
4. **Easier Testing** - Content extraction and metadata processing can be tested independently
5. **Maintainability** - Changes to metadata logic don't affect content extraction logic

**Content Extraction Phase** (Strategy-Independent):

- Extract text content from slides
- Extract speaker notes
- Extract basic structural information (slide count)
- **No metadata interpretation** - just raw content

**Document Processing Phase** (Strategy-Dependent):

- Interpret content based on processing strategy context
- Extract presentation metadata (title, author, dates)
- Apply strategy-specific metadata enrichment
- Handle context-specific processing needs

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
    Extract text content from a PowerPoint file.

    NOTE: This function focuses ONLY on content extraction. Metadata extraction
    is handled separately in the document processing phase for better separation
    of concerns and reusability across different processing strategies.

    Args:
        file_path: Path to the PPTX file

    Returns:
        Optional[Dict]: Dictionary containing:
            - content: Full text content from all slides and speaker notes
    """
    try:
        prs = Presentation(file_path)

        # Extract slide content
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

            # Add slide content to overall content
            all_text_parts.extend(slide_text_parts)

        # Combine all content including speaker notes
        full_content = "\n\n".join(all_text_parts)
        if speaker_notes:
            combined_notes = "\n\n".join(speaker_notes)
            full_content += "\n\n=== Speaker Notes ===\n" + combined_notes

        return {
            'content': full_content
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

    This method handles PowerPoint metadata extraction in the document processing phase,
    maintaining separation of concerns by keeping metadata logic separate from content extraction.

    Args:
        content: Extracted text content from the presentation
        file_path: Path to the PowerPoint file

    Returns:
        Dict: PowerPoint-specific metadata
    """
    metadata = {'content': content}

    # Extract PowerPoint metadata directly using python-pptx
    try:
        from pptx import Presentation
        prs = Presentation(file_path)

        # Extract presentation metadata
        core_props = prs.core_properties
        metadata.update({
            'slide_count': len(prs.slides),
            'presentation_title': core_props.title or '',
            'presentation_author': core_props.author or '',
            'presentation_created': core_props.created.isoformat() if core_props.created else '',
            'presentation_modified': core_props.modified.isoformat() if core_props.modified else '',
        })

        # Check for speaker notes
        has_notes = False
        speaker_notes = []
        for slide_num, slide in enumerate(prs.slides, 1):
            if slide.has_notes_slide:
                notes_slide = slide.notes_slide
                notes_text_frame = notes_slide.notes_text_frame
                if notes_text_frame.text.strip():
                    has_notes = True
                    speaker_notes.append(f"Slide {slide_num} Notes: {notes_text_frame.text.strip()}")

        metadata['has_speaker_notes'] = has_notes

        # Include speaker notes in content if available
        if speaker_notes:
            combined_notes = "\n\n".join(speaker_notes)
            metadata['speaker_notes'] = combined_notes
            # Optionally combine with main content
            metadata['content'] = content + "\n\n=== Speaker Notes ===\n" + combined_notes

    except Exception as e:
        print(f"Error extracting PowerPoint metadata from {file_path}: {e}")
        # Continue with basic metadata if PowerPoint-specific extraction fails
        metadata.update({
            'slide_count': 0,
            'presentation_title': '',
            'presentation_author': '',
            'has_speaker_notes': False,
            'presentation_created': '',
            'presentation_modified': '',
        })

    return metadata
```

### Step 5: Update Processing Strategy

PowerPoint files will use the standard chunking strategy alongside other file types:

```python
def process_single_document(self, file_path: Path) -> Optional[ProcessedDocument]:
    """
    Process a single document file with PowerPoint support.
    PowerPoint files use standard chunking like other document types.
    """
    # Read the document
    file_data = _read_document_file(file_path)
    if not file_data:
        return None

    content = file_data['content']

    # Extract metadata using strategy-specific logic
    metadata = self.extract_metadata(content, file_path)

    # Generate chunks using standard chunking strategy for all file types
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

Create sample PowerPoint files and implement unit tests for content extraction and file reading.

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

        # Extract content from all slides and speaker notes
        all_text_parts = []
        speaker_notes = []

        for slide_num, slide in enumerate(prs.slides, 1):
            # Extract slide text and notes...
            pass

        # Combine all content
        full_content = "\n\n".join(all_text_parts)
        if speaker_notes:
            combined_notes = "\n\n".join(speaker_notes)
            full_content += "\n\n=== Speaker Notes ===\n" + combined_notes

        return {
            'content': full_content
        } if full_content.strip() else None

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

This implementation extends the document processing pipeline for PowerPoint files while maintaining consistency with existing file processing approaches and following key architectural principles:

### Key Architectural Improvements

1. **Separation of Concerns**: Content extraction is separated from metadata processing, creating cleaner, more maintainable code
2. **Strategy Pattern Compliance**: PowerPoint processing follows the same strategy pattern as other file types
3. **Reusability**: Content extraction functions can be reused across different processing strategies
4. **Testability**: Content extraction and metadata processing can be tested independently
5. **Extensibility**: New processing strategies can easily handle PowerPoint files with different metadata requirements

### Implementation Benefits

- **Consistent Architecture**: PowerPoint processing follows the same three-phase pipeline as other file types
- **Error Isolation**: Content extraction errors are separate from metadata processing errors
- **Performance Optimization**: Content is extracted once and reused for both chunking and metadata processing
- **Memory Efficiency**: No redundant file parsing between content extraction and metadata phases
- **Maintainability**: Changes to metadata logic don't require changes to content extraction logic

This approach ensures that PowerPoint support integrates seamlessly with the existing document processing pipeline while providing a foundation for future enhancements and additional file type support.
