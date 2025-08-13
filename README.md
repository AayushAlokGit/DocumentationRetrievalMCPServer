# Work Item Documentation Retriever

A powerful document retrieval system for Work Items using Azure Cognitive Search with vector search capabilities and AI-powered embeddings.

## 🎯 Project Components

This project consists of **two main parts**:

### 1. 📄 Document Processing & Upload System

- **Purpose**: Processes and indexes your work item documentation
- **Components**: Scripts to discover, process, and upload markdown files to Azure Cognitive Search
- **Usage**: Run once to set up your searchable index, then periodically to add new documents
- **Key Files**: `src/upload/scripts/upload_work_items.py`, `src/upload/document_upload.py`, `src/upload/document_utils.py`

### 2. 🔌 MCP Server for VS Code Integration

- **Purpose**: Provides intelligent search capabilities directly within VS Code
- **Components**: Model Context Protocol server that exposes search tools to VS Code agent
- **Usage**: Runs as a background service, integrates with VS Code for AI-powered documentation queries
- **Key Files**: `run_mcp_server.py`, `src/workitem_mcp/search_documents.py`, `src/common/azure_cognitive_search.py`

**Workflow**: First use the document upload system to index your files, then run the MCP server to enable AI-powered search in VS Code.

## 🚀 Features

- **Vector Search**: AI-powered semantic search using Azure OpenAI embeddings
- **Document Processing**: Automatic processing of Markdown files with frontmatter support
- **Intelligent Chunking**: Smart text chunking for optimal search performance
- **Work Item Integration**: Seamless integration with Work Items directory structure
- **Interactive Search**: Command-line interface for easy querying
- **VS Code Integration**: Model Context Protocol server for VS Code agent mode

## 📁 Project Structure

```
PersonalDocumentationAssistantMCPServer/
├── run_mcp_server.py                  # 🔌 MCP Server entry point
├── upload_documents.py               # 📄 Document upload CLI
├──
├── src/                               # Core application code
│   ├── common/                        # 🔌📄 Shared services
│   │   ├── azure_cognitive_search.py # Azure Search service
│   │   ├── embedding_service.py      # Embedding generation
│   │   └── openai_service.py         # OpenAI integration
│   ├──
│   ├── workitem_mcp/                  # � MCP Server components
│   │   ├── server.py                 # MCP Server implementation
│   │   ├── search_documents.py       # Search functionality
│   │   └── tools/                    # MCP tools and routing
│   │       ├── tool_router.py        # Tool dispatch routing
│   │       ├── search_tools.py       # Search tool implementations
│   │       ├── info_tools.py         # Information tools
│   │       ├── result_formatter.py   # Result formatting
│   │       └── tool_schemas.py       # Tool schema definitions
│   ├──
│   ├── upload/                        # 📄 Document upload system
│   │   ├── document_upload.py        # Document processing pipeline
│   │   ├── document_utils.py         # Document utilities
│   │   ├── file_tracker.py           # File processing tracking
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
└── .env                              # Environment variables (create from .env.example)
```

**Legend**: 🔌 = MCP Server components | 📄 = Document Upload components

## 🛠️ Setup

This project has **two separate setup processes** for each component:

### 📄 Document Upload System Setup

**Complete this FIRST** - Sets up document processing and search index:

- 📖 **[DOCUMENT_UPLOAD_SETUP.md](DOCUMENT_UPLOAD_SETUP.md)** - Complete setup guide
- Includes Azure services setup, environment configuration, and document indexing

### 🔌 MCP Server Setup

**Complete this SECOND** - Integrates with VS Code for AI-powered search:

- 📖 **[MCP_SERVER_SETUP.md](MCP_SERVER_SETUP.md)** - Complete setup guide
- Requires completed document upload setup as prerequisite

### Quick Prerequisites Check

- Python 3.8+
- Azure Cognitive Search service (Basic tier+)
- Azure OpenAI service with text-embedding-ada-002
- Work Items directory with Markdown files
- VS Code (for MCP integration)

