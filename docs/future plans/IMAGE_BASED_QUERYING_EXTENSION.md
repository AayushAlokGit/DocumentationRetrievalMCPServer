# Image-Based Querying Extension Plan

## Overview

This document outlines the implementation plan for extending the Personal Documentation Assistant MCP Server with **Image-Based Querying** capabilities. This enhancement will enable users to search and query documents based on images embedded within markdown files, providing a multimodal search experience.

## Current State Analysis

### What We Have Now

- ✅ **Text-Only Processing**: Current system processes markdown text content only
- ✅ **Markdown Parsing**: Robust frontmatter and content extraction
- ✅ **Vector Search**: Text embeddings with Azure OpenAI
- ✅ **Azure Cognitive Search**: Established search infrastructure
- ✅ **Document Chunking**: Effective text segmentation

### Current Limitations

- ❌ **Image Blindness**: Images in markdown files are ignored or treated as text references
- ❌ **No Visual Context**: Cannot understand or search based on image content
- ❌ **Missing Multimodal Embeddings**: Only text embeddings are generated
- ❌ **Limited Metadata**: Image alt-text and paths not extracted or indexed

## Extension Goals

### Primary Objectives

1. **Image Content Analysis**: Extract and understand visual content from images
2. **Multimodal Search**: Enable search queries that combine text and visual elements
3. **Image Metadata Extraction**: Index image paths, alt-text, and descriptions
4. **Visual Context Enhancement**: Improve document understanding through visual information
5. **Backward Compatibility**: Maintain existing text-only functionality

### Use Cases After Enhancement

- **Visual Documentation Search**: "Find diagrams showing database architecture"
- **UI/UX Reference Queries**: "Show screenshots of login interfaces"
- **Technical Diagram Discovery**: "Locate flowcharts related to authentication process"
- **Code Example Visualization**: "Find images of code snippets for API integration"
- **Comprehensive Context**: "Documents about user workflow with accompanying screenshots"

## 🔑 Key Steps for Image-Based Querying Implementation

### **Step 1: Image Detection & Extraction** 🔍

- **Parse markdown syntax** to find image references (`![alt](path)`, HTML `<img>` tags)
- **Resolve image paths** from relative to absolute file locations
- **Validate image files** and extract basic metadata (format, size, etc.)

### **Step 2: Computer Vision Integration** 🧠

- **Choose vision service**: Azure Computer Vision API or OpenAI Vision API
- **Analyze image content** to generate descriptive text
- **Extract OCR text** from images containing readable text
- **Generate image tags** and confidence scores

### **Step 3: Enhanced Document Processing** 📄

- **Modify document readers** to include image analysis data
- **Create multimodal chunks** that combine text content with image descriptions
- **Preserve image-text relationships** within document sections

### **Step 4: Search Index Enhancement** 🗃️

- **Extend Azure Search schema** with new image-specific fields:
  - `has_images` (boolean filter)
  - `image_descriptions` (searchable text)
  - `image_alt_text` (searchable text)
  - `image_count` (numeric filter)
- **Update upload pipeline** to include image metadata in search documents

### **Step 5: Multimodal Search Tools** 🔎

- **Create enhanced search functions** that query both text and image content
- **Add new MCP tools** for image-aware search capabilities
- **Implement filtering** to search documents with/without images
- **Format results** to show image context alongside text matches

### **Step 6: Configuration & Testing** ⚙️

- **Add environment variables** for vision service credentials
- **Install dependencies** (Pillow, Azure Computer Vision SDK)
- **Test image processing pipeline** with sample documents
- **Validate search accuracy** with multimodal queries

## Implementation Plan

### Phase 1: Image Detection and Extraction

#### 1.1 Enhanced Markdown Processing

