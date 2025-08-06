# Azure Cognitive Search Integration Plan

## Overview

Integration plan for Azure Cognitive Search with MCP server tools for VS Code agent context.

## Current Implementation ✅

### Search Infrastructure

- **Azure Cognitive Search Index**: `work-items-index` with vector search (1536 dimensions)
- **DocumentSearcher Class**: `src/search_documents.py` with hybrid/vector/text search methods
- **Azure OpenAI Integration**: Automatic embedding generation
- **Upload/Delete Support**: Full document lifecycle management

### Verified Components

- ✅ Document upload with embedding generation
- ✅ Text search (keyword matching)
- ✅ Vector search (semantic similarity)
- ✅ Hybrid search (combined approach)
- ✅ Filtered search by work item ID
- ✅ Document deletion and cleanup

## Search Types

### Hybrid Search (Recommended)

- **Use Case**: General questions and context retrieval
- **Method**: Vector similarity + keyword matching
- **Best For**: "How do I configure authentication in WI-123?"

### Vector Search

- **Use Case**: Semantic and conceptual queries
- **Method**: Embedding similarity only
- **Best For**: "Find documents about security implementations"

### Text Search

- **Use Case**: Exact terms and work item IDs
- **Method**: Full-text search only
- **Best For**: "WI-456" or specific error messages

## Current API Interface

### DocumentSearcher Methods

```python
# Text search
results = searcher.text_search(query, work_item_id=None, top_k=5)

# Vector search
results = await searcher.vector_search(query, work_item_id=None, top_k=5)

# Hybrid search (recommended)
results = await searcher.hybrid_search(query, work_item_id=None, top_k=5)

# Document management
success = await searcher.upload_document(document_data)
success = searcher.delete_document(document_id)

# Index statistics
count = searcher.get_document_count()
work_items = searcher.get_work_items()
```

### Search Result Format

```python
# Each result contains:
{
    "id": "unique-document-id",
    "content": "document content",
    "title": "document title",
    "work_item_id": "WI-123",
    "file_path": "path/to/file.md",
    "tags": "tag1,tag2",
    "chunk_index": 0,
    "@search.score": 0.85  # relevance score
}
```

## MCP Server Integration

### Recommended MCP Tools

#### Tool 1: `search_work_items`

- **Purpose**: Search work item documentation
- **Input**: query, work_item_filter (optional), max_results
- **Output**: Formatted search results with relevance scores
- **Search Type**: Hybrid (text + vector)

#### Tool 2: `get_work_item_context`

- **Purpose**: Get context for answering questions
- **Input**: question, work_item_id (optional)
- **Output**: Formatted context for LLM consumption
- **Search Type**: Hybrid optimized for context

#### Tool 3: `list_work_items`

- **Purpose**: Browse available work items
- **Input**: pattern (optional)
- **Output**: Work item inventory with document counts
- **Search Type**: Faceted search

### Context Formatting Example

```python
def format_context(results, question):
    context = f"**Question**: {question}\n\n"

    for i, result in enumerate(results, 1):
        context += f"**Source {i}** (Score: {result['@search.score']:.2f})\n"
        context += f"Work Item: {result['work_item_id']}\n"
        context += f"File: {result['file_path']}\n"
        context += f"Content: {result['content']}\n\n"
        context += "---\n\n"

    context += "**Instructions**: Base your answer on the provided sources.\n"
    return context
```

## Testing

The implementation has been verified with `simple_test.py`:

- ✅ Document upload with embedding generation
- ✅ Text search functionality
- ✅ Vector search functionality
- ✅ Document cleanup
- ✅ End-to-end workflow

Run test: `python simple_test.py`

## Next Steps

1. **MCP Server Integration**: Update MCP server to use DocumentSearcher
2. **Context Optimization**: Implement result formatting for LLM context
3. **Performance Monitoring**: Add search analytics and caching
4. **Error Handling**: Robust error handling for production use

This implementation provides a solid foundation for AI-powered work item documentation search.
