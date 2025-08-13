# Personal Documentation Assistant MCP Server

A powerful AI-enhanced document retrieval system using Azure Cognitive Search with vector embeddings and Model Context Protocol (MCP) integration for VS Code.

## 🎯 Project Overview

This project provides **intelligent document search and retrieval** for your Work Items documentation through two integrated components:

### 📄 Document Processing & Upload System

- **Purpose**: Processes and indexes your work item documentation into Azure Cognitive Search
- **Features**: Smart chunking, vector embeddings, idempotent processing, batch uploads
- **Usage**: Run periodically to maintain your searchable document index
- **Key Scripts**: `upload_work_items.py`, `document_upload.py`, `create_index.py`

### 🔌 MCP Server for VS Code Integration

- **Purpose**: Provides AI-powered search directly within VS Code through the Model Context Protocol
- **Features**: Semantic search, work item filtering, context-aware results, tool integration
- **Usage**: Runs as background service, integrates with VS Code Copilot for intelligent queries
- **Key Components**: `run_mcp_server.py`, search tools, result formatting

**Complete Workflow**: Upload documents → Start MCP server → Query through VS Code Copilot

## ✨ Key Features

### Document Processing

- **🧠 Vector Embeddings**: Uses Azure OpenAI text-embedding-ada-002 for semantic understanding
- **📊 Smart Chunking**: Intelligent text segmentation for optimal search performance
- **🔄 Idempotent Processing**: File signature tracking prevents duplicate processing
- **📁 Work Item Structure**: Seamless integration with Work Items directory organization
- **🏷️ Metadata Support**: Full frontmatter parsing for titles, tags, and work item IDs

### Search Capabilities

- **🔍 Hybrid Search**: Combines keyword and semantic vector search
- **🎯 Work Item Filtering**: Search within specific work items or across all documentation
- **💡 Semantic Understanding**: Find conceptually related content even with different wording
- **📈 Relevance Scoring**: Advanced ranking algorithms for best results
- **⚡ Fast Retrieval**: Optimized indexing for quick response times

### VS Code Integration

- **🤖 MCP Protocol**: Native integration with VS Code Copilot and AI assistants
- **🛠️ Tool Ecosystem**: 5 specialized search and information tools
- **💬 Natural Language**: Query using plain English questions and concepts
- **📋 Structured Results**: Formatted output with source references and metadata
- **🔧 Easy Setup**: Simple configuration through VS Code settings

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
│   │       ├── delete_by_work_item.py # Delete by work item ID
│   │       ├── delete_by_file_path.py # Delete by file path
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

**System Setup & Verification:**

- `python src/upload/scripts/verify_document_upload_setup.py` - Verify complete system setup
- `python src/upload/scripts/create_index.py` - Create Azure Search index with vector capabilities

**Document Processing:**

- `python src/upload/scripts/upload_work_items.py` - Process and index all Work Items documents
- `python src/upload/scripts/upload_work_items.py --work-item <ID>` - Upload specific work item by ID
- `python src/upload/scripts/upload_work_items.py --dry-run` - Preview what will be processed without uploading
- `python src/upload/scripts/upload_work_items.py --force --work-item <ID>` - Force reprocessing of specific work item (deletes existing + re-uploads)
- `python src/upload/scripts/upload_work_items.py --reset` - Delete all documents and reset tracker for fresh start
- `python src/upload/scripts/upload_single_file.py <file_path>` - Upload a single markdown file

**Document Management:**

- `python src/upload/scripts/delete_by_work_item.py <work_item_id>` - Delete all documents for a specific work item
- `python src/upload/scripts/delete_by_work_item.py <work_item_id> --no-confirm` - Delete without confirmation
- `python src/upload/scripts/delete_by_file_path.py <file_pattern>` - Delete documents matching file path pattern
- `python src/upload/scripts/delete_by_file_path.py <file_pattern> --no-confirm` - Delete without confirmation

**Testing:**

- `python src/tests/test_simple_e2e.py` - Run simple end-to-end verification tests
- `python src/tests/test_end_to_end.py` - Run comprehensive system tests

#### MCP Server Commands (🔌)

**Server Management:**

- `python run_mcp_server.py` - Start the MCP server for VS Code integration
- Configure VS Code MCP integration using VS Code settings JSON

**Available MCP Tools (use in VS Code Copilot):**

- `search_work_items` - Search across all work item documentation with text/vector/hybrid search
- `search_by_work_item` - Search within a specific work item's documents
- `semantic_search` - Find conceptually similar content using vector embeddings
- `get_work_item_list` - List all available work item IDs in the index
- `get_work_item_summary` - Get summary statistics about work items and document counts

### Example Queries (in VS Code with MCP Server 🔌)

**Natural Language Search:**

```
"What work items dealt with authentication issues?"
"Show me all bug fixes related to performance problems"
"Find documents about API integration patterns"
"List work items that mention database optimization"
```

**Specific Work Item Queries:**

