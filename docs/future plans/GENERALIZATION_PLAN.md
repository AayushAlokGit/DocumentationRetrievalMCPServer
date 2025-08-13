# Personal Knowledge Assistant Generalization Plan

## Overview

This document outlines a comprehensive plan to transform the current Work Item Documentation Retriever into a **Generic Personal Knowledge Assistant MCP Server** that can handle any type of document collection, not just work items.

## Current State Analysis

### What Works Well

- ✅ **Core Architecture**: MCP server structure with Azure Cognitive Search
- ✅ **Search Capabilities**: Text, vector, and hybrid search functionality
- ✅ **Document Processing**: Markdown parsing, chunking, and embedding generation
- ✅ **Tool Interface**: Well-structured MCP tools for search and information retrieval

### Current Limitations

- ❌ **Hard-coded Work Item Logic**: Directory naming assumes work item IDs
- ❌ **Schema Dependencies**: Search index schema tied to work item structure
- ❌ **Upload Process**: Assumes specific folder structure (work item folders)
- ❌ **Tool Names**: Tools are named specifically for work items
- ❌ **Configuration**: Environment variables and paths are work item specific

## Generalization Goals

### Primary Objectives

1. **Universal Document Support**: Handle any structured document collection
2. **Flexible Organization**: Support multiple organizational schemes (folders, tags, categories)
3. **Configurable Schema**: Allow customizable document metadata
4. **Generic Upload Process**: Support various document sources and structures
5. **Extensible Tool Set**: Provide generic search and retrieval tools

### Use Cases After Generalization

- **Technical Documentation**: API docs, architecture guides, runbooks
- **Research Collections**: Papers, articles, notes, bookmarks
- **Project Documentation**: Requirements, designs, meeting notes
- **Personal Knowledge Base**: Learning notes, reference materials
- **Company Documentation**: Policies, procedures, guidelines
- **Code Documentation**: README files, code comments, wikis

## Implementation Plan

### Phase 1: Core Abstraction Layer

#### 1.1 Document Collection Model

```python
# New abstraction for document collections
class DocumentCollection:
    def __init__(self, name: str, base_path: str, schema: DocumentSchema):
        self.name = name
        self.base_path = base_path
        self.schema = schema
        self.metadata = {}

    def get_categories(self) -> List[str]:
        """Get all document categories/groupings"""

    def get_documents_by_category(self, category: str) -> List[Document]:
        """Get documents in a specific category"""
```

#### 1.2 Generic Document Schema

```python
class DocumentSchema:
    def __init__(self):
        self.required_fields = ["title", "content", "source_path"]
        self.optional_fields = ["category", "tags", "author", "created_date"]
        self.custom_fields = {}

    def add_custom_field(self, name: str, field_type: str, required: bool = False):
        """Add custom metadata field"""
```

#### 1.3 Flexible Document Processor

```python
class GenericDocumentProcessor:
    def __init__(self, collection: DocumentCollection):
        self.collection = collection

    def discover_documents(self) -> List[DocumentInfo]:
        """Discover documents using configurable patterns"""

    def extract_category(self, file_path: str) -> str:
        """Extract category using configurable rules"""

    def process_document(self, doc_info: DocumentInfo) -> ProcessedDocument:
        """Process document with flexible schema"""
```

### Phase 2: Configuration System

#### 2.1 Collection Configuration Files

```yaml
# collection.yaml - Define document collection structure
name: "Personal Knowledge Base"
version: "1.0"
base_path: "/path/to/documents"

# Document discovery rules
discovery:
  patterns:
    - "**/*.md"
    - "**/*.txt"
    - "**/*.pdf"
  exclude_patterns:
    - "**/node_modules/**"
    - "**/.git/**"

# Category extraction rules
categorization:
  strategy: "folder_based" # or "tag_based", "filename_based", "metadata_based"
  folder_depth: 1 # How many folder levels to use for categories

# Custom metadata fields
schema:
  required_fields:
    - title
    - content
    - source_path
    - category
  optional_fields:
    - tags
    - author
    - created_date
    - last_modified
  custom_fields:
    priority: "string"
    status: "string"
    project: "string"

# Upload behavior
upload:
  chunk_size: 1000
  overlap: 200
  embed_title: true
  embed_metadata: true
```

