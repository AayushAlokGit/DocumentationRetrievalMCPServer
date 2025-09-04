# Personal Documentation Assistant MCP Server

A powerful AI-enhanced document retrieval system with **ChromaDB vector search** and **cloud-based embeddings** for enterprise-grade search with Model Context Protocol (MCP) integration for VS Code.

## 🎯 Project Overview

This project provides **intelligent document search and retrieval** for your documentation through two integrated components with **hybrid architecture**:

### 📄 Document Processing & Upload System

- **Purpose**: Processes and indexes your documentation using ChromaDB vector database
- **Vector Search Architecture**: **ChromaDB** with enterprise-grade text embeddings
- **Features**: Smart chunking, high-quality vector embeddings, idempotent processing, batch uploads
- **Usage**: Run periodically to maintain your searchable document index
- **Key Scripts**: `upload_with_pipeline.py`, `upload_with_custom_metadata.py`, `delete_by_context_and_filename.py`

### 🔌 MCP Server for VS Code Integration

- **Purpose**: Provides AI-powered search directly within VS Code through the Model Context Protocol
- **Architecture**: **ChromaDB backend** with **5 universal tools** and cloud embeddings
- **Features**: Vector semantic search, context filtering, enterprise AI understanding, VS Code Copilot integration
- **Usage**: Runs as background service, integrates with VS Code Copilot for intelligent queries
- **Key Components**: `run_mcp_server.py`, 5 universal search tools, structured result formatting

**Complete Workflow**: Upload documents to ChromaDB → Start MCP server → Query through VS Code Copilot → Enterprise-grade search

## ✨ Key Features

### Document Processing

- **🧠 Enterprise Embeddings**: High-quality text embeddings for superior semantic understanding
- **📊 Smart Chunking**: Intelligent text segmentation for optimal search performance
- **🔄 Idempotent Processing**: File signature tracking prevents duplicate processing
- **📁 Flexible Structure**: Seamless integration with any documentation organization
- **🏷️ Metadata Support**: Full frontmatter parsing for titles, tags, and context information
- **🔒 Local Storage**: ChromaDB stores vectors locally while leveraging cloud AI for embeddings
- **📋 Comprehensive Logging**: Timestamped audit trails with automatic directory creation and dual console+file output
- **⚡ Hybrid Architecture**: Local database performance with cloud AI quality

### Search Capabilities

- **🔍 Vector Search**: Semantic similarity search using ChromaDB with enterprise-grade embeddings
- **🎯 Context Filtering**: Search within specific contexts or across all documentation
- **💡 Semantic Understanding**: Advanced AI-powered concept matching and content discovery
- **📈 Relevance Scoring**: Optimized algorithms for high-dimensional vector similarity
- **⚡ Fast Retrieval**: Local ChromaDB indexing for rapid search with enterprise-quality results
- **🔐 Flexible Privacy**: Local document storage with configurable cloud processing for embeddings

### VS Code Integration

- **🤖 MCP Protocol**: Native integration with VS Code Copilot and AI assistants
- **🛠️ 5 Universal Tools**: Complete document search, exploration, and management capabilities
- **🌐 Hybrid Search**: Semantic search across projects, research, APIs, and all document types
- **💬 Natural Language**: Query using plain English questions and concepts with enterprise AI understanding
- **📋 Structured Results**: Formatted output with source references and metadata
- **🔧 Easy Setup**: Simple configuration through VS Code settings with flexible embedding providers
- **🔐 Configurable Privacy**: Choose your preferred balance of local storage and cloud processing

## 📁 Project Structure

