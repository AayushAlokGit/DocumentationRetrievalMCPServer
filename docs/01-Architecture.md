# Technical Architecture

## Overview

This document outlines the technical architecture for the Work Item Documentation MCP Server project.

## 1. MCP Server Core

- **Language**: Python (using mcp package)
- **Framework**: Model Context Protocol Python SDK
- **Port**: Configurable (default: 3000)
- **Communication**: JSON-RPC over stdio/HTTP

## 2. Vector Database

- **Primary Choice**: Azure Cognitive Search (for both local and production)
- **Why Azure Cognitive Search**:
  - Native vector search capabilities
  - Hybrid search (keyword + semantic)
  - Seamless Azure ecosystem integration
  - Built-in scaling and security
  - Rich filtering and faceting
- **Alternative Options** (if needed):
  - Chroma (lightweight, local only)
  - Pinecone (cloud-based)
  - Weaviate (open-source)
- **Recommendation**: Azure Cognitive Search for consistent experience across environments

## 3. Azure OpenAI Integration

- **Service**: Azure OpenAI Service
- **Models**:
  - **Chat Completion**: GPT-4 or GPT-3.5-turbo for conversational responses and question answering
  - **Embeddings**: text-embedding-ada-002 for vector embeddings
- **Response Generation**: Use chat completion API with system prompts and retrieved context
- **Authentication**: Azure AD or API keys

## 4. Document Processing Pipeline

- **Input**: Local markdown files from Work Items directory
- **Processing**: Text chunking, metadata extraction
- **Embedding**: Generate embeddings using Azure OpenAI
- **Storage**: Store in Azure Cognitive Search with metadata
- **File Tracking**: Use `DocumentProcessingTracker` for idempotent processing
- **Retrieval**: Vector similarity search to find relevant context
- **Response Generation**: Chat completion with retrieved context and system prompts

### File Processing Features

- **Signature-based Tracking**: Uses file path, size, and modification time for change detection
- **Automatic Environment Setup**: Initializes from `WORK_ITEMS_PATH` environment variable
- **Idempotent Processing**: Skips unchanged files to improve efficiency
- **Direct Value Storage**: Stores signature components directly for better debugging visibility

## Chat Completion Workflow

### 1. Retrieval-Augmented Generation (RAG) Pattern

1. **User Query Processing**: Receive question from VS Code agent
2. **Vector Search**: Generate embedding for query and search Azure Cognitive Search
3. **Context Retrieval**: Retrieve relevant work item chunks and metadata
4. **Prompt Construction**: Build chat completion prompt with:
   - System prompt defining role and behavior
   - Retrieved context from work items
   - User's original question
5. **Chat Completion**: Call Azure OpenAI chat completion API
6. **Response Delivery**: Return structured response to MCP client

### 2. System Prompt Strategy

```
You are a helpful assistant that answers questions about work items based on provided documentation.

Context: {retrieved_context}

Guidelines:
- Answer based only on the provided context
- If information is not available, say so clearly
- Provide specific references to work items when possible
- Be concise but comprehensive
- Use a professional, helpful tone
```

### 3. Chat Completion Benefits

- **Conversational**: Natural dialogue with follow-up questions
- **Context-Aware**: Maintains conversation history
- **Structured Responses**: Can format responses for VS Code display
- **Multi-turn Support**: Handles complex, multi-part queries

## Simplified MCP Server Focus

For the initial implementation, we'll focus on a single, powerful tool:

### Core Tool: `ask_question`

- **Purpose**: Answer questions about work items using RAG pattern
- **Input**: Natural language questions
- **Output**: AI-generated answers with source references
- **Features**: Context retrieval, source attribution, professional responses

### Future Tools (Optional Extensions)

- `search_work_items` - Direct search functionality
- `get_work_item_details` - Specific work item retrieval
- `list_work_items` - Browse available items

## Current File Structure

```
PersonalDocumentationAssistantMCPServer/
├── run_mcp_server.py                  # MCP Server entry point
├── upload_documents.py               # Document upload CLI
├──
├── src/                               # Core application code
│   ├── common/                        # Shared services
│   │   ├── azure_cognitive_search.py # Azure Search service
│   │   ├── embedding_service.py      # Embedding generation
│   │   └── openai_service.py         # OpenAI integration
│   ├──
│   ├── workitem_mcp/                  # MCP Server components
│   │   ├── server.py                 # MCP Server implementation
│   │   ├── search_documents.py       # Search functionality
│   │   └── tools/                    # MCP tools and routing
│   │       ├── tool_router.py        # Tool dispatch routing
│   │       ├── search_tools.py       # Search tool implementations
│   │       ├── info_tools.py         # Information tools
│   │       ├── result_formatter.py   # Result formatting
│   │       └── tool_schemas.py       # Tool schema definitions
│   ├──
│   ├── upload/                        # Document upload system
│   │   ├── document_upload.py        # Document processing pipeline
│   │   ├── document_utils.py         # Document utilities
│   │   ├── file_tracker.py           # DocumentProcessingTracker
│   │   └── scripts/                  # Upload utilities
│   │       ├── create_index.py       # Index creation
│   │       ├── upload_work_items.py  # Batch upload
│   │       ├── upload_single_file.py # Single file upload
│   │       └── verify_document_upload_setup.py # System verification
│   └──
│   └── tests/                         # Test files
├──
├── docs/                              # Documentation
├── requirements.txt                   # Python dependencies
└── .env                              # Environment variables
│   ├── __init__.py
│   └── test_server.py
├── .env.example                     # Environment variables template
├── requirements.txt                 # Python dependencies
├── .gitignore
└── README.md
```
