# Personal Documentation Assistant MCP Server

A powerful AI-enhanced document retrieval system using Azure Cognitive Search with vector embeddings and Model Context Protocol (MCP) integration for VS Code.

## 🎯 Project Overview

This project provides **intelligent document search and retrieval** for your documentation through two integrated components:

### 📄 Document Processing & Upload System

- **Purpose**: Processes and indexes your documentation into Azure Cognitive Search
- **Features**: Smart chunking, vector embeddings, idempotent processing, batch uploads
- **Usage**: Run periodically to maintain your searchable document index
- **Key Scripts**: `upload_with_pipeline.py`, `upload_with_custom_metadata.py`, `create_index.py`

### 🔌 MCP Server for VS Code Integration

- **Purpose**: Provides AI-powered search directly within VS Code through the Model Context Protocol
- **Features**: Universal search, context filtering, semantic understanding, tool integration
- **Usage**: Runs as background service, integrates with VS Code Copilot for intelligent queries
- **Key Components**: `run_mcp_server.py`, universal search tools, result formatting

**Complete Workflow**: Upload documents → Start MCP server → Query through VS Code Copilot

## ✨ Key Features

### Document Processing

- **🧠 Vector Embeddings**: Uses Azure OpenAI text-embedding-ada-002 for semantic understanding
- **📊 Smart Chunking**: Intelligent text segmentation for optimal search performance
- **🔄 Idempotent Processing**: File signature tracking prevents duplicate processing
- **📁 Flexible Structure**: Seamless integration with any documentation organization
- **🏷️ Metadata Support**: Full frontmatter parsing for titles, tags, and context information

### Search Capabilities

- **🔍 Hybrid Search**: Combines keyword and semantic vector search
- **🎯 Context Filtering**: Search within specific contexts or across all documentation
- **💡 Semantic Understanding**: Find conceptually related content even with different wording
- **📈 Relevance Scoring**: Advanced ranking algorithms for best results
- **⚡ Fast Retrieval**: Optimized indexing for quick response times

### VS Code Integration

- **🤖 MCP Protocol**: Native integration with VS Code Copilot and AI assistants
- **🛠️ Universal Tools**: 5 powerful universal tools for comprehensive document access
- **🌐 Cross-Document Search**: Universal search across projects, research, APIs, and all document types
- **💬 Natural Language**: Query using plain English questions and concepts
- **📋 Structured Results**: Formatted output with source references and metadata
- **🔧 Easy Setup**: Simple configuration through VS Code settings

## 📁 Project Structure

```
DocumentationRetrievalMCPServer/
├── run_mcp_server.py                  # 🔌 MCP Server entry point
├── requirements.txt                   # Python dependencies
├── .env.example                       # Environment configuration template
├──
├── src/                               # Core application code
│   ├── common/                        # 🔌📄 Shared services
│   │   ├── azure_cognitive_search.py # Azure Search service
│   │   ├── embedding_service.py      # Embedding generation
│   │   └── openai_service.py         # OpenAI integration
│   ├──
│   ├── mcp_server/                    # 🔌 MCP Server components
│   │   ├── server.py                 # MCP Server implementation
│   │   └── tools/                    # Universal MCP tools
│   │       ├── tool_router.py        # Tool dispatch routing
│   │       ├── universal_tools.py    # Universal tool implementations
│   │       ├── tool_schemas.py       # Tool schema definitions
│   │       └── work_item_tools.py    # Legacy compatibility tools
│   ├──
│   ├── document_upload/               # 📄 Document upload system
│   │   ├── document_processing_pipeline.py # Document processing pipeline
│   │   ├── discovery_strategies.py   # Document discovery strategies
│   │   ├── processing_strategies.py  # Document processing strategies
│   │   ├── file_tracker.py           # File processing tracking
│   │   ├── common_scripts/           # Common utility scripts
│   │   │   └── create_index.py       # Index creation script
│   │   └── personal_documentation_assistant_scripts/ # Main upload scripts
│   │       ├── upload_with_pipeline.py # Main upload script
│   │       ├── upload_with_custom_metadata.py # Custom metadata upload
│   │       └── delete_by_context_and_filename.py # Context-based deletion
│   └──
│   └── tests/                         # Test files
├──
└── docs/                              # Documentation
    ├── 01-Architecture-Simplified.md # System architecture overview
    ├── DOCUMENT_UPLOAD_SETUP.md      # Document upload setup guide
    └── MCP_SERVER_SETUP.md           # MCP server setup guide
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
- Documentation directory with files organized by context
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
   python src/document_upload/common_scripts/create_index.py
   ```