```
DocumentationRetrievalMCPServer/
├── run_mcp_server.py                  # 🔌 MCP Server entry point (ChromaDB default)
├── requirements.txt                   # Python dependencies (ChromaDB + Sentence Transformers)
├── .env.example                       # Environment configuration template
├──
├── src/                               # Core application code
│   ├── common/                        # 🔌📄 Shared services
│   │   ├── vector_search_services/   # Vector search engine abstraction
│   │   │   ├── chromadb_service.py   # ChromaDB implementation (PRIMARY)
│   │   │   ├── azure_cognitive_search.py # Azure Search (LEGACY - reference only)
│   │   │   └── vector_search_service_factory.py # Auto-detects ChromaDB
│   │   └── embedding_services/       # Embedding generation services
│   │       ├── local_embedding_service.py # Local Sentence Transformers (PRIMARY)
│   │       ├── azure_openai_embedding_service.py # Azure OpenAI (LEGACY - reference)
│   │       └── embedding_service_factory.py # Auto-detects local embeddings
│   ├──
│   ├── mcp_server/                    # 🔌 MCP Server components
│   │   ├── server.py                 # MCP Server implementation (ChromaDB integrated)
│   │   └── tools/                    # 5 Universal MCP tools
│   │       ├── tool_router.py        # Tool dispatch routing (ChromaDB)
│   │       ├── chroma_db/            # ChromaDB tools (ACTIVE)
│   │       └── azure_cognitive_search/ # Azure tools (LEGACY - reference only)
│   ├──
│   └──
│   └── document_upload/               # 📄 Document Processing System
│       ├── document_processing_pipeline.py # Strategy-based processing pipeline
│       ├── processing_strategies.py   # Document processing strategies (MD, DOCX, TXT, PPTX)
│       ├── chunking_strategies.py     # Smart text chunking algorithms
│       ├── upload_strategies.py       # Upload strategy abstraction (ChromaDB default)
│       ├── discovery_strategies.py    # File discovery and organization
│       ├── document_processing_tracker.py # File change tracking
│       └── personal_documentation_assistant_scripts/
│           └── chroma_db_scripts/     # 📄 Ready-to-use ChromaDB scripts (PRIMARY)
│               ├── upload_with_pipeline.py
│               ├── upload_with_custom_metadata.py
│               ├── delete_by_context_and_filename.py
│               └── script_tests/      # Comprehensive test coverage
│           └── azure_cognitive_search_scripts/ # LEGACY - reference only
├──
├── docs/                              # 📖 Comprehensive documentation
    ├── README.md                      # Project overview (this file)
    ├── DOCUMENT_UPLOAD_SETUP_FOR_CHROMADB.md # ChromaDB setup (PRIMARY GUIDE)
    ├── DOCUMENT_UPLOAD_SETUP_FOR_AZURE_COGNTIVE_SEARCH.md # Azure setup (LEGACY)
    ├── MCP_SERVER_SETUP.md           # MCP server setup guide
    ├── 02-Architecture-with-chromadb-local-embeddings.md # Architecture guide (PRIMARY)
    ├── 01-Architecture-with-azure-cognitive-search.md # Azure architecture (LEGACY)
    └── CHROMADB_DATA_VIEWING_GUIDE.md # ChromaDB data inspection tools
```

**Legend**: 🔌 = MCP Server components | 📄 = Document Upload components | **PRIMARY** = Current active implementation | **LEGACY** = Maintained for reference

## 🛠️ Setup

### 🎯 Current Architecture: ChromaDB + Local Embeddings (100% Local & Private)

**The system now runs entirely locally with complete privacy and zero ongoing costs:**

1. **📄 Document Upload System**: [DOCUMENT_UPLOAD_SETUP_FOR_CHROMADB.md](DOCUMENT_UPLOAD_SETUP_FOR_CHROMADB.md)
2. **🔌 MCP Server Setup**: [MCP_SERVER_SETUP.md](MCP_SERVER_SETUP.md)

**Benefits**:

- ✅ **Zero cloud costs** - no subscriptions or API usage fees
- ✅ **Complete privacy** - all data stays on your machine
- ✅ **Works offline** - no internet required after setup
- ✅ **No API keys** - no account setup or credential management
- ✅ **Fast performance** - local SSD storage with sub-100ms search
- ✅ **Easy maintenance** - simple local file management