```python
# Add to document_utils.py
def extract_image_references(content: str, file_path: Path) -> List[Dict]:
    """
    Extract image references from markdown content.

    Supports:
    - Standard markdown: ![alt](path)
    - HTML img tags: <img src="path" alt="alt">
    - Reference-style: ![alt][ref] with [ref]: path
    """
    images = []

    # Standard markdown images: ![alt](path)
    md_pattern = r'!\[([^\]]*)\]\(([^\)]+)\)'
    for match in re.finditer(md_pattern, content):
        alt_text = match.group(1)
        image_path = match.group(2)
        images.append({
            'type': 'markdown',
            'alt_text': alt_text,
            'path': image_path,
            'raw_reference': match.group(0)
        })

    # HTML img tags
    html_pattern = r'<img[^>]+src=["\']([^"\']+)["\'][^>]*alt=["\']([^"\']*)["\'][^>]*>'
    for match in re.finditer(html_pattern, content):
        image_path = match.group(1)
        alt_text = match.group(2)
        images.append({
            'type': 'html',
            'alt_text': alt_text,
            'path': image_path,
            'raw_reference': match.group(0)
        })

    return images

def resolve_image_paths(images: List[Dict], base_path: Path) -> List[Dict]:
    """Resolve relative image paths to absolute paths."""
    for image in images:
        image_path = image['path']

        # Handle different path types
        if image_path.startswith(('http://', 'https://')):
            image['resolved_path'] = image_path
            image['exists'] = False  # Cannot verify remote images
        else:
            # Resolve relative paths
            resolved = (base_path.parent / image_path).resolve()
            image['resolved_path'] = str(resolved)
            image['exists'] = resolved.exists()

    return images
```

#### 1.2 Image Validation and Processing

```python
def validate_image_file(image_path: str) -> Dict:
    """Validate and extract basic information from image file."""
    try:
        from PIL import Image
        import os

        if not os.path.exists(image_path):
            return {'valid': False, 'error': 'File not found'}

        with Image.open(image_path) as img:
            return {
                'valid': True,
                'format': img.format,
                'size': img.size,
                'mode': img.mode,
                'file_size': os.path.getsize(image_path)
            }
    except Exception as e:
        return {'valid': False, 'error': str(e)}
```

### Phase 2: Computer Vision Integration

#### 2.1 Azure Computer Vision Service

```python
# Add to requirements.txt: azure-cognitiveservices-vision-computervision
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from azure.core.credentials import AzureKeyCredential

class ImageAnalysisService:
    """Service for analyzing image content using Azure Computer Vision."""

    def __init__(self):
        self.endpoint = os.getenv('AZURE_COMPUTER_VISION_ENDPOINT')
        self.key = os.getenv('AZURE_COMPUTER_VISION_KEY')
        self.client = ComputerVisionClient(self.endpoint, AzureKeyCredential(self.key))

    def analyze_image_content(self, image_path: str) -> Dict:
        """Analyze image and extract descriptive content."""
        try:
            with open(image_path, 'rb') as image_stream:
                # Get image description
                description = self.client.describe_image_in_stream(image_stream)

                # Get OCR text if present
                image_stream.seek(0)
                ocr_result = self.client.read_in_stream(image_stream, raw=True)

                # Process results
                captions = [cap.text for cap in description.captions] if description.captions else []
                tags = [tag.name for tag in description.tags] if description.tags else []

                return {
                    'descriptions': captions,
                    'tags': tags,
                    'ocr_text': self._extract_ocr_text(ocr_result),
                    'confidence': description.captions[0].confidence if description.captions else 0
                }

        except Exception as e:
            return {'error': str(e), 'descriptions': [], 'tags': [], 'ocr_text': ''}

    def _extract_ocr_text(self, ocr_result) -> str:
        """Extract text from OCR result."""
        # Implementation for extracting text from Azure OCR response
        # This would involve polling the operation and extracting text lines
        pass
```

#### 2.2 OpenAI Vision API Integration (Alternative)

```python
class OpenAIVisionService:
    """Service for analyzing images using OpenAI Vision API."""

    def __init__(self):
        self.client = self._get_openai_client()

    def analyze_image_content(self, image_path: str) -> Dict:
        """Analyze image using OpenAI Vision API."""
        try:
            import base64

            # Encode image to base64
            with open(image_path, 'rb') as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')

            response = self.client.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Describe this image in detail, including any text, diagrams, UI elements, or technical content visible."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500
            )

            description = response.choices[0].message.content

            return {
                'description': description,
                'source': 'openai-vision'
            }

        except Exception as e:
            return {'error': str(e), 'description': ''}
```

### Phase 3: Enhanced Document Processing

#### 3.1 Multimodal Document Processing

