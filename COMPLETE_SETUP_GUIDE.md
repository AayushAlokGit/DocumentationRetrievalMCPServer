# Work Item Documentation Retriever - Complete Setup Guide

A comprehensive guide to set up the Work Item Documentation MCP Server for VS Code integration.

## 🎯 Overview

This project creates a Model Context Protocol (MCP) server that enables VS Code to intelligently search and query your work item documentation using AI. It indexes markdown files from your work items directory and provides semantic search capabilities directly in VS Code.

## 📋 Prerequisites

Before starting, ensure you have:

### Required Services

- **Azure OpenAI Service** with deployment access
- **Azure Cognitive Search** service
- **Python 3.8+** installed on your machine
- **VS Code** with MCP support

### Required Access

- Azure subscription with permissions to create/manage:
  - Azure OpenAI resources
  - Azure Cognitive Search resources
- Work Items documentation stored in markdown files

## 🚀 Step-by-Step Setup

### Step 1: Clone and Navigate to Project

```bash
# If cloning from repository
git clone <repository-url>
cd WorkItemDocumentationRetriever

# Or if you already have the project
cd "C:\Users\aayushalok\OneDrive - Microsoft\Desktop\Personal Projects\WorkItemDocumentationRetriever"
```

### Step 2: Set Up Python Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Azure Services Setup

#### 3.1 Create Azure OpenAI Service