### � Legacy Reference: Azure Cognitive Search (Deprecated)

_The Azure integration is maintained for reference but is no longer the recommended approach:_

1. **📄 Document Upload System**: [DOCUMENT_UPLOAD_SETUP_FOR_AZURE_COGNTIVE_SEARCH.md](DOCUMENT_UPLOAD_SETUP_FOR_AZURE_COGNTIVE_SEARCH.md)
2. **🔌 MCP Server Setup**: [MCP_SERVER_SETUP.md](MCP_SERVER_SETUP.md)

**Note**: Requires Azure account, API keys, ongoing cloud costs, and data leaves your machine. 2. **🔌 MCP Server Setup**: [MCP_SERVER_SETUP.md](MCP_SERVER_SETUP.md)

**Benefits**: Zero cloud costs, complete privacy, local processing, works offline

### 🏢 Enterprise Path: Azure Cognitive Search

1. **📄 Document Upload System**: [DOCUMENT_UPLOAD_SETUP_FOR_AZURE_COGNTIVE_SEARCH.md](DOCUMENT_UPLOAD_SETUP_FOR_AZURE_COGNTIVE_SEARCH.md)
2. **🔌 MCP Server Setup**: [MCP_SERVER_SETUP.md](MCP_SERVER_SETUP.md)

**Benefits**: Enterprise scale, cloud integration, Azure ecosystem

**Complete this FIRST** - Sets up document processing and search index:

- 📖 **[DOCUMENT_UPLOAD_SETUP_FOR_CHROMADB.md](DOCUMENT_UPLOAD_SETUP_FOR_CHROMADB.md)** - ChromaDB setup (recommended)
- 📖 **[DOCUMENT_UPLOAD_SETUP_FOR_AZURE_COGNTIVE_SEARCH.md](DOCUMENT_UPLOAD_SETUP_FOR_AZURE_COGNTIVE_SEARCH.md)** - Azure setup (enterprise)

### 🔌 MCP Server Setup

**Complete this SECOND** - Integrates with VS Code for AI-powered search:

- 📖 **[MCP_SERVER_SETUP.md](MCP_SERVER_SETUP.md)** - Complete setup guide
- Requires completed document upload setup as prerequisite

### Quick Prerequisites Check

**For ChromaDB (Recommended):**

- Python 3.8+
- Documentation directory with files organized by context
- VS Code (for MCP integration)

**For Azure Cognitive Search (Enterprise):**

- Python 3.8+
- Azure Cognitive Search service (Basic tier+)
- Azure OpenAI service with text-embedding-ada-002
- Documentation directory with files organized by context
- VS Code (for MCP integration)

### Installation

**Choose your vector search engine and follow the appropriate setup guide:**

1. **📄 ChromaDB Document Upload** (Recommended): See [DOCUMENT_UPLOAD_SETUP_FOR_CHROMADB.md](DOCUMENT_UPLOAD_SETUP_FOR_CHROMADB.md)

   - Local vector search setup
   - Environment configuration
   - Document indexing with zero cloud costs

2. **📄 Azure Document Upload** (Enterprise): See [DOCUMENT_UPLOAD_SETUP_FOR_AZURE_COGNTIVE_SEARCH.md](DOCUMENT_UPLOAD_SETUP_FOR_AZURE_COGNTIVE_SEARCH.md)

   - Azure services setup
   - Cloud environment configuration
   - Enterprise document indexing

3. **🔌 MCP Server Integration**: See [MCP_SERVER_SETUP.md](MCP_SERVER_SETUP.md)
   - VS Code MCP configuration (works with either vector search engine)
   - Server integration
   - Testing and usage

## 🎯 Usage

### Part 1: Document Processing & Upload

**First, set up your search index and upload documents:**

**For ChromaDB (Recommended):**

