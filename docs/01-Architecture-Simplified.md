# Work Item Documentation MCP Server - Architecture

## Overview

A dual-component system that combines intelligent document processing with AI-powered search capabilities through VS Code integration.

**Vision**: Enable developers to ask natural language questions about work item documentation directly within VS Code using Azure Cognitive Search and Model Context Protocol.

## System Components

### 🔄 Document Processing Pipeline

- Strategy-based document discovery and processing
- Azure Cognitive Search integration with vector embeddings
- Idempotent file tracking and comprehensive metadata extraction

### 🔌 MCP Server for VS Code

- 8 specialized search and information tools
- Real-time VS Code Copilot integration
- Multiple search types: text, vector, hybrid, semantic

---

## Technical Stack

### Core Technologies

- **Language**: Python 3.8+
- **MCP Framework**: Model Context Protocol Python SDK
- **Vector Database**: Azure Cognitive Search
- **Embeddings**: Azure OpenAI (text-embedding-ada-002, 1536 dimensions)
- **Communication**: JSON-RPC over stdio

### Azure Services

- **Azure Cognitive Search**: Vector + hybrid search with 14-field schema
- **Azure OpenAI**: Embeddings generation and future chat completion
- **Integration**: Enterprise-grade security and scaling

---

## Document Processing Pipeline

### Three-Phase Strategy-Based Architecture

#### Phase 1: Document Discovery

- **Strategy**: `PersonalDocumentationDiscoveryStrategy`
- **Scope**: Scans work item directory structures
- **Filtering**: Configurable file types (.md, .txt, .docx)
- **Metadata**: Extracts work item IDs and classifications

#### Phase 2: Document Processing

- **Strategy**: `PersonalDocumentationAssistantProcessingStrategy`
- **Processing**: Intelligent chunking with context preservation
- **Embeddings**: Asynchronous Azure OpenAI embedding generation
- **Output**: Azure Cognitive Search-ready objects

#### Phase 3: Upload & Indexing

- **Upload**: Individual document processing to Azure Cognitive Search
- **Tracking**: Immediate success marking with signature-based change detection
- **Error Handling**: Failed upload logging (⚠️ **No retry mechanism**)

### File Tracking System

- **Signature**: File path + size + modification time
- **Storage**: JSON-based tracking file
- **Behavior**: Idempotent processing (skips unchanged files)

---

## Generic Index Design

### Strategy-Independent Schema

The Azure Cognitive Search index uses **generic field names** to support multiple document types:

```python
{
    "context_id": "Work item ID / Project ID / Contract ID",
    "context_name": "Work item name / Project name / Contract name",
    "category": "Document type/classification",
    "content": "Full-text searchable content",
    "content_vector": "1536-dimensional embeddings",
    "chunk_index": "Document chunk sequence"
}
```

### Strategy Mapping Examples

| Strategy Type  | `context_id`  | `context_name`  | `category`       |
| -------------- | ------------- | --------------- | ---------------- |
| **Work Items** | WORK-123      | Work Item Title | technical/design |
| **API Docs**   | API-SERVICE-1 | Service Name    | endpoint/auth    |
| **Legal Docs** | CONTRACT-456  | Contract Title  | legal/policy     |

---

## MCP Tools

### 8 Specialized Search Tools

#### Core Search (3 tools)

1. **`search_work_items`** - Universal search with configurable types
2. **`search_by_work_item`** - Focused single work item search
3. **`semantic_search`** - Concept-based semantic search

#### Chunk Navigation (3 tools)

4. **`search_by_chunk`** - Precise chunk identification
5. **`search_file_chunks`** - File-specific chunk retrieval
6. **`search_chunk_range`** - Sequential chunk reading

#### Information (2 tools)

7. **`get_work_item_list`** - Available work item discovery
8. **`get_work_item_summary`** - System statistics and health

### Search Types Comparison

| Type         | Best For           | Technology             | Performance      |
| ------------ | ------------------ | ---------------------- | ---------------- |
| **Text**     | Exact keywords     | Azure Search BM25      | Fastest          |
| **Vector**   | Natural language   | OpenAI embeddings      | Good             |
| **Hybrid**   | Balanced relevance | Text + Vector          | Best relevance   |
| **Semantic** | Complex questions  | Azure semantic ranking | Most intelligent |

---

## Configuration

### Environment Variables

```bash
# Azure Cognitive Search
AZURE_SEARCH_SERVICE=your-search-service-name
AZURE_SEARCH_KEY=your-admin-key
AZURE_SEARCH_INDEX=work-items-index

# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://your-service.openai.azure.com/
AZURE_OPENAI_KEY=your-api-key
EMBEDDING_DEPLOYMENT=text-embedding-ada-002

# Document Processing
PERSONAL_DOCUMENTATION_ROOT_DIRECTORY=C:\path\to\Work Items
```

### VS Code MCP Setup

**File**: `.vscode/mcp.json`

```json
{
  "servers": {
    "work-items-documentation": {
      "command": "python",
      "args": ["run_mcp_server.py"],
      "cwd": "C:\\absolute\\path\\to\\project"
    }
  }
}
```

---

## Current Status

### Production Statistics

- **375 documents** indexed across **22 work items**
- **93 unique files** processed
- **Sub-second search** response times
- **8 MCP tools** available in VS Code

### Key Limitations

- ⚠️ **No retry mechanism** for failed uploads
- **Single attempt policy** for document processing
- **Manual recovery** required for upload failures

---

## Development Workflow

### Setup Process

1. Configure Azure services and environment variables
2. Run `create_index.py` to set up Azure Cognitive Search
3. Use `upload_work_items.py` to process and index documents
4. Configure `.vscode/mcp.json` for VS Code integration
5. Query documentation directly within VS Code

### Maintenance Commands

```bash
# Upload new/changed documents (idempotent)
python src/document_upload/personal_documentation_assistant_scripts/upload_work_items.py

# Force reprocessing
python src/document_upload/personal_documentation_assistant_scripts/upload_work_items.py --reset

# System verification
python src/document_upload/common_scripts/verify_document_upload_setup.py
```

---

## Future Enhancements

### Short Term

- **Upload Retry Mechanism**: Exponential backoff for failed uploads
- **Chat Completion**: Direct question answering within VS Code
- **Advanced Filtering**: Date ranges, content types, custom metadata

### Medium Term

- **Multi-Language Support**: PDF, HTML, additional file formats
- **Real-Time Updates**: Live document synchronization
- **Analytics**: Usage analytics and search optimization

### Long Term

- **Multi-Modal Search**: Image and diagram search capabilities
- **Knowledge Graph**: Relationship mapping between work items
- **Integration Ecosystem**: Jira, Azure DevOps, GitHub integration

---

## Key Architectural Strengths

- **Generic Index Design**: Single schema supports unlimited document types
- **Strategy Pattern**: Extensible for new use cases without infrastructure changes
- **Production Ready**: Enterprise Azure services with proper error handling
- **Developer-Centric**: Seamless VS Code integration with natural language queries
- **Cost Efficient**: Single index, shared infrastructure, unified management

The system successfully bridges static documentation and intelligent, context-aware developer assistance through AI-powered search within the development environment.