```python
def read_markdown_file_with_images(file_path: Path) -> Optional[Dict]:
    """
    Enhanced markdown file reader with image analysis.

    Returns:
        Dict with content, metadata, and image_data
    """
    try:
        # Read file content (existing functionality)
        content = file_path.read_text(encoding='utf-8')

        if not content.strip():
            return None

        # Extract standard metadata
        metadata = extract_metadata(content, file_path)

        # Extract and analyze images
        image_refs = extract_image_references(content, file_path)
        resolved_images = resolve_image_paths(image_refs, file_path)

        # Analyze image content
        image_analysis_service = get_image_analysis_service()
        image_data = []

        for image in resolved_images:
            if image['exists']:
                analysis = image_analysis_service.analyze_image_content(image['resolved_path'])
                image_data.append({
                    **image,
                    'analysis': analysis
                })

        # Remove frontmatter from content
        post = frontmatter.loads(content)
        clean_content = post.content if post.metadata else content

        return {
            'content': clean_content.strip(),
            'file_path': str(file_path),
            'metadata': metadata,
            'images': image_data
        }

    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None
```

#### 3.2 Enhanced Text Chunking with Image Context

```python
def chunk_text_with_image_context(content: str, images: List[Dict],
                                max_chunk_size: int = 4000) -> List[Dict]:
    """
    Create text chunks enhanced with image context.

    Returns:
        List of chunk dictionaries with text and associated image data
    """
    # Get base text chunks
    text_chunks = simple_chunk_text(content, max_chunk_size)

    enhanced_chunks = []

    for i, chunk in enumerate(text_chunks):
        # Find images referenced in this chunk
        chunk_images = []
        for image in images:
            if image['raw_reference'] in chunk:
                chunk_images.append(image)

        # Create enhanced chunk with image context
        enhanced_content = chunk

        # Add image descriptions to chunk content for better embeddings
        for image in chunk_images:
            if 'analysis' in image and image['analysis'].get('description'):
                enhanced_content += f"\n[IMAGE CONTEXT: {image['analysis']['description']}]"
            elif image['alt_text']:
                enhanced_content += f"\n[IMAGE: {image['alt_text']}]"

        enhanced_chunks.append({
            'content': enhanced_content,
            'original_content': chunk,
            'images': chunk_images,
            'chunk_id': f"chunk_{i}"
        })

    return enhanced_chunks
```

### Phase 4: Search Schema Enhancement

#### 4.1 Updated Azure Search Index

```python
# Enhanced search index fields in create_index.py
additional_fields = [
    SimpleField(
        name="has_images",
        type=SearchFieldDataType.Boolean,
        filterable=True,
        facetable=True
    ),
    SimpleField(
        name="image_count",
        type=SearchFieldDataType.Int32,
        filterable=True,
        sortable=True
    ),
    SearchableField(
        name="image_descriptions",
        type=SearchFieldDataType.String,
        searchable=True,
        retrievable=True
    ),
    SearchableField(
        name="image_alt_text",
        type=SearchFieldDataType.String,
        searchable=True,
        retrievable=True
    ),
    SimpleField(
        name="image_paths",
        type=SearchFieldDataType.Collection(SearchFieldDataType.String),
        retrievable=True,
        filterable=True
    )
]
```

#### 4.2 Enhanced Document Upload

```python
def create_search_document_with_images(chunk_data: Dict, metadata: Dict) -> Dict:
    """Create search document with image data included."""

    # Extract image information
    images = chunk_data.get('images', [])
    image_descriptions = []
    image_alt_texts = []
    image_paths = []

    for image in images:
        if 'analysis' in image:
            analysis = image['analysis']
            if analysis.get('description'):
                image_descriptions.append(analysis['description'])
            if analysis.get('descriptions'):
                image_descriptions.extend(analysis['descriptions'])

        if image.get('alt_text'):
            image_alt_texts.append(image['alt_text'])

        if image.get('path'):
            image_paths.append(image['path'])

    # Create enhanced search document
    return {
        'id': generate_document_id(metadata['file_path'], chunk_data['chunk_id']),
        'content': chunk_data['content'],
        'content_vector': None,  # Will be populated by embedding service
        'file_path': metadata['file_path'],
        'title': metadata['title'],
        'work_item_id': metadata['work_item_id'],
        'tags': metadata['tags'],
        'last_modified': metadata['last_modified'],
        'has_images': len(images) > 0,
        'image_count': len(images),
        'image_descriptions': ' '.join(image_descriptions),
        'image_alt_text': ' '.join(image_alt_texts),
        'image_paths': image_paths
    }
```

### Phase 5: Enhanced Search Capabilities

#### 5.1 Multimodal Search Tools