1. **Upload your documents:**
   ```bash
   python src/document_upload/personal_documentation_assistant_scripts/chroma_db_scripts/upload_with_pipeline.py
   ```

**For Azure Cognitive Search (Enterprise):**

1. **Set up the search index:**

   ```bash
   python src/document_upload/common_scripts/azure_cogntive_search_scripts/create_index.py
   ```

2. **Upload your documents:**
   ```bash
   python src/document_upload/personal_documentation_assistant_scripts/azure_cognitive_search_scripts/upload_with_pipeline.py
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

**ChromaDB Commands (Recommended):**

**Document Processing:**

- `python src/document_upload/personal_documentation_assistant_scripts/chroma_db_scripts/upload_with_pipeline.py <path>` - Process and index all documentation from specified path
- `python src/document_upload/personal_documentation_assistant_scripts/chroma_db_scripts/upload_with_pipeline.py <path> --dry-run` - Preview what will be processed without uploading
- `python src/document_upload/personal_documentation_assistant_scripts/chroma_db_scripts/upload_with_pipeline.py <path> --force-reset` - Delete all documents and tracker, then reprocess everything
- `python src/document_upload/personal_documentation_assistant_scripts/chroma_db_scripts/upload_with_custom_metadata.py <path> --metadata '{"title": "Custom Title", "tags": "tag1,tag2", "category": "reference", "work_item_id": "PROJ-123"}'` - Upload with custom metadata override

**Document Processing with Logging:**

- `python src/document_upload/personal_documentation_assistant_scripts/chroma_db_scripts/upload_with_pipeline.py <path> --log-file` - Upload with auto-generated IST timestamp log file
- `python src/document_upload/personal_documentation_assistant_scripts/chroma_db_scripts/upload_with_pipeline.py <path> --log-file "custom.log"` - Upload with custom log file name
- `python src/document_upload/personal_documentation_assistant_scripts/chroma_db_scripts/upload_with_pipeline.py <path> --verbose --log-file` - Verbose upload with comprehensive logging

**Document Management:**

- `python src/document_upload/personal_documentation_assistant_scripts/chroma_db_scripts/delete_by_context_and_filename.py <context_name>` - Delete all documents for a specific context
- `python src/document_upload/personal_documentation_assistant_scripts/chroma_db_scripts/delete_by_context_and_filename.py <context_name> <filename> --preview` - Preview deletion before execution
- `python src/document_upload/personal_documentation_assistant_scripts/chroma_db_scripts/delete_by_context_and_filename.py <context_name> <filename> --log-file` - Delete with auto-generated audit log
- `python src/document_upload/personal_documentation_assistant_scripts/chroma_db_scripts/delete_by_context_and_filename.py <context_name> <filename> --dry-run --log-file "audit.log"` - Preview deletion with custom audit log

**Azure Cognitive Search Commands (Enterprise):**

**System Setup & Verification:**

- `python src/document_upload/common_scripts/azure_cogntive_search_scripts/create_index.py` - Create Azure Search index with vector capabilities

**Document Processing:**

- `python src/document_upload/personal_documentation_assistant_scripts/azure_cognitive_search_scripts/upload_with_pipeline.py <path>` - Process and index all documentation from specified path
- `python src/document_upload/personal_documentation_assistant_scripts/azure_cognitive_search_scripts/upload_with_pipeline.py <path> --dry-run` - Preview what will be processed without uploading
- `python src/document_upload/personal_documentation_assistant_scripts/azure_cognitive_search_scripts/upload_with_pipeline.py <path> --force-reset` - Delete all documents and tracker, then reprocess everything
- `python src/document_upload/personal_documentation_assistant_scripts/azure_cognitive_search_scripts/upload_with_custom_metadata.py <path> --metadata '{"title": "Custom Title", "tags": "tag1,tag2", "category": "reference", "work_item_id": "PROJ-123"}'` - Upload with custom metadata override

**Document Management:**

- `python src/document_upload/personal_documentation_assistant_scripts/azure_cognitive_search_scripts/delete_by_context_and_filename.py <context_name>` - Delete all documents for a specific context

**Testing:**

Test your configuration by running document processing in dry-run mode and starting the MCP server.

#### MCP Server Commands (🔌)

**Server Management:**

- `python run_mcp_server.py` - Start the MCP server for VS Code integration
- Configure VS Code MCP integration using `.vscode/mcp.json` file

**Available MCP Tools (use in VS Code Copilot):**

**5 Universal ChromaDB Tools:**

- `mcp_documentation_chromadb_search_documents` - Semantic vector search with comprehensive metadata filtering
- `mcp_documentation_chromadb_get_document_content` - Retrieve complete document content from ChromaDB
- `mcp_documentation_chromadb_get_document_contexts` - Discover available contexts with document statistics
- `mcp_documentation_chromadb_explore_document_structure` - Navigate ChromaDB collection structure and chunks
- `mcp_documentation_chromadb_get_index_summary` - ChromaDB collection health, statistics, and overview

**All tools provide:**

- ✅ **Local Storage** - Documents stored locally in ChromaDB
- ✅ **Enterprise Search** - High-quality semantic understanding
- ✅ **Fast Response** - Local vector search with optimized performance
- ✅ **Rich Metadata** - Context, tags, categories, file types, and custom metadata
- ✅ **Semantic Understanding** - Advanced AI-powered similarity matching

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

**For ChromaDB (Recommended - Minimal Configuration):**

```env
# Required: Local Documentation Path
PERSONAL_DOCUMENTATION_ROOT_DIRECTORY=C:\Users\YourName\Desktop\Documentation

