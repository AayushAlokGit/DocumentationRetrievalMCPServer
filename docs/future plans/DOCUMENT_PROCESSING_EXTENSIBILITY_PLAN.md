# Document Processing Pipeline Extensibility Plan

## Executive Summary

**The Core Mission**: Take any document and generate **context-relevant metadata** that feeds into the **generic Azure Search index schema**. This makes **metadata extraction extensibility the most critical architectural component**.

### Why This Matters

The pipeline's success depends entirely on its ability to:

1. **Understand Context**: Different use cases (Work Items, Projects, Academic) need different metadata
2. **Generate Quality Metadata**: Better metadata = better search results = better user experience
3. **Map to Fixed Schema**: All metadata must fit into Azure Search's predefined fields
4. **Remain Extensible**: Easy to add new contexts without rewriting the pipeline

**Document reading is secondary** - it's just about getting the raw content. **Metadata extraction is primary** - it's about making that content searchable and relevant for the specific use case.

After analyzing the current document processing pipeline implementation in `src/document_upload/processing_strategies.py`, I've identified key areas where extensibility can be enhanced while maintaining the existing architecture. The current code already follows good design patterns with abstract base classes, but there are specific opportunities to improve the extensibility of document reading and metadata extraction components.

## Current Architecture Analysis

### Strengths

- ✅ **Strategy Pattern**: Uses `DocumentProcessingStrategy` abstract base class
- ✅ **Separation of Concerns**: Clear separation between discovery, processing, and upload phases
- ✅ **Modular Design**: Individual methods for different processing steps
- ✅ **Type Safety**: Proper dataclasses and type hints

### Areas for Improvement

- 🔧 **Document Reading**: Currently hardcoded in `_read_document_file()` function
- 🔧 **Metadata Extraction**: File-type specific logic scattered across methods
- 🔧 **File Type Detection**: Simple mapping that could be more extensible
- 🔧 **Content Processing**: Different file types need specialized handling

## Core Architectural Principle

**The Primary Goal of document processing**: Take a document and generate **relevant metadata** for the **context** in which the pipeline is being used. This metadata then feeds into the **generic Azure Search index schema**.

### The document processing Flow

```
Document → Context-Aware Metadata Extraction → Azure Search Index Schema
```

**This makes metadata extraction extensibility the MOST CRITICAL component.**

### Why Metadata Extraction is the Priority

1. **🎯 Context Adaptation**: Different use cases need different metadata interpretation
2. **📊 Search Index Mapping**: All metadata must map to the fixed Azure Search schema
3. **🔍 Search Quality**: Better metadata = better search results and relevance
4. **🚀 Use Case Flexibility**: Same pipeline, different metadata strategies
5. **📈 Business Value**: Metadata quality directly impacts user search experience

### Azure Search Index Schema Constraints

The pipeline must generate metadata that fits into these fixed fields:

```python
AZURE_SEARCH_INDEX_FIELDS = {
    'id', 'content', 'content_vector', 'file_path', 'file_name', 'file_type',
    'title', 'tags', 'category', 'context_name', 'last_modified',
    'chunk_index', 'metadata_json'
}
```

**The extensibility challenge**: How do we extract **context-specific metadata** and map it to these **generic fields** effectively?

## Key Insight: Context Dependency Problem

**Critical Issue Identified**: The original metadata extraction approach had a fundamental flaw - even with extensible `MetadataExtractor` interfaces, the metadata extraction logic was still **context-dependent**.

### The Problem

Different **usage contexts** require fundamentally different metadata interpretation:

| Context Type   | Directory Structure         | Key Metadata             | Tags Focus                     |
| -------------- | --------------------------- | ------------------------ | ------------------------------ |
| **Work Items** | `/Bug 12345/notes.md`       | `work_item_id`, `status` | Work item IDs, categories      |
| **Projects**   | `/ProjectX/api/docs.md`     | `project_name`, `module` | Project names, technical terms |
| **Academic**   | `/Research/papers/study.md` | `author`, `publication`  | Authors, citations, topics     |
| **Personal**   | `/2024/travel/notes.md`     | `date`, `location`       | Dates, locations, activities   |

The **same file type** (e.g., Markdown) needs **different metadata extraction** depending on the **context/strategy** it's being processed in.

### The Solution: Two-Layer Architecture