#### 2.2 Environment Configuration

```bash
# Generic environment variables
KNOWLEDGE_BASE_NAME=personal-knowledge
KNOWLEDGE_BASE_PATH=/path/to/documents
COLLECTION_CONFIG_PATH=/path/to/collection.yaml

# Azure Search (unchanged)
AZURE_SEARCH_ENDPOINT=https://your-search.search.windows.net
AZURE_SEARCH_ADMIN_KEY=your-admin-key
AZURE_SEARCH_INDEX=knowledge-base-index

# OpenAI (unchanged)
OPENAI_API_KEY=your-openai-key
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

### Phase 3: Generic Upload System

#### 3.1 Flexible Document Discovery

```python
class DocumentDiscovery:
    def __init__(self, config: CollectionConfig):
        self.config = config

    def find_documents(self, base_path: str) -> List[DocumentInfo]:
        """Find documents using configurable patterns"""

    def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract metadata using configurable rules"""
        # Support multiple strategies:
        # - Folder structure: /category/subcategory/document.md
        # - YAML frontmatter: category: "API Documentation"
        # - Filename patterns: [API] Authentication Guide.md
        # - Directory metadata: .metadata.yaml files
```

#### 3.2 Generic Upload Scripts

```python
# Replace upload_work_items.py with upload_documents.py
class GenericDocumentUploader:
    def __init__(self, collection_config: CollectionConfig):
        self.config = collection_config
        self.discovery = DocumentDiscovery(collection_config)

    def upload_collection(self, base_path: str):
        """Upload entire document collection"""

    def upload_category(self, category: str):
        """Upload specific category"""

    def upload_document(self, file_path: str):
        """Upload single document"""
```

### Phase 4: Generic MCP Tools

#### 4.1 New Tool Schema Names

```python
# Replace work item specific tools with generic ones
TOOLS = [
    "search_documents",           # Replace: search_work_items
    "search_by_category",         # Replace: search_by_work_item
    "semantic_search",            # Keep as is
    "get_categories",             # Replace: get_work_item_list
    "get_collection_summary",     # Replace: get_work_item_summary
    "get_document_details",       # New: Get specific document info
    "search_by_metadata",         # New: Search by custom metadata
]
```

#### 4.2 Flexible Search Parameters

```python
# Enhanced search tool with flexible filtering
{
    "name": "search_documents",
    "description": "Search document collection using text, vector, or hybrid search",
    "parameters": {
        "query": "Search query",
        "search_type": "text|vector|hybrid",
        "filters": {
            "category": "Filter by category",
            "tags": "Filter by tags",
            "metadata": "Filter by custom metadata fields"
        },
        "max_results": 5
    }
}
```

### Phase 5: Enhanced Features

#### 5.1 Multi-Collection Support

```python
# Support multiple document collections in one instance
class MultiCollectionManager:
    def __init__(self):
        self.collections = {}

    def add_collection(self, name: str, config: CollectionConfig):
        """Add a new document collection"""

    def search_across_collections(self, query: str) -> List[SearchResult]:
        """Search across all collections"""

    def search_collection(self, collection_name: str, query: str) -> List[SearchResult]:
        """Search specific collection"""
```

#### 5.2 Document Relationships

```python
# Support for document linking and relationships
class DocumentGraph:
    def find_related_documents(self, document_id: str) -> List[Document]:
        """Find documents related by content similarity"""

    def find_document_references(self, document_id: str) -> List[Document]:
        """Find documents that reference this one"""
```

#### 5.3 Advanced Metadata Support

```python
# Support for rich metadata and tagging
class MetadataExtractor:
    def extract_from_frontmatter(self, content: str) -> Dict:
        """Extract YAML frontmatter"""

    def extract_from_filename(self, filename: str) -> Dict:
        """Extract metadata from filename patterns"""

    def extract_from_content(self, content: str) -> Dict:
        """Extract metadata from document content"""
```

## Migration Strategy

### Step 1: Backward Compatibility

- Create adapter layer for existing work item functionality
- Implement configuration that mimics current behavior
- Ensure existing scripts continue to work

### Step 2: Gradual Transition

- Introduce new generic tools alongside existing ones
- Update documentation with new approach
- Provide migration guide for users

### Step 3: Deprecation Path

- Mark work item specific tools as deprecated
- Provide clear migration timeline
- Remove deprecated functionality in major version update

## File Changes Required

### New Files

```
src/
├── document_collection/
│   ├── __init__.py
│   ├── collection.py           # DocumentCollection class
│   ├── schema.py              # Document schema definitions
│   ├── discovery.py           # Document discovery logic
│   └── processor.py           # Generic document processor
├── config/
│   ├── __init__.py
│   ├── collection_config.py   # Configuration management
│   └── schema_validator.py    # Config validation
└── generic_mcp/               # Rename from workitem_mcp
    ├── __init__.py
    ├── server.py              # Updated generic server
    ├── search_documents.py    # Updated searcher
    └── tools/
        ├── __init__.py
        ├── document_tools.py  # Generic document tools
        ├── search_tools.py    # Updated search tools
        └── info_tools.py      # Updated info tools
```

### Modified Files

```
upload/
├── upload_documents.py       # Generic uploader (replace upload_work_items.py)
├── document_utils.py         # Enhanced for generic docs
└── scripts/
    ├── create_generic_index.py
    └── migrate_from_workitems.py

config/
├── collection.yaml.example   # Example collection config
└── .env.example              # Updated environment variables

docs/
├── GENERIC_SETUP.md          # New setup guide
├── COLLECTION_CONFIG.md      # Collection configuration guide
├── MIGRATION_GUIDE.md        # Migration from work items
└── EXAMPLES/                 # Example configurations
    ├── technical_docs.yaml
    ├── research_notes.yaml
    └── project_documentation.yaml
```

## Testing Strategy

### Test Collections

1. **Technical Documentation**: Simulate API docs, guides
2. **Research Collection**: Academic papers, notes
3. **Mixed Media**: Different file types and structures
4. **Large Collection**: Test performance with thousands of documents

### Validation Tests

1. **Backward Compatibility**: Ensure work item functionality still works
2. **Configuration Validation**: Test various collection configurations
3. **Search Quality**: Verify search results across different document types
4. **Performance**: Benchmark upload and search performance

## Success Metrics

### Functionality

- ✅ Support for at least 3 different document collection types
- ✅ Configurable categorization strategies
- ✅ Generic upload process works with various folder structures
- ✅ Search tools work across different document types
- ✅ Backward compatibility maintained for existing users

### Performance

- ✅ Upload performance within 10% of current system
- ✅ Search latency under 500ms for typical queries
- ✅ Memory usage scales reasonably with document count

### Usability

- ✅ Simple configuration for common use cases
- ✅ Clear migration path from current system
- ✅ Comprehensive documentation and examples

## Timeline

### Week 1-2: Foundation

- Implement core abstraction layer
- Create configuration system
- Design new schema structure

### Week 3-4: Upload System

- Build generic document discovery
- Implement flexible upload process
- Create configuration examples

### Week 5-6: MCP Tools

- Update MCP server for generic use
- Implement new tool schemas
- Update search and info tools

### Week 7-8: Testing & Documentation

- Comprehensive testing with different document types
- Create migration guides and examples
- Performance optimization

### Week 9-10: Polish & Release

- Address feedback and issues
- Final documentation updates
- Release preparation

## Conclusion

This generalization plan transforms the Work Item Documentation Retriever into a powerful, flexible Personal Knowledge Assistant that can handle any type of document collection. The approach maintains backward compatibility while providing a clear path forward for more diverse use cases.

The key insight is that "work items" were just one specific organizational scheme for documents. By abstracting this to "categories" and making the organizational rules configurable, we create a much more powerful and reusable system.

This generalized version will serve as a foundation for personal knowledge management, enabling users to create their own AI-powered document retrieval systems for any domain or use case.