2. **Upload your documents:**

   ```bash
   python src/document_upload/personal_documentation_assistant_scripts/upload_with_pipeline.py
   ```

### Part 2: MCP Server for VS Code

**Then, start the MCP server and configure VS Code:**

3. **Start MCP server:**

   ```bash
   python run_mcp_server.py
   ```

4. **Configure VS Code MCP integration:**
   See [MCP_SERVER_SETUP.md](docs/MCP_SERVER_SETUP.md) for detailed instructions.

### Command Reference

#### Document Upload Commands (📄)

**System Setup & Verification:**

- `python src/document_upload/common_scripts/create_index.py` - Create Azure Search index with vector capabilities

**Document Processing:**

- `python src/document_upload/personal_documentation_assistant_scripts/upload_with_pipeline.py <path>` - Process and index all documentation from specified path
- `python src/document_upload/personal_documentation_assistant_scripts/upload_with_pipeline.py <path> --dry-run` - Preview what will be processed without uploading
- `python src/document_upload/personal_documentation_assistant_scripts/upload_with_pipeline.py <path> --force-reset` - Delete all documents and tracker, then reprocess everything
- `python src/document_upload/personal_documentation_assistant_scripts/upload_with_pipeline.py <path> --stats` - Show detailed processing statistics after completion
- `python src/document_upload/personal_documentation_assistant_scripts/upload_with_pipeline.py <path> --verbose` - Enable verbose logging for debugging
- `python src/document_upload/personal_documentation_assistant_scripts/upload_with_custom_metadata.py <path> --metadata '{"title": "Custom Title", "tags": "tag1,tag2", "category": "reference", "work_item_id": "PROJ-123"}'` - Upload with custom metadata override
- `python src/document_upload/personal_documentation_assistant_scripts/upload_with_custom_metadata.py <path> --metadata '{...}' --validate-only` - Validate metadata without uploading

**Document Management:**

- `python src/document_upload/personal_documentation_assistant_scripts/delete_by_context_and_filename.py <context_name>` - Delete all documents for a specific context
- `python src/document_upload/personal_documentation_assistant_scripts/delete_by_context_and_filename.py <context_name> --no-confirm` - Delete without confirmation

**Testing:**

Test your configuration by running document processing in dry-run mode and starting the MCP server.

#### MCP Server Commands (🔌)

**Server Management:**

- `python run_mcp_server.py` - Start the MCP server for VS Code integration
- Configure VS Code MCP integration using `.vscode/mcp.json` file

**Available MCP Tools (use in VS Code Copilot):**

**Universal Tools:**

- `search_documents` - Universal search across all document types with advanced filtering (400-char previews)
- `get_document_content` - Retrieve complete document content without truncation (complements search)
- `get_document_contexts` - Discover available contexts (projects, research, etc.) with statistics
- `explore_document_structure` - Navigate through document hierarchy and structure
- `get_index_summary` - Get comprehensive index statistics and analytics

### Example Queries (in VS Code with MCP Server 🔌)

**Natural Language Search:**

```
"What documentation deals with authentication issues?"
"Show me all content related to performance optimization"
"Find documents about API integration patterns"
"List contexts that mention database optimization"
```

**Specific Context Queries:**

```
"Search for error handling in Project-A documentation"
"What documentation exists for the main research project?"
"Show me the implementation details in context ABC-123"
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
"List all available documentation contexts"
"Give me a summary of the documentation index"
"How many documents are available for each context?"
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
AZURE_SEARCH_INDEX=documentation-index

# Required: Local Documentation Path
PERSONAL_DOCUMENTATION_ROOT_DIRECTORY=C:\Users\YourName\Desktop\Documentation

# Optional: Advanced Configuration
OPENAI_API_VERSION=2024-02-01
SEARCH_API_VERSION=2024-07-01
MAX_CHUNK_SIZE=1000
CHUNK_OVERLAP=200
```

### Environment Setup Tips

1. **Azure OpenAI**: Ensure your deployment name matches `EMBEDDING_DEPLOYMENT`
2. **Search Service**: Use the admin key (not query key) for document uploads
3. **Documentation Path**: Use absolute path with proper Windows path format
4. **Index Name**: Will be created automatically if it doesn't exist

## 🧪 Testing