```python
# Add to search_tools.py
def search_documents_with_images(query: str, include_image_context: bool = True) -> List[Dict]:
    """Enhanced search that considers image content."""

    search_service = get_azure_search_service()

    # Build enhanced search query
    if include_image_context:
        # Search in both text content and image descriptions
        search_fields = ["content", "image_descriptions", "image_alt_text", "title", "tags"]
    else:
        search_fields = ["content", "title", "tags"]

    results = search_service.search(
        search_text=query,
        search_fields=search_fields,
        include_total_count=True,
        top=10
    )

    return format_multimodal_results(results)

def search_by_image_content(query: str) -> List[Dict]:
    """Search specifically in image descriptions and alt-text."""

    search_service = get_azure_search_service()

    results = search_service.search(
        search_text=query,
        search_fields=["image_descriptions", "image_alt_text"],
        filter="has_images eq true",
        include_total_count=True,
        top=10
    )

    return format_image_focused_results(results)
```

#### 5.2 MCP Tools Enhancement

```python
# Add new MCP tools for image-based search
{
    "name": "search_documents_with_images",
    "description": "Search across document text and image content",
    "inputSchema": {
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "include_images": {"type": "boolean", "default": True}
        },
        "required": ["query"]
    }
},
{
    "name": "find_documents_with_images",
    "description": "Find documents that contain images matching description",
    "inputSchema": {
        "type": "object",
        "properties": {
            "image_description": {"type": "string"},
            "min_images": {"type": "integer", "default": 1}
        },
        "required": ["image_description"]
    }
}
```

## Configuration Requirements

### Environment Variables

```env
# New environment variables for image processing
AZURE_COMPUTER_VISION_ENDPOINT=https://your-cv-service.cognitiveservices.azure.com/
AZURE_COMPUTER_VISION_KEY=your-cv-key

# Or alternatively for OpenAI Vision
OPENAI_VISION_MODEL=gpt-4-vision-preview

# Image processing settings
MAX_IMAGE_SIZE_MB=10
SUPPORTED_IMAGE_FORMATS=jpg,jpeg,png,gif,bmp,tiff
ENABLE_OCR=true
```

### Dependencies

```txt
# Add to requirements.txt
azure-cognitiveservices-vision-computervision>=0.9.0
Pillow>=9.0.0
```

## Implementation Phases

### Phase 1: Foundation Layer

- Image detection and extraction from markdown syntax
- Basic metadata collection and path resolution
- File validation and format support

### Phase 2: Computer Vision Integration

- Azure Computer Vision or OpenAI Vision API integration
- Image content analysis and description generation
- OCR text extraction capabilities

### Phase 3: Enhanced Document Processing

- Multimodal document reading with image context
- Enhanced chunking strategies that preserve image-text relationships
- Comprehensive metadata extraction

### Phase 4: Search Infrastructure Enhancement

- Extended search index schema for image metadata
- Enhanced document upload pipeline
- Multimodal embedding strategies

### Phase 5: User Interface and Tools

- New MCP search tools for image-based queries
- Enhanced search result formatting
- Integration testing and optimization

## Technology Stack

### Core Technologies

- **Python Libraries**: Pillow (image processing), regex (content parsing)
- **Azure Computer Vision**: Image analysis, OCR, object detection
- **OpenAI Vision API**: Alternative vision analysis with GPT-4V
- **Azure Cognitive Search**: Enhanced schema with image metadata fields

### Integration Points

- **Document Processing Pipeline**: Extended markdown parsing
- **Embedding Generation**: Multimodal content embedding
- **Search Infrastructure**: Enhanced indexing and querying
- **MCP Protocol**: New tools for image-aware search

## Validation Strategy

### Technical Validation

- Image format compatibility testing
- Vision API integration verification
- Search performance with multimodal content

### User Experience Validation

- Search result quality assessment
- Multimodal query effectiveness
- Integration with existing workflows

## Benefits After Implementation

1. **Enhanced Search Accuracy**: Visual context improves search relevance
2. **Multimodal Understanding**: Better comprehension of technical documentation
3. **Comprehensive Indexing**: No information left behind in visual content
4. **Better User Experience**: More intuitive and complete search results
5. **Future-Proof Architecture**: Foundation for additional multimedia support

## Future Extensions

- **Video Content Analysis**: Extend to video files in documentation
- **Audio Processing**: Handle embedded audio content
- **Interactive Diagrams**: Support for SVG and interactive content
- **Image Similarity Search**: Find visually similar images
- **Custom Vision Models**: Train domain-specific image understanding

---

**Status**: Conceptual Planning  
**Priority**: Future Enhancement  
**Dependencies**: Stable core system, Azure/OpenAI service access  
**Complexity**: Medium (depends on chosen vision service integration)