```

**For Azure Cognitive Search (Enterprise):**

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

```

### Environment Setup Tips

**For ChromaDB:**

1. **Documentation Path**: Use absolute path with proper Windows path format
2. **ChromaDB Path**: Default `./chromadb_data` works well, no changes needed
3. **Embedding Model**: Local Sentence Transformers model, downloaded automatically

**For Azure:**

1. **Azure OpenAI**: Ensure your deployment name matches `EMBEDDING_DEPLOYMENT`
2. **Search Service**: Use the admin key (not query key) for document uploads
3. **Documentation Path**: Use absolute path with proper Windows path format
4. **Index Name**: Will be created automatically if it doesn't exist

## 📋 Script Logging and Audit Trail

### Comprehensive Operation Logging

All ChromaDB scripts now support detailed logging for operations tracking, compliance, and troubleshooting:

#### Automatic Logging with IST Timestamps

```bash
# Upload with auto-generated log file (IST timestamp)
python src/document_upload/personal_documentation_assistant_scripts/chroma_db_scripts/upload_with_pipeline.py "docs/" --log-file

# Delete with auto-generated log file (IST timestamp)
python src/document_upload/personal_documentation_assistant_scripts/chroma_db_scripts/delete_by_context_and_filename.py "PROJECT-123" "file.md" --log-file
```

#### Custom Log Files

```bash
# Upload with custom log file name (stored in ScriptExecutionLogs/)
python src/document_upload/personal_documentation_assistant_scripts/chroma_db_scripts/upload_with_pipeline.py "docs/" --log-file "weekly_batch.log"

# Absolute path for custom log location
python src/document_upload/personal_documentation_assistant_scripts/chroma_db_scripts/upload_with_pipeline.py "docs/" --log-file "C:\Logs\production.log"
```

#### Production-Ready Logging Features

- **📁 Auto-Directory Creation**: `ScriptExecutionLogs/` directory created automatically
- **🕐 IST Timestamps**: All operations timestamped with India Standard Time
- **📊 Dual Output**: Simultaneous console and file logging for immediate feedback
- **🔍 Complete Audit Trail**: Full operation history with timing, success rates, and error details
- **📝 Smart Naming**: Auto-generated files use format: `{script}_{YYYYMMDD}_{HHMMSS}_IST.log`