### Test Document Upload System (📄)

```bash
# Create the search index
python src/document_upload/common_scripts/create_index.py

# Test document processing with pipeline
python src/document_upload/personal_documentation_assistant_scripts/upload_with_pipeline.py "path/to/your/docs" --dry-run
```

### Test MCP Server Integration (🔌)

```bash
# Test MCP server functionality
python run_mcp_server.py

# Test in VS Code after MCP configuration
# Use VS Code agent to ask: "List all documentation contexts"
```

## 📊 Architecture

The system consists of two main parts working together:

### Part 1: Document Processing Pipeline (📄)

1. **Document Discovery**: Scans documentation directory structure
2. **Content Processing**: Extracts content and metadata from various file types
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

Once integrated with VS Code, you can use these **5 universal document search tools** through natural language queries:

### 🌟 Universal Search Tools

- **`search_documents`**: Universal document search across all document types

  - **Features**: Text, vector, semantic, and hybrid search modes
  - **Filtering**: Context name, file type, category, file name, chunk pattern, tags
  - **Scope**: Works across projects, research, APIs, contracts, and all document types
  - **Best for**: Any document search need with advanced filtering
  - **Note**: Returns 400-character content previews

- **`get_document_content`**: Retrieve complete document content without truncation

  - **Features**: Full content access by document ID or context+file combination
  - **Flexibility**: Optional content length limits and metadata inclusion control
  - **Best for**: Reading complete documents after finding them with search_documents
  - **Perfect complement**: Use search_documents to find → get_document_content for full text

- **`get_document_contexts`**: Discover available document contexts with statistics

  - **Features**: Context filtering and statistics
  - **Output**: Document counts per context, hierarchical view
  - **Best for**: Understanding your document landscape and organization

- **`explore_document_structure`**: Navigate through document hierarchy

  - **Features**: Explore contexts, files, chunks, and categories
  - **Navigation**: Structure visualization and organized browsing
  - **Best for**: Understanding document organization and finding specific files

- **`get_index_summary`**: Comprehensive index statistics and analytics
  - **Features**: Total counts, facet distributions, popular tags
  - **Analytics**: Context distribution, file types, categories
  - **Best for**: Getting overview of your entire document collection

### Usage in VS Code

Simply ask questions naturally - the MCP server automatically selects the appropriate tool:

- "What's in my Project-A documentation?" → Uses `search_documents` with context filter
- "Find anything about authentication" → Uses `search_documents`
- "Show me the full content of document abc123" → Uses `get_document_content` with document ID
- "Get the complete readme file from the project context" → Uses `get_document_content` with context+file
- "Find deployment guides then show me the complete instructions" → Combined workflow: search + content retrieval
- "List all documentation contexts" → Uses `get_document_contexts`
- "Show me my documentation structure" → Uses `explore_document_structure`

## 📚 Document Support

- **Markdown Files**: Full support with frontmatter parsing
- **Text Files**: Plain text document support
- **Word Documents**: DOCX file processing
- **Frontmatter Fields**:
  - `title`: Document title
  - `context_name`: Associated context identifier
  - `tags`: Comma-separated tags
  - `category`: Document category
  - `last_modified`: Last modification date

## 🛡️ Error Handling

The system includes comprehensive error handling:

- Connection failures to Azure services
- Document processing errors
- Search query failures
- Automatic retry mechanisms
- Context validation
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
- **"No documentation found"**: Ensure PERSONAL_DOCUMENTATION_ROOT_DIRECTORY points to correct directory
- **"MCP server not connecting"**: Check VS Code MCP configuration paths
- **"Force reprocessing not working"**: Use `--force --context <NAME>` for targeted reprocessing
- **"Documents not deleted"**: Use delete utility scripts for manual cleanup

### Document Management

Use the utility scripts for document lifecycle management:

```bash
# Check what documents exist for a context
python src/document_upload/personal_documentation_assistant_scripts/delete_by_context_and_filename.py <context_name> --dry-run

# Clean up specific context documents
python src/document_upload/personal_documentation_assistant_scripts/delete_by_context_and_filename.py <context_name>
```

### Get Help

1. Check Azure service connections in your `.env` file
2. Use `--dry-run` flag with upload scripts to test configuration
3. Review log files for detailed error messages
4. Use the `create_index.py` script to recreate the search index if needed

## 📝 License

This project is for internal use and documentation purposes.

---

**Made with ❤️ for efficient documentation retrieval**