### Installation

**Follow the component-specific setup guides:**

1. **📄 Document Upload System**: See [DOCUMENT_UPLOAD_SETUP.md](DOCUMENT_UPLOAD_SETUP.md)

   - Azure services setup
   - Environment configuration
   - Document indexing

2. **🔌 MCP Server Integration**: See [MCP_SERVER_SETUP.md](MCP_SERVER_SETUP.md)
   - VS Code MCP configuration
   - Server integration
   - Testing and usage

## 🎯 Usage

### Part 1: Document Processing & Upload

**First, set up your search index and upload documents:**

1. **Set up the search index:**

   ```bash
   python src/upload/scripts/create_index.py
   ```

2. **Upload your documents:**

   ```bash
   python src/upload/scripts/upload_work_items.py
   ```

### Part 2: MCP Server for VS Code

**Then, start the MCP server and configure VS Code:**

3. **Start MCP server:**

   ```bash
   python mcp_server.py
   # or use: start_mcp_server.bat (Windows)
   ```

4. **Configure VS Code MCP integration:**
   See [VSCODE_MCP_SETUP.md](VSCODE_MCP_SETUP.md) for detailed instructions.

### Command Reference

#### Document Upload Commands (📄)

- `python src/upload/scripts/verify_document_upload_setup.py` - Verify document upload system setup is correct
- `python src/upload/scripts/create_index.py` - Create Azure Search index with vector capabilities
- `python src/upload/scripts/upload_work_items.py` - Process and index all Work Items documents
- `python src/upload/scripts/upload_work_items.py --work-item WI-123` - Upload specific work item
- `python src/upload/scripts/upload_work_items.py --dry-run` - Preview what will be uploaded
- `python src/upload/scripts/upload_work_items.py --reset` - Delete all search documents and reset tracker for complete reprocessing

#### MCP Server Commands (🔌)

- `python run_mcp_server.py` - Start the MCP server for VS Code integration
- Use VS Code agent to query: "What work items dealt with authentication?"

### Example Queries (in VS Code with MCP Server 🔌)

```bash
# Search for specific topics
"What work items dealt with authentication?"

# Find work items by type
"Show me all bug fixes related to security"

# Search for code examples
"Find API integration examples"

# Get work item summaries
"List all available work items and their document counts"
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

### Test Document Upload System (📄)

```bash
# Verify document upload setup is correct
python verify_document_upload_setup.py

# Test document processing
python tests/test_end_to_end.py
python tests/test_simple_e2e.py
```

### Test MCP Server Integration (🔌)

```bash
# Test MCP server functionality
python mcp_server.py

# Test in VS Code after MCP configuration
# Use VS Code agent to ask: "List all work items"
```

## 📊 Architecture

The system consists of two main parts working together:

### Part 1: Document Processing Pipeline (📄)

1. **Document Discovery**: Scans Work Items directory structure
2. **Content Processing**: Extracts content and metadata from Markdown files
3. **Text Chunking**: Splits documents into searchable chunks
4. **Embedding Generation**: Creates vector embeddings using Azure OpenAI
5. **Index Storage**: Stores documents and vectors in Azure Cognitive Search
6. **File Tracking**: Uses `DocumentProcessingTracker` for idempotent processing

### Part 2: MCP Server for VS Code (🔌)

1. **MCP Protocol**: Provides Model Context Protocol interface for VS Code
2. **Search Engine**: Handles text, vector, and hybrid search queries
3. **Context Retrieval**: Finds relevant documentation for AI assistant
4. **Tool Exposure**: Exposes search tools to VS Code agent mode
5. **Result Formatting**: Formats search results for optimal AI consumption

### Shared Components

- **Azure OpenAI Service**: Used by both parts for embeddings and chat
- **Azure Cognitive Search**: Central search index used by both parts
- **Configuration Management**: Shared environment and settings
- **DocumentProcessingTracker**: Idempotent file processing with direct signature tracking

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