#### Log File Examples

```
ScriptExecutionLogs/
├── upload_with_pipeline_20250831_143022_IST.log        # Auto-generated upload log
├── delete_by_context_and_filename_20250831_143125_IST.log  # Auto-generated deletion log
├── weekly_batch.log                                    # Custom named log
└── production_audit.log                                # Custom operation log
```

**Best Practices for Production Use:**

- Always use `--log-file` for production operations
- Use descriptive custom log names for important operations
- Review logs for performance insights and error patterns
- Archive old logs periodically to maintain disk space

## 🧪 Testing

### Test Document Upload System (📄)

**For ChromaDB (Recommended):**

```bash
# Test document processing with pipeline
python src/document_upload/personal_documentation_assistant_scripts/chroma_db_scripts/upload_with_pipeline.py "path/to/your/docs" --dry-run
```

**For Azure Cognitive Search (Enterprise):**

```bash
# Create the search index
python src/document_upload/common_scripts/azure_cogntive_search_scripts/create_index.py

# Test document processing with pipeline
python src/document_upload/personal_documentation_assistant_scripts/azure_cognitive_search_scripts/upload_with_pipeline.py "path/to/your/docs" --dry-run
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
4. **Embedding Generation**: Creates vector embeddings using:
   - **ChromaDB**: Local Sentence Transformers (all-MiniLM-L6-v2)
   - **Azure**: Azure OpenAI (text-embedding-ada-002)
5. **Index Storage**: Stores documents and vectors in chosen search engine
6. **File Tracking**: Uses `DocumentProcessingTracker` for idempotent processing

### Part 2: MCP Server for VS Code (🔌)

1. **MCP Protocol**: Provides Model Context Protocol interface for VS Code
2. **Search Engine**: Handles text, vector, and hybrid search queries (auto-detects ChromaDB vs Azure)
3. **Context Retrieval**: Finds relevant documentation for AI assistant
4. **Tool Exposure**: Exposes search tools to VS Code agent mode
5. **Result Formatting**: Formats search results for optimal AI consumption

### Shared Components

- **Vector Search Services**: Abstracted interface supporting both ChromaDB and Azure
- **Embedding Services**: Local or cloud embedding generation
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
- **📋 Operation Logging**: Complete audit trails with IST timestamps for production monitoring and compliance

## 🤝 Contributing

1. Follow the existing code structure
2. Add tests for new features
3. Update documentation as needed
4. Use proper error handling

## 🐛 Troubleshooting

### Common Issues

- **"Failed to connect to ChromaDB"**: Check ChromaDB installation and `CHROMADB_PATH`
- **"Failed to connect to Azure OpenAI"**: Check your Azure OpenAI endpoint and key (Azure users only)
- **"Search service connection failed"**: Verify Azure Search service name and key (Azure users only)
- **"No documentation found"**: Ensure PERSONAL_DOCUMENTATION_ROOT_DIRECTORY points to correct directory
- **"MCP server not connecting"**: Check VS Code MCP configuration paths
- **"Embedding generation issues"**: Verify cloud service configuration and connectivity

---

## 🛠️ Document Management

Use the utility scripts for document lifecycle management:

**Current ChromaDB Scripts (PRIMARY):**

```bash
# Check what documents exist for a context
python src/document_upload/personal_documentation_assistant_scripts/chroma_db_scripts/delete_by_context_and_filename.py <context_name> --dry-run