1. **Create Azure OpenAI Resource:**

   - Go to [Azure Portal](https://portal.azure.com)
   - Create new resource → AI + Machine Learning → Azure OpenAI
   - Choose region (e.g., East US, West Europe)
   - Note down: Endpoint URL and API Key

2. **Deploy Required Models:**
   - Navigate to Azure OpenAI Studio
   - Deploy these models:
     - **text-embedding-ada-002** (for embeddings)
     - **gpt-4** or **gpt-35-turbo** (for chat completions)
   - Note down deployment names

#### 3.2 Create Azure Cognitive Search Service

1. **Create Search Service:**
   - Go to Azure Portal
   - Create new resource → Web → Azure Cognitive Search
   - Choose pricing tier (Basic or higher for vector search)
   - Note down: Service name and Admin API key

### Step 4: Environment Configuration

Create a `.env` file in the project root:

```bash
# Copy the example environment file
cp config/.env.example .env
```

Edit `.env` with your Azure credentials:

```env
# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=https://your-openai-service.openai.azure.com/
AZURE_OPENAI_KEY=your-openai-api-key-here
EMBEDDING_DEPLOYMENT=text-embedding-ada-002
OPENAI_API_VERSION=2024-05-01-preview

# Azure Cognitive Search Configuration
AZURE_SEARCH_SERVICE=your-search-service-name
AZURE_SEARCH_KEY=your-search-admin-key-here
AZURE_SEARCH_INDEX=work-items-index

# Local Paths - Update this to your Work Items directory
WORK_ITEMS_PATH=C:\path\to\your\Work Items

# Optional: Chunking Configuration
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
VECTOR_DIMENSIONS=1536
```

### Step 5: Prepare Your Work Items Directory

Your work items should be organized like this:

```
Work Items/
├── WI-12345/
│   ├── requirements.md
│   ├── implementation-notes.md
│   └── testing.md
├── BUG-67890/
│   ├── analysis.md
│   ├── fix-documentation.md
│   └── screenshots/ (ignored)
└── FEATURE-11111/
    ├── design.md
    ├── implementation.md
    └── testing.md
```

**Key Requirements:**

- Each work item has its own directory
- Directory name = Work Item ID
- Contains `.md` (markdown) files
- Can include YAML frontmatter for metadata

**Example Markdown with Frontmatter:**

```markdown
---
title: "User Authentication Implementation"
tags: ["authentication", "security", "backend"]
work_item_id: "WI-12345"
last_modified: "2024-08-06"
---

# User Authentication Implementation

This document describes the implementation of user authentication...
```

### Step 6: Initialize the Search Index

```bash
# Create the Azure Cognitive Search index
python scripts/create_azure_cognitive_search_index.py
```

Expected output:

```
🔧 Creating Azure Cognitive Search index...
✅ Search index 'work-items-index' created successfully
📊 Index created with vector search capabilities (1536 dimensions)
```

### Step 7: Upload Your Documentation

```bash
# Upload all work item documents
python scripts/upload_work_items.py

# Or upload specific work item
python scripts/upload_work_items.py --work-item WI-12345

# Dry run to see what will be uploaded
python scripts/upload_work_items.py --dry-run
```

Expected output:

```
🚀 Starting document upload process...
📁 Discovered 45 markdown files across 12 work items
🔄 Processing documents with embeddings...
✅ Uploaded 234 document chunks successfully
📊 Processing complete: 12 work items, 45 files, 234 chunks
```

### Step 8: Test the MCP Server

```bash
# Test the MCP server functionality
python -c "
import asyncio
import sys
sys.path.append('src')
from mcp_server import main
asyncio.run(main())
"
```

Or use the VS Code task:

```bash
# Run the test task
python mcp_server.py
```

### Step 9: Configure VS Code MCP Integration

#### 9.1 Update MCP Configuration

Edit your VS Code MCP settings file (usually in `%APPDATA%\Code\User\globalStorage\rooveterinaryinc.roo-cline\settings\cline_mcp_settings.json`):

```json
{
  "mcpServers": {
    "work-items-documentation": {
      "command": "python",
      "args": [
        "C:\\Users\\aayushalok\\OneDrive - Microsoft\\Desktop\\Personal Projects\\WorkItemDocumentationRetriever\\mcp_server.py"
      ],
      "cwd": "C:\\Users\\aayushalok\\OneDrive - Microsoft\\Desktop\\Personal Projects\\WorkItemDocumentationRetriever",
      "env": {
        "PYTHONPATH": "C:\\Users\\aayushalok\\OneDrive - Microsoft\\Desktop\\Personal Projects\\WorkItemDocumentationRetriever"
      }
    }
  }
}
```

#### 9.2 Restart VS Code

Restart VS Code to load the new MCP server configuration.

## 🧪 Testing Your Setup

### Test 1: Verify Index Creation

```bash
python -c "
import sys; sys.path.append('src')
from search_documents import DocumentSearcher
searcher = DocumentSearcher()
print(f'📊 Documents: {searcher.get_document_count()}')
print(f'📋 Work Items: {len(searcher.get_work_items())}')
"
```

### Test 2: Test Search Functionality

```bash
python scripts/test_search.py
```

### Test 3: Interactive Search

```bash
python src/search_documents.py
```

Try queries like:

- `text authentication`
- `vector login implementation`
- `hybrid user security`

### Test 4: VS Code Integration

1. Open VS Code
2. Open the Command Palette (`Ctrl+Shift+P`)
3. Look for MCP-related commands
4. Test queries like:
   - "What work items dealt with authentication?"
   - "Show me API implementation examples"
   - "List all available work items"

## 🔧 Available MCP Tools in VS Code

Once configured, you can use these tools:

- **`search_work_items`**: General search across all documentation
- **`get_work_item_list`**: List all indexed work item IDs
- **`get_work_item_summary`**: Get statistics about your documentation
- **`search_by_work_item`**: Search within a specific work item
- **`semantic_search`**: Find conceptually similar content

## 🐛 Troubleshooting

### Common Issues

#### 1. "Failed to connect to Azure OpenAI"

**Solution:**

- Verify `AZURE_OPENAI_ENDPOINT` and `AZURE_OPENAI_KEY` in `.env`
- Check if your Azure OpenAI resource is properly deployed
- Ensure the embedding model is deployed in Azure OpenAI Studio

#### 2. "Search service connection failed"

**Solution:**

- Verify `AZURE_SEARCH_SERVICE` and `AZURE_SEARCH_KEY` in `.env`
- Check if Azure Cognitive Search service is running
- Ensure the service tier supports vector search (Basic or higher)

#### 3. "No work items found"

**Solution:**

- Verify `WORK_ITEMS_PATH` points to correct directory
- Ensure work item directories contain `.md` files
- Check file permissions and that files are not empty

#### 4. "MCP server not connecting in VS Code"

**Solution:**

- Verify the absolute path in MCP configuration is correct
- Ensure Python virtual environment is activated
- Check VS Code console for MCP-related error messages
- Restart VS Code after configuration changes

### Debugging Commands

```bash
# Test Azure connections
python -c "
import sys; sys.path.append('src')
from openai_service import get_openai_service
from azure_cognitive_search import get_azure_search_service

# Test OpenAI
openai_svc = get_openai_service()
print(f'OpenAI Connection: {openai_svc.test_connection()}')

# Test Search
search_svc = get_azure_search_service()
print(f'Search Index Documents: {search_svc.get_document_count()}')
"

# Check processed files
python -c "
from src.file_tracker import ProcessingTracker
tracker = ProcessingTracker('processed_files.json')
stats = tracker.get_stats()
print(f'Processed files: {stats}')
"

# Test MCP server startup
python mcp_server.py --test
```

## 📊 Usage Examples

Once everything is set up, you can use the system in VS Code:

### Example Queries

- **General Search**: "Show me all authentication-related work items"
- **Specific Work Item**: "What was implemented in WI-12345?"
- **Technical Details**: "How did we handle API rate limiting?"
- **Bug Analysis**: "What were the root causes of performance issues?"
- **Implementation Patterns**: "Show me examples of database integration"

### Expected Responses

The system will provide:

- Relevant document excerpts
- Work item IDs and titles
- Source file paths
- Relevance scores
- Related tags and metadata

## 🔄 Maintenance

### Updating Documentation

```bash
# Reprocess specific work item
python scripts/upload_work_items.py --work-item WI-12345 --force

# Reprocess all documentation
python scripts/upload_work_items.py --reset
```

### Index Management

```bash
# Recreate index
python scripts/create_azure_cognitive_search_index.py --recreate

# Check index health
python -c "
import sys; sys.path.append('src')
from azure_cognitive_search import get_azure_search_service
search_svc = get_azure_search_service()
print(f'Index: {search_svc.index_name}')
print(f'Documents: {search_svc.get_document_count()}')
print(f'Work Items: {len(search_svc.get_work_items())}')
"
```

## 📚 Additional Resources

- [Model Context Protocol Documentation](https://modelcontextprotocol.io/)
- [Azure OpenAI Service Documentation](https://docs.microsoft.com/en-us/azure/cognitive-services/openai/)
- [Azure Cognitive Search Documentation](https://docs.microsoft.com/en-us/azure/search/)
- [VS Code MCP Integration Guide](https://code.visualstudio.com/docs/editor/model-context-protocol)

## 🆘 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review the log files in your project directory
3. Verify all environment variables are correctly set
4. Ensure all Azure services are properly configured and running
5. Test individual components (search, embeddings, MCP server) separately

---

**🎉 Once setup is complete, you'll have a powerful AI-powered documentation search system integrated directly into VS Code!**