**Layer 1: File-Type Content Extraction** (Context-Independent)

- Extracts **structural content** from files (headings, links, frontmatter)
- **Reusable** across all contexts and strategies
- **No interpretation** - just raw structured data

**Layer 2: Context-Specific Interpretation** (Strategy-Dependent)

- Interprets structural content based on **strategy context**
- **Work Item Strategy**: Interprets directory names as work item IDs
- **Project Strategy**: Interprets directory names as project modules
- **Academic Strategy**: Interprets frontmatter as citation metadata

### Benefits of This Approach

1. **🔧 True Extensibility**: Add new file types without affecting context logic
2. **🎯 Context Independence**: File extraction logic is reusable across strategies
3. **🚀 Strategy Flexibility**: Each strategy interprets content differently
4. **🔒 Separation of Concerns**: File parsing ≠ Context interpretation
5. **📚 Maintainability**: Changes to file formats don't affect context logic
6. **🔄 Composability**: Mix and match content extractors with context interpreters

## Extensibility Plan

## Prioritized Extensibility Plan

**Priority 1: Context-Aware Metadata Extraction** (MOST CRITICAL)
**Priority 2: Azure Search Schema Mapping**
**Priority 3: Document Reading Extensibility**

### Priority 1: Context-Aware Metadata Extraction System (CRITICAL)

**Goal**: Make metadata extraction highly extensible for different use case contexts while ensuring proper mapping to Azure Search schema.

**Implementation**:

````python
# Layer 1: File-Type Content Extraction (Context-Independent)
class ContentExtractor(ABC):
    """Extracts raw structured content from files - NO context interpretation."""

    @abstractmethod
    def can_extract(self, file_type: str) -> bool:
        """Check if this extractor handles the file type."""
        pass

    @abstractmethod
    def extract_content_structure(self, content: str, file_path: Path) -> Dict[str, Any]:
        """Extract raw structured content WITHOUT context interpretation."""
        pass

