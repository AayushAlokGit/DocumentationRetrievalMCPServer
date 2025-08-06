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

- **Input**: Local markdown files
- **Processing**: Text chunking, metadata extraction
- **Embedding**: Generate embeddings using Azure OpenAI
- **Storage**: Store in Azure Cognitive Search with metadata
- **Retrieval**: Vector similarity search to find relevant context
- **Response Generation**: Chat completion with retrieved context and system prompts

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

## Simplified File Structure

```
WorkItemDocumentationRetriever/
├── src/
│   ├── server/
│   │   ├── __init__.py
│   │   └── main.py                  # MCP server entry point
│   ├── services/
│   │   ├── __init__.py
│   │   ├── azure_openai.py          # Azure OpenAI integration
│   │   └── azure_search.py          # Azure Cognitive Search operations
│   └── utils/
│       ├── __init__.py
│       ├── config.py                # Configuration management
│       └── logger.py                # Logging utilities
├── data/
│   └── work-items/                  # Local markdown files
├── scripts/
│   ├── setup.py                     # Project setup
│   ├── upload_documents.py          # Document upload
│   └── validate_config.py           # Configuration validation
├── tests/
│   ├── __init__.py
│   └── test_server.py
├── .env.example                     # Environment variables template
├── requirements.txt                 # Python dependencies
├── .gitignore
└── README.md
```