```
"Search for error handling in work item Bug-12345"
"What documentation exists for PersonalDocumentationAssistantMCPServer?"
"Show me the implementation details in work item WI-67890"
```

**Conceptual/Semantic Search:**

```
"Find content related to troubleshooting and debugging"
"Show me anything about code review processes"
"Search for testing strategies and methodologies"
"Find security-related documentation"
```

**Information Retrieval:**

```
"List all available work items"
"Give me a summary of the documentation index"
"How many documents are available for each work item?"
```

## 🔧 Configuration

The system uses environment variables for configuration. Create a `.env` file in the project root:

```env
# Required: Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=https://your-openai-service.openai.azure.com/
AZURE_OPENAI_KEY=your-openai-api-key
EMBEDDING_DEPLOYMENT=text-embedding-ada-002

# Required: Azure Cognitive Search Configuration
AZURE_SEARCH_SERVICE=your-search-service-name
AZURE_SEARCH_KEY=your-search-admin-key
AZURE_SEARCH_INDEX=work-items-index

# Required: Local Work Items Path
PERSONAL_DOCUMENTATION_ROOT_DIRECTORY=C:\Users\YourName\Desktop\Work Items

# Optional: Advanced Configuration
OPENAI_API_VERSION=2024-02-01
SEARCH_API_VERSION=2024-07-01
MAX_CHUNK_SIZE=1000
CHUNK_OVERLAP=200
```

### Environment Setup Tips

1. **Azure OpenAI**: Ensure your deployment name matches `EMBEDDING_DEPLOYMENT`
2. **Search Service**: Use the admin key (not query key) for document uploads
3. **Work Items Path**: Use absolute path with proper Windows path format
4. **Index Name**: Will be created automatically if it doesn't exist

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

Once integrated with VS Code, you can use these **5 specialized tools** through natural language queries:

### Search Tools

- **`search_work_items`**: Multi-modal search across all work item documentation

  - Supports text, vector (semantic), and hybrid search modes
  - Optional work item filtering and result count control
  - Best for: General searches across entire documentation base

- **`search_by_work_item`**: Targeted search within specific work item

  - Focuses search on single work item's documents
  - Ideal for deep-dive investigations
  - Best for: "Find X in work item Y" type queries

- **`semantic_search`**: Pure vector-based conceptual search
  - Uses AI embeddings to find conceptually similar content
  - Great for finding related topics with different wording
  - Best for: Discovering related concepts and ideas

### Information Tools

- **`get_work_item_list`**: List all indexed work item IDs

  - Returns complete inventory of available work items
  - Useful for discovery and system overview
  - Best for: "What work items are available?" queries

- **`get_work_item_summary`**: Statistics and index overview
  - Document counts per work item
  - System health and indexing status
  - Best for: Understanding documentation coverage

### Usage in VS Code

Simply ask questions naturally - the MCP server automatically selects the appropriate tool:

- "What's in work item ABC-123?" → Uses `search_by_work_item`
- "Find anything about authentication" → Uses `search_work_items`
- "List all work items" → Uses `get_work_item_list`

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
- Work item ID validation
- Document lifecycle management

## 📈 Performance

- **Batch Processing**: Documents processed in batches for efficiency
- **Idempotent Uploads**: Tracks processed files to avoid re-processing
- **Vector Optimization**: 1536-dimension embeddings for optimal search quality
- **Chunking Strategy**: Smart text splitting for better search granularity
- **Enhanced Force Reprocessing**: Properly deletes existing documents before re-upload
- **Document Management**: Utility scripts for targeted cleanup and maintenance

## 🤝 Contributing

1. Follow the existing code structure
2. Add tests for new features
3. Update documentation as needed
4. Use proper error handling

## 🐛 Troubleshooting

### Common Issues

- **"Failed to connect to Azure OpenAI"**: Check your Azure OpenAI endpoint and key
- **"Search service connection failed"**: Verify Azure Search service name and key
- **"No work items found"**: Ensure PERSONAL_DOCUMENTATION_ROOT_DIRECTORY points to correct directory
- **"MCP server not connecting"**: Check VS Code MCP configuration paths
- **"Force reprocessing not working"**: Use `--force --work-item <ID>` for targeted reprocessing
- **"Documents not deleted"**: Use delete utility scripts for manual cleanup

### Document Management

Use the utility scripts for document lifecycle management:

```bash
# Check what documents exist for a work item
python src/upload/scripts/delete_by_work_item.py <work_item_id> --dry-run

# Clean up specific work item documents
python src/upload/scripts/delete_by_work_item.py <work_item_id>

# Remove documents by file pattern
python src/upload/scripts/delete_by_file_path.py "filename.md"
```

### Get Help

1. Run `python src/upload/scripts/verify_document_upload_setup.py` to diagnose issues
2. Check the troubleshooting section in setup guides
3. Review log files for detailed error messages
4. Use force reprocessing for clean document state

## 📝 License

This project is for internal use and documentation purposes.

---

**Made with ❤️ for efficient Work Item documentation retrieval**
