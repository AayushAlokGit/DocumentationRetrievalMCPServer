# Work Item Documentation Retriever

A powerful document retrieval system for Work Items using Azure Cognitive Search with vector search capabilities and AI-powered embeddings.

## 🚀 Features

- **Vector Search**: AI-powered semantic search using Azure OpenAI embeddings
- **Document Processing**: Automatic processing of Markdown files with frontmatter support
- **Intelligent Chunking**: Smart text chunking for optimal search performance
- **Work Item Integration**: Seamless integration with Work Items directory structure
- **Interactive Search**: Command-line interface for easy querying
- **VS Code Integration**: Model Context Protocol server for VS Code agent mode

## 📁 Project Structure

```
WorkItemDocumentationRetriever/
├── mcp_server.py           # Main MCP server entry point
├── src/                    # Core application code
│   ├── create_index.py     # Azure Search index creation
│   ├── document_upload.py  # Document processing and upload
│   ├── openai_service.py   # OpenAI service integration
│   └── search_documents.py # Search functionality
├── tests/                  # Test files
├── scripts/                # Utility scripts
├── config/                 # Configuration files
├── docs/                   # Documentation
├── requirements.txt        # Python dependencies
└── .env                   # Environment variables (create from .env.example)
```

## 🛠️ Setup

### Quick Setup

📚 **For complete setup instructions**: See [COMPLETE_SETUP_GUIDE.md](COMPLETE_SETUP_GUIDE.md)  
⚡ **For quick start**: See [QUICK_SETUP.md](QUICK_SETUP.md)  
🔧 **For VS Code integration**: See [VSCODE_MCP_SETUP.md](VSCODE_MCP_SETUP.md)

### Prerequisites

- Python 3.8+
- Azure Cognitive Search service
- Azure OpenAI service
- Work Items directory with Markdown files

### Installation

1. **Clone and navigate to the project:**

   ```bash
   cd WorkItemDocumentationRetriever
   ```

2. **Create and activate virtual environment:**

   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment:**

   ```bash
   cp .env.example .env
   # Edit .env with your Azure credentials and paths
   ```

5. **Verify setup:**
   ```bash
   python verify_setup.py
   ```

## 🎯 Usage

### Quick Start

1. **Set up the search index:**

   ```bash
   python scripts/create_azure_cognitive_search_index.py
   ```

2. **Upload your documents:**

   ```bash
   python scripts/upload_work_items.py
   ```

3. **Start MCP server:**

   ```bash
   python mcp_server.py
   # or use: start_mcp_server.bat (Windows)
   ```

4. **Configure VS Code MCP integration**
   See [VSCODE_MCP_SETUP.md](VSCODE_MCP_SETUP.md) for detailed instructions.

### Command Reference

- `python verify_setup.py` - Verify your setup is correct
- `python scripts/create_azure_cognitive_search_index.py` - Create Azure Search index with vector capabilities
- `python scripts/upload_work_items.py` - Process and index all Work Items documents
- `python scripts/upload_work_items.py --work-item WI-123` - Upload specific work item
- `python scripts/upload_work_items.py --dry-run` - Preview what will be uploaded
- `python mcp_server.py` - Start the MCP server

### Example Queries (in VS Code)

```bash
# Search for specific topics
"What work items dealt with authentication?"

# Find work items by type
"Show me all bug fixes related to security"

# Search for code examples
"Find API integration examples"
```

## 🔧 Configuration

The system uses environment variables for configuration. Copy `.env.example` to `.env` and configure:

```env
# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=https://your-openai-service.openai.azure.com/
AZURE_OPENAI_KEY=your-openai-key
EMBEDDING_DEPLOYMENT=text-embedding-ada-002

# Azure Cognitive Search Configuration
AZURE_SEARCH_SERVICE=your-search-service
AZURE_SEARCH_KEY=your-search-key
AZURE_SEARCH_INDEX=work-items-index

# Local Paths
WORK_ITEMS_PATH=C:\path\to\your\Work Items
```

## 🧪 Testing

Run the setup verification script:

```bash
python verify_setup.py
```

Run individual test files from the `tests/` directory:

```bash
python tests/test_end_to_end.py
python tests/test_simple_e2e.py
```

## 📊 Architecture

The system consists of several key components:

1. **Document Processor**: Extracts content and metadata from Markdown files
2. **Embedding Generator**: Creates vector embeddings using Azure OpenAI
3. **Search Index**: Stores documents and vectors in Azure Cognitive Search
4. **MCP Server**: Provides Model Context Protocol interface for VS Code
5. **Query Engine**: Handles both text and semantic search queries

## 🔍 MCP Tools

Once integrated with VS Code, you can use these tools:

- **`search_work_items`**: Search across all work item documentation
- **`get_work_item_list`**: List all available work item IDs
- **`get_work_item_summary`**: Get documentation statistics
- **`search_by_work_item`**: Search within a specific work item
- **`semantic_search`**: Find conceptually similar content

## 📚 Document Support

- **Markdown Files**: Full support with frontmatter parsing
- **Frontmatter Fields**:
  - `title`: Document title
  - `work_item_id`: Associated work item ID
  - `tags`: Comma-separated tags
  - `last_modified`: Last modification date

## 🛡️ Error Handling

The system includes comprehensive error handling:

- Connection failures to Azure services
- Document processing errors
- Search query failures
- Automatic retry mechanisms

## 📈 Performance

- **Batch Processing**: Documents processed in batches for efficiency
- **Idempotent Uploads**: Tracks processed files to avoid re-processing
- **Vector Optimization**: 1536-dimension embeddings for optimal search quality
- **Chunking Strategy**: Smart text splitting for better search granularity

## 🤝 Contributing

1. Follow the existing code structure
2. Add tests for new features
3. Update documentation as needed
4. Use proper error handling

## 🐛 Troubleshooting

### Common Issues

- **"Failed to connect to Azure OpenAI"**: Check your Azure OpenAI endpoint and key
- **"Search service connection failed"**: Verify Azure Search service name and key
- **"No work items found"**: Ensure WORK_ITEMS_PATH points to correct directory
- **"MCP server not connecting"**: Check VS Code MCP configuration paths

### Get Help

1. Run `python verify_setup.py` to diagnose issues
2. Check the troubleshooting section in [COMPLETE_SETUP_GUIDE.md](COMPLETE_SETUP_GUIDE.md)
3. Review log files for detailed error messages

## 📝 License

This project is for internal use and documentation purposes.

---

**Made with ❤️ for efficient Work Item documentation retrieval**