# Clean up specific context documents
python src/document_upload/personal_documentation_assistant_scripts/chroma_db_scripts/delete_by_context_and_filename.py <context_name>
```

## 🆘 Support & Troubleshooting

### Current Support (ChromaDB)

1. **For ChromaDB issues**: Check local ChromaDB installation and embedding model downloads
2. **Performance**: Verify local SSD storage and sufficient RAM (minimum 4GB recommended)
3. Use `--dry-run` flag with upload scripts to test configuration
4. Review log files in `ScriptExecutionLogs/` for detailed error messages
5. **No index management needed** - ChromaDB collections are managed automatically

### Legacy Support (Azure - Reference Only)

- Azure scripts are maintained for reference but not actively supported
- For historical Azure issues: Check Azure service connections in `.env` file
- Use `create_index.py` script to recreate Azure search index if needed

---

## 📚 Documentation Structure

| Document                                                                                                     | Purpose                            | Status               |
| ------------------------------------------------------------------------------------------------------------ | ---------------------------------- | -------------------- |
| **README.md**                                                                                                | Project overview and current setup | ✅ **CURRENT**       |
| **[DOCUMENT_UPLOAD_SETUP_FOR_CHROMADB.md](DOCUMENT_UPLOAD_SETUP_FOR_CHROMADB.md)**                           | ChromaDB setup guide               | ✅ **PRIMARY GUIDE** |
| **[MCP_SERVER_SETUP.md](MCP_SERVER_SETUP.md)**                                                               | MCP server configuration           | ✅ **CURRENT**       |
| **[02-Architecture-with-chromadb-local-embeddings.md](02-Architecture-with-chromadb-local-embeddings.md)**   | Technical architecture             | ✅ **CURRENT**       |
| **[CHROMADB_DATA_VIEWING_GUIDE.md](CHROMADB_DATA_VIEWING_GUIDE.md)**                                         | Data inspection tools              | ✅ **CURRENT**       |
| **[DOCUMENT_UPLOAD_SETUP_FOR_AZURE_COGNTIVE_SEARCH.md](DOCUMENT_UPLOAD_SETUP_FOR_AZURE_COGNTIVE_SEARCH.md)** | Azure setup guide                  | 📚 **LEGACY**        |
| **[01-Architecture-with-azure-cognitive-search.md](01-Architecture-with-azure-cognitive-search.md)**         | Azure architecture                 | 📚 **LEGACY**        |

**Legend**: ✅ = Current/Active | 📚 = Legacy/Reference

---

**The Personal Documentation Assistant MCP Server has successfully achieved its vision:**

### 🎯 Core Achievements

- ✅ **100% Local Processing** - Complete privacy with zero external dependencies
- ✅ **Zero Ongoing Costs** - No cloud services, API keys, or subscription fees
- ✅ **Enterprise Performance** - Sub-100ms search with local ChromaDB and Sentence Transformers
- ✅ **VS Code Integration** - 5 universal MCP tools for seamless developer experience
- ✅ **Production Ready** - Comprehensive testing, documentation, and utility scripts

### 🔒 Privacy & Security

- **Data Sovereignty**: All documents and processing remain on your machine
- **No External Transmission**: Zero data sent to external services or APIs
- **Offline Capable**: Works completely without internet after initial setup
- **Audit Trail**: Complete local logging and activity tracking

### 💰 Cost Efficiency

- **Zero Cloud Costs**: No Azure subscriptions or OpenAI API usage
- **One-Time Setup**: Install once, use forever with no recurring fees
- **Resource Efficient**: Optimized for local hardware with minimal system requirements

### 🛠️ Developer Experience

- **Simple Setup**: Easy installation with clear documentation
- **VS Code Native**: Seamless integration with GitHub Copilot
- **Semantic Search**: Intelligent document discovery using natural language
- **Flexible Architecture**: Extensible design for future enhancements

**This architecture demonstrates that enterprise-grade AI-powered document search can be achieved locally, privately, and cost-effectively without sacrificing performance or functionality.**

---

_Get started with the [ChromaDB Setup Guide](DOCUMENT_UPLOAD_SETUP_FOR_CHROMADB.md) and experience intelligent document search with complete privacy and zero costs!_

## 📝 License

This project is for internal use and documentation purposes.

---

**Made with ❤️ for efficient documentation retrieval**