# Layer 2: Context-Specific Metadata Interpreter (Strategy-Dependent)
class ContextMetadataInterpreter(ABC):
    """Interprets structured content based on strategy context."""

    @abstractmethod
    def interpret_context_for_search(self, structured_content: Dict[str, Any],
                                    file_path: Path) -> Dict[str, Any]:
        """Interpret content based on strategy-specific search context needs."""
        pass

    @abstractmethod
    def map_to_search_schema(self, context_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Map context-specific metadata to Azure Search schema fields."""
        pass

# File-Type Extractors (Context-Independent - Reusable)
class MarkdownContentExtractor(ContentExtractor):
    def can_extract(self, file_type: str) -> bool:
        return file_type == 'markdown'

    def extract_content_structure(self, content: str, file_path: Path) -> Dict[str, Any]:
        """Extract markdown structure without interpreting context meaning."""
        import frontmatter
        import re

        # Extract frontmatter
        try:
            post = frontmatter.loads(content)
            frontmatter_data = dict(post.metadata) if post.metadata else {}
            clean_content = post.content if post.metadata else content
        except:
            frontmatter_data = {}
            clean_content = content

        # Extract headings
        headings = re.findall(r'^#+\s+(.+)$', clean_content, re.MULTILINE)

        # Extract links
        links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', clean_content)

        # Extract code blocks and languages
        code_blocks = re.findall(r'```(\w*)\n([\s\S]*?)\n```', clean_content)

        return {
            'frontmatter': frontmatter_data,
            'headings': headings,
            'links': links,
            'code_blocks': code_blocks,
            'clean_content': clean_content,
            'has_code_blocks': '```' in clean_content,
            'word_count': len(clean_content.split()),
            'paragraph_count': len(clean_content.split('\n\n'))
        }

class DocxContentExtractor(ContentExtractor):
    def can_extract(self, file_type: str) -> bool:
        return file_type == 'document'

    def extract_content_structure(self, content: str, file_path: Path) -> Dict[str, Any]:
        """Extract DOCX structure without interpreting context meaning."""
        import re

        # Parse the already-extracted content from DOCX reader
        headings = re.findall(r'^#+\s+(.+)$', content, re.MULTILINE)

        return {
            'headings': headings,
            'has_formatting': '#' in content,  # Indicates preserved formatting
            'paragraph_count': len(content.split('\n\n')),
            'word_count': len(content.split()),
            'clean_content': content
        }

# Context Interpreters (Strategy-Dependent - THE CRITICAL PART)
class WorkItemContextInterpreter(ContextMetadataInterpreter):
    """Interprets content for work item-focused contexts."""

    def interpret_context_for_search(self, structured_content: Dict[str, Any],
                                    file_path: Path) -> Dict[str, Any]:
        """Extract work item-specific metadata from structured content."""
        metadata = {}

        # Work item-specific interpretation
        work_item_id = self._extract_work_item_from_path(file_path)
        metadata['work_item_id'] = work_item_id
        metadata['work_item_type'] = self._classify_work_item_type(work_item_id)

        # Title extraction with work item focus
        metadata['document_title'] = self._extract_work_item_title(structured_content, file_path)

        # Tags with work item emphasis
        tags = {work_item_id.lower()}
        tags.update(self._extract_work_item_tags(structured_content))
        metadata['document_tags'] = sorted(list(tags))

        # Category based on work item type and content
        metadata['document_category'] = self._determine_work_item_category(
            structured_content, work_item_id
        )

        return metadata

    def map_to_search_schema(self, context_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Map work item metadata to Azure Search schema."""
        return {
            'title': context_metadata.get('document_title', 'Untitled'),
            'tags': ', '.join(context_metadata.get('document_tags', [])),
            'category': context_metadata.get('document_category', 'work-item'),
            'context_name': context_metadata.get('work_item_id', 'unknown'),
            # Store additional work item data in metadata_json
            'metadata_json': json.dumps({
                'work_item_type': context_metadata.get('work_item_type'),
                'work_item_id': context_metadata.get('work_item_id'),
                'extraction_strategy': 'work_item'
            })
        }

    def _extract_work_item_from_path(self, file_path: Path) -> str:
        """Extract work item ID from directory structure."""
        return file_path.parent.name

    def _classify_work_item_type(self, work_item_id: str) -> str:
        """Classify work item type from ID pattern."""
        if work_item_id.lower().startswith('bug'):
            return 'bug'
        elif work_item_id.lower().startswith('task'):
            return 'task'
        elif work_item_id.lower().startswith('feature'):
            return 'feature'
        else:
            return 'unknown'

    def _extract_work_item_title(self, structured_content: Dict, file_path: Path) -> str:
        """Extract title with work item context in mind."""
        # Priority: frontmatter title -> first heading -> filename
        if structured_content.get('frontmatter', {}).get('title'):
            return structured_content['frontmatter']['title']
        elif structured_content.get('headings'):
            return structured_content['headings'][0]
        else:
            return file_path.stem.replace('_', ' ').replace('-', ' ').title()

    def _extract_work_item_tags(self, structured_content: Dict) -> set:
        """Extract work item-specific tags."""
        tags = set()

        # Add filename as tag
        if 'clean_content' in structured_content:
            # Extract technical terms, API names, etc.
            content = structured_content['clean_content'].lower()
            if 'api' in content:
                tags.add('api')
            if 'database' in content or 'db' in content:
                tags.add('database')
            if any(lang in content for lang in ['python', 'javascript', 'sql']):
                tags.add('code')

        # Add tags based on code blocks
        if structured_content.get('has_code_blocks'):
            tags.add('technical')
            # Extract programming languages from code blocks
            for lang, _ in structured_content.get('code_blocks', []):
                if lang:
                    tags.add(f'lang-{lang}')

        return tags

    def _determine_work_item_category(self, structured_content: Dict, work_item_id: str) -> str:
        """Determine category based on work item type and content."""
        work_item_type = self._classify_work_item_type(work_item_id)

        if structured_content.get('has_code_blocks'):
            return f'{work_item_type}-technical'
        elif len(structured_content.get('headings', [])) > 3:
            return f'{work_item_type}-documentation'
        else:
            return f'{work_item_type}-notes'

class ProjectContextInterpreter(ContextMetadataInterpreter):
    """Interprets content for project-focused contexts."""

    def interpret_context_for_search(self, structured_content: Dict[str, Any],
                                    file_path: Path) -> Dict[str, Any]:
        metadata = {}

        # Project-specific interpretation
        project_info = self._extract_project_info(file_path)
        metadata['project_name'] = project_info['name']
        metadata['project_module'] = project_info['module']

        # Different tagging strategy for projects
        tags = {project_info['name'].lower()}
        if structured_content.get('has_code_blocks'):
            tags.add('technical')
            tags.add('code')

        # Extract programming languages and frameworks
        tags.update(self._extract_tech_stack_tags(structured_content))

        metadata['document_tags'] = sorted(list(tags))
        metadata['document_category'] = self._determine_project_category(structured_content)

        return metadata

    def map_to_search_schema(self, context_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Map project metadata to Azure Search schema."""
        return {
            'title': context_metadata.get('document_title', 'Untitled'),
            'tags': ', '.join(context_metadata.get('document_tags', [])),
            'category': context_metadata.get('document_category', 'project'),
            'context_name': context_metadata.get('project_name', 'unknown'),
            'metadata_json': json.dumps({
                'project_name': context_metadata.get('project_name'),
                'project_module': context_metadata.get('project_module'),
                'extraction_strategy': 'project'
            })
        }

    def _extract_project_info(self, file_path: Path) -> Dict[str, str]:
        """Extract project name and module from path structure."""
        parts = file_path.parts
        return {
            'name': parts[-3] if len(parts) > 2 else parts[-2],  # Project name
            'module': parts[-2] if len(parts) > 2 else 'main'    # Module/component
        }

    def _extract_tech_stack_tags(self, structured_content: Dict) -> set:
        """Extract technology stack tags from content."""
        tags = set()
        content = structured_content.get('clean_content', '').lower()

        # Programming languages
        languages = {
            'python': ['python', 'py', 'django', 'flask'],
            'javascript': ['javascript', 'js', 'node', 'react', 'vue'],
            'java': ['java', 'spring', 'hibernate'],
            'csharp': ['c#', 'csharp', '.net', 'asp.net']
        }

        for lang, keywords in languages.items():
            if any(keyword in content for keyword in keywords):
                tags.add(lang)

        # Frameworks and tools
        if any(keyword in content for keyword in ['docker', 'kubernetes', 'k8s']):
            tags.add('containerization')
        if any(keyword in content for keyword in ['api', 'rest', 'graphql']):
            tags.add('api')
        if any(keyword in content for keyword in ['database', 'sql', 'mongodb']):
            tags.add('database')

        return tags

    def _determine_project_category(self, structured_content: Dict) -> str:
        """Determine category based on project content."""
        if structured_content.get('has_code_blocks'):
            return 'project-technical'
        elif 'api' in structured_content.get('clean_content', '').lower():
            return 'project-api'
        elif len(structured_content.get('headings', [])) > 5:
            return 'project-documentation'
        else:
            return 'project-notes'
````

### Priority 2: Document Reading Extensibility

**Goal**: Make document reading extensible for new file types without modifying core pipeline code.

**Implementation**:

```python
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Dict, Any

class DocumentReader(ABC):
    """Abstract interface for reading different document types."""

    @abstractmethod
    def can_read(self, file_path: Path) -> bool:
        """Check if this reader can handle the given file type."""
        pass

    @abstractmethod
    def read_document(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Read document content and return structured data."""
        pass

    @abstractmethod
    def get_supported_extensions(self) -> List[str]:
        """Return list of supported file extensions."""
        pass

# Concrete implementations
class MarkdownDocumentReader(DocumentReader):
    def can_read(self, file_path: Path) -> bool:
        return file_path.suffix.lower() == '.md'

    def read_document(self, file_path: Path) -> Optional[Dict[str, Any]]:
        # Markdown-specific reading logic
        pass

    def get_supported_extensions(self) -> List[str]:
        return ['.md']

class DocxDocumentReader(DocumentReader):
    def can_read(self, file_path: Path) -> bool:
        return file_path.suffix.lower() == '.docx'

    def read_document(self, file_path: Path) -> Optional[Dict[str, Any]]:
        # DOCX-specific reading logic with structure preservation
        pass

    def get_supported_extensions(self) -> List[str]:
        return ['.docx']
```

### 2. Document Reader Registry

**Goal**: Central registry for managing document readers with automatic discovery.

**Implementation**:

```python
class DocumentReaderRegistry:
    """Registry for managing document readers."""

    def __init__(self):
        self._readers: List[DocumentReader] = []
        self._register_default_readers()

    def register_reader(self, reader: DocumentReader) -> None:
        """Register a new document reader."""
        self._readers.append(reader)

    def get_reader(self, file_path: Path) -> Optional[DocumentReader]:
        """Get appropriate reader for file type."""
        for reader in self._readers:
            if reader.can_read(file_path):
                return reader
        return None

    def get_supported_extensions(self) -> List[str]:
        """Get all supported file extensions."""
        extensions = []
        for reader in self._readers:
            extensions.extend(reader.get_supported_extensions())
        return list(set(extensions))

    def _register_default_readers(self):
        """Register default readers for common file types."""
        self.register_reader(MarkdownDocumentReader())
        self.register_reader(TextDocumentReader())
        self.register_reader(DocxDocumentReader())
```

### 3. Context-Aware Metadata Extraction System

**Issue Identified**: You're absolutely right! Even with a `MetadataExtractor` interface, the metadata extraction logic is still **context-dependent**. Different contexts (Work Items, Projects, Categories) need fundamentally different extraction approaches.

**Goal**: Separate **file-type specific extraction** from **context-specific interpretation**.

**Two-Layer Architecture**:

````python
# Layer 1: File-Type Specific Content Extraction (Context-Independent)
class ContentExtractor(ABC):
    """Extracts raw structured content from files - NO context interpretation."""

    @abstractmethod
    def can_extract(self, file_type: str) -> bool:
        """Check if this extractor handles the file type."""
        pass

    @abstractmethod
    def extract_content_structure(self, content: str, file_path: Path) -> Dict[str, Any]:
        """Extract raw structured content WITHOUT context interpretation."""
        pass

# Layer 2: Context-Specific Metadata Interpretation (Strategy-Dependent)
class ContextMetadataInterpreter(ABC):
    """Interprets structured content based on strategy context."""

    @abstractmethod
    def interpret_for_context(self, structured_content: Dict[str, Any],
                             file_path: Path) -> Dict[str, Any]:
        """Interpret content based on strategy-specific context needs."""
        pass

# File-Type Extractors (Context-Independent)
class MarkdownContentExtractor(ContentExtractor):
    def can_extract(self, file_type: str) -> bool:
        return file_type == 'markdown'

    def extract_content_structure(self, content: str, file_path: Path) -> Dict[str, Any]:
        """Extract markdown structure without interpreting context meaning."""
        import frontmatter

        # Extract frontmatter
        try:
            post = frontmatter.loads(content)
            frontmatter_data = dict(post.metadata) if post.metadata else {}
            clean_content = post.content if post.metadata else content
        except:
            frontmatter_data = {}
            clean_content = content

        # Extract headings
        headings = re.findall(r'^#+\s+(.+)$', clean_content, re.MULTILINE)

        # Extract links
        links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', clean_content)

        return {
            'frontmatter': frontmatter_data,
            'headings': headings,
            'links': links,
            'clean_content': clean_content,
            'has_code_blocks': '```' in clean_content,
            'word_count': len(clean_content.split())
        }

class DocxContentExtractor(ContentExtractor):
    def can_extract(self, file_type: str) -> bool:
        return file_type == 'document'

    def extract_content_structure(self, content: str, file_path: Path) -> Dict[str, Any]:
        """Extract DOCX structure without interpreting context meaning."""
        # Parse the already-extracted content from DOCX reader
        headings = re.findall(r'^#+\s+(.+)$', content, re.MULTILINE)

        return {
            'headings': headings,
            'has_formatting': '#' in content,  # Indicates preserved formatting
            'paragraph_count': len(content.split('\n\n')),
            'word_count': len(content.split())
        }

# Context Interpreters (Strategy-Dependent)
class WorkItemContextInterpreter(ContextMetadataInterpreter):
    """Interprets content for work item-focused contexts."""

    def interpret_context_for_search(self, structured_content: Dict[str, Any],
                                    file_path: Path) -> Dict[str, Any]:
        metadata = {}

        # Work item-specific interpretation
        work_item_id = self._extract_work_item_from_path(file_path)
        metadata['work_item_id'] = work_item_id
        metadata['context_name'] = work_item_id

        # Title extraction with work item focus
        metadata['title'] = self._extract_work_item_title(structured_content, file_path)

        # Tags with work item emphasis
        tags = {work_item_id.lower()}
        tags.update(self._extract_work_item_tags(structured_content))
        metadata['tags'] = sorted(list(tags))

        return metadata

    def _extract_work_item_from_path(self, file_path: Path) -> str:
        """Extract work item ID from directory structure."""
        return file_path.parent.name

    def _extract_work_item_title(self, structured_content: Dict, file_path: Path) -> str:
        """Extract title with work item context in mind."""
        # Priority: frontmatter title -> first heading -> filename
        if 'frontmatter' in structured_content and 'title' in structured_content['frontmatter']:
            return structured_content['frontmatter']['title']
        elif structured_content.get('headings'):
            return structured_content['headings'][0]
        else:
            return file_path.stem.replace('_', ' ').replace('-', ' ').title()

class ProjectContextInterpreter(ContextMetadataInterpreter):
    """Interprets content for project-focused contexts."""

    def interpret_context_for_search(self, structured_content: Dict[str, Any],
                                    file_path: Path) -> Dict[str, Any]:
        metadata = {}

        # Project-specific interpretation
        project_name = self._extract_project_from_path(file_path)
        metadata['project_name'] = project_name
        metadata['context_name'] = project_name

        # Different tagging strategy for projects
        tags = {project_name.lower()}
        if structured_content.get('has_code_blocks'):
            tags.add('technical')
        metadata['tags'] = sorted(list(tags))

        return metadata

    def _extract_project_from_path(self, file_path: Path) -> str:
        """Extract project name from path structure."""
        # Could be top-level directory or specific project folder
        return file_path.parts[-2] if len(file_path.parts) > 1 else file_path.parent.name
````

### 4. Enhanced Processing Strategy with Two-Layer Architecture

**Goal**: Separate file-type extraction from context interpretation in the base strategy.

**Implementation**:

```python
class DocumentProcessingStrategy(ABC):
    """Enhanced base class with two-layer metadata extraction."""

    def __init__(self):
        self.document_reader_registry = DocumentReaderRegistry()
        self.content_extractors: List[ContentExtractor] = []
        self.context_interpreter: ContextMetadataInterpreter = None
        self._register_default_extractors()
        self._initialize_context_interpreter()

    def register_content_extractor(self, extractor: ContentExtractor) -> None:
        """Register a file-type content extractor."""
        self.content_extractors.append(extractor)

    @abstractmethod
    def _initialize_context_interpreter(self) -> None:
        """Initialize the strategy-specific context interpreter."""
        pass

    def read_document(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Read document using appropriate reader."""
        reader = self.document_reader_registry.get_reader(file_path)
        if not reader:
            print(f"Warning: No reader available for {file_path}")
            return None
        return reader.read_document(file_path)

    def extract_metadata(self, content: str, file_path: Path) -> Dict:
        """Two-layer metadata extraction: Content → Context."""
        try:
            # Step 1: File-type specific content extraction (context-independent)
            file_extension = file_path.suffix.lower()
            file_type = self._get_file_type(file_extension)

            structured_content = self._extract_structured_content(content, file_path, file_type)

            # Step 2: Context-specific interpretation (strategy-dependent)
            context_metadata = {}
            if self.context_interpreter:
                context_metadata = self.context_interpreter.interpret_context_for_search(
                    structured_content, file_path
                )

            # Step 3: Combine base metadata with extracted information
            base_metadata = {
                'file_type': file_type,
                'file_path': str(file_path),
                'file_name': file_path.name,
                'last_modified': self._get_last_modified(file_path)
            }

            # Merge all metadata layers
            base_metadata.update(structured_content)
            base_metadata.update(context_metadata)

            return base_metadata

        except Exception as e:
            return self._get_error_metadata(file_path, str(e))

    def _extract_structured_content(self, content: str, file_path: Path, file_type: str) -> Dict[str, Any]:
        """Extract structured content using appropriate content extractor."""
        for extractor in self.content_extractors:
            if extractor.can_extract(file_type):
                try:
                    return extractor.extract_content_structure(content, file_path)
                except Exception as e:
                    print(f"Warning: Content extractor {type(extractor).__name__} failed: {e}")

        # Fallback to basic content structure
        return {
            'clean_content': content,
            'word_count': len(content.split()),
            'has_content': bool(content.strip())
        }

    def _register_default_extractors(self):
        """Register default content extractors for common file types."""
        self.register_content_extractor(MarkdownContentExtractor())
        self.register_content_extractor(DocxContentExtractor())
        self.register_content_extractor(TextContentExtractor())

    @abstractmethod
    def _get_file_type(self, file_extension: str) -> str:
        """Map file extension to file type."""
        pass

    def _get_last_modified(self, file_path: Path) -> str:
        """Get file last modified timestamp."""
        file_stat = file_path.stat()
        last_modified_dt = datetime.fromtimestamp(file_stat.st_mtime)
        return last_modified_dt.isoformat() + 'Z'

    def _get_error_metadata(self, file_path: Path, error_message: str) -> Dict:
        """Return minimal metadata when extraction fails."""
        return {
            'file_type': 'unknown',
            'title': file_path.stem,
            'tags': [file_path.parent.name, 'error'],
            'context_name': file_path.parent.name,
            'last_modified': datetime.now().isoformat() + 'Z',
            'extraction_error': error_message
        }

# Concrete Strategy Implementation
class PersonalDocumentationAssistantProcessingStrategy(DocumentProcessingStrategy):
    """Work item-focused processing strategy."""

    def _initialize_context_interpreter(self) -> None:
        """Initialize work item context interpreter."""
        self.context_interpreter = WorkItemContextInterpreter()

    def _get_file_type(self, file_extension: str) -> str:
        """Map file extension to file type."""
        type_mapping = {
            '.md': 'markdown',
            '.txt': 'text',
            '.docx': 'document'
        }
        return type_mapping.get(file_extension, 'unknown')

class ProjectDocumentationProcessingStrategy(DocumentProcessingStrategy):
    """Project-focused processing strategy."""

    def _initialize_context_interpreter(self) -> None:
        """Initialize project context interpreter."""
        self.context_interpreter = ProjectContextInterpreter()

    def _get_file_type(self, file_extension: str) -> str:
        """Map file extension to file type."""
        type_mapping = {
            '.md': 'markdown',
            '.txt': 'text',
            '.docx': 'document',
            '.py': 'code',
            '.js': 'code'
        }
        return type_mapping.get(file_extension, 'unknown')
```

### 5. File Type Detection Enhancement

**Goal**: Make file type detection extensible and configurable.

**Implementation**:

```python
class FileTypeDetector:
    """Extensible file type detection."""

    def __init__(self):
        self.type_mappings = {
            '.md': 'markdown',
            '.txt': 'text',
            '.docx': 'document',
            '.pdf': 'pdf',
            '.html': 'html',
            '.json': 'json',
            '.xml': 'xml'
        }
        self.content_detectors: List[ContentBasedDetector] = []

    def register_content_detector(self, detector: 'ContentBasedDetector'):
        """Register a content-based file type detector."""
        self.content_detectors.append(detector)

    def get_file_type(self, file_path: Path, content: Optional[str] = None) -> str:
        """Detect file type using extension and optionally content."""
        # First try extension-based detection
        extension_type = self.type_mappings.get(file_path.suffix.lower())
        if extension_type:
            return extension_type

        # If content is available, try content-based detection
        if content:
            for detector in self.content_detectors:
                detected_type = detector.detect_from_content(content, file_path)
                if detected_type:
                    return detected_type

        return 'unknown'

    def register_file_type(self, extension: str, file_type: str):
        """Register a new file type mapping."""
        self.type_mappings[extension] = file_type

class ContentBasedDetector(ABC):
    """Abstract base for content-based file type detection."""

    @abstractmethod
    def detect_from_content(self, content: str, file_path: Path) -> Optional[str]:
        """Detect file type from content."""
        pass
```

## Implementation Strategy (Prioritized for Metadata Extraction)

### Phase 1: Context-Aware Metadata Foundation (Week 1) - CRITICAL

1. **Create ContentExtractor Interfaces**: Implement file-type specific content extraction
2. **Create ContextMetadataInterpreter Interfaces**: Implement strategy-specific interpretation
3. **Implement WorkItem and Project Interpreters**: Core business logic for metadata interpretation
4. **Azure Search Schema Mapping**: Ensure all metadata maps correctly to search fields

### Phase 2: Metadata Migration (Week 2) - HIGH PRIORITY

1. **Migrate Current PersonalDocumentationAssistant**: Convert to new two-layer system
2. **Test Metadata Quality**: Validate that extracted metadata improves search results
3. **Schema Mapping Validation**: Ensure all context metadata fits Azure Search schema
4. **Performance Testing**: Confirm metadata extraction doesn't slow down pipeline

### Phase 3: Document Reading Enhancement (Week 3) - MEDIUM PRIORITY

1. **Migrate Document Readers**: Convert current reading logic to extensible readers
2. **Add New File Types**: Implement readers for PDF, HTML, JSON, XML as needed
3. **Reader Registry System**: Implement automatic reader discovery and registration

### Phase 4: Complete Integration & Testing (Week 4) - VALIDATION

1. **End-to-End Testing**: Test complete document → metadata → search index flow
2. **Context Strategy Testing**: Validate multiple context strategies work correctly
3. **Search Quality Validation**: Confirm metadata improvements enhance search results
4. **Documentation & Examples**: Document how to add new context strategies

## Key Success Metrics

1. **Metadata Quality**: Better titles, tags, and context_name extraction
2. **Search Relevance**: Improved search results due to better metadata
3. **Context Flexibility**: Easy to add new context strategies (Academic, Personal, etc.)
4. **Azure Schema Compliance**: All metadata correctly maps to search index fields
5. **Performance**: No significant slowdown in document processing pipeline

## Extension Examples

### Adding PDF Support

```python
class PdfDocumentReader(DocumentReader):
    def can_read(self, file_path: Path) -> bool:
        return file_path.suffix.lower() == '.pdf'

    def read_document(self, file_path: Path) -> Optional[Dict[str, Any]]:
        try:
            import PyPDF2
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                content = []
                for page in reader.pages:
                    content.append(page.extract_text())
                return {
                    'content': '\n\n'.join(content),
                    'file_path': str(file_path),
                    'page_count': len(reader.pages)
                }
        except Exception as e:
            print(f"Error reading PDF {file_path}: {e}")
            return None

    def get_supported_extensions(self) -> List[str]:
        return ['.pdf']

# Register the new reader
strategy.document_reader_registry.register_reader(PdfDocumentReader())
```

### Adding Custom Metadata Extractor

````python
class TechnicalDocumentExtractor(MetadataExtractor):
    def can_extract(self, file_type: str, content: str) -> bool:
        # Extract from any text that contains code or technical terms
        technical_keywords = ['API', 'function', 'class', 'import', 'def ', 'const ']
        return any(keyword in content for keyword in technical_keywords)

    def extract_metadata(self, content: str, file_path: Path,
                        base_metadata: Dict) -> Dict[str, Any]:
        metadata = {}

        # Extract code blocks
        code_blocks = re.findall(r'```[\s\S]*?```', content)
        if code_blocks:
            metadata['has_code'] = True
            metadata['code_block_count'] = len(code_blocks)

        # Extract programming languages
        languages = re.findall(r'```(\w+)', content)
        if languages:
            metadata['programming_languages'] = list(set(languages))

        # Add technical category
        metadata['category'] = 'technical'

        return metadata

    def get_priority(self) -> int:
        return 50  # Medium priority

# Register the new extractor
strategy.register_metadata_extractor(TechnicalDocumentExtractor())
````

## Benefits of This Approach

1. **🔧 Extensible**: Easy to add new file types without modifying core code
2. **🎯 Maintainable**: Clear separation of concerns and single responsibility
3. **🚀 Performant**: Registry pattern enables efficient lookups
4. **🔒 Type Safe**: Proper abstractions with type hints
5. **📚 Testable**: Each component can be tested independently
6. **🔄 Backward Compatible**: Existing functionality remains unchanged
7. **📈 Scalable**: Can handle growing number of file types and extraction strategies

## Configuration and Usage

### Simple Extension Example

```python
# In your processing strategy
class MyCustomProcessingStrategy(DocumentProcessingStrategy):
    def _register_default_extractors(self):
        # Register strategy-specific extractors
        self.register_metadata_extractor(WorkItemExtractor())
        self.register_metadata_extractor(TechnicalDocumentExtractor())
        self.register_metadata_extractor(ProjectMetadataExtractor())

    def __init__(self):
        super().__init__()
        # Register custom document readers
        self.document_reader_registry.register_reader(CustomFileReader())
```

This extensibility plan maintains the existing architecture while making it significantly more extensible and maintainable. The strategy pattern is preserved, but the internal components become pluggable and reusable across different strategies.
