# Work Item Documentation Retriever

A powerful document retrieval system for Work Items using Azure Cognitive Search with vector search capabilities and AI-powered embeddings.

## 🚀 Features

- **Vector Search**: AI-powered semantic search using Azure OpenAI embeddings
- **Document Processing**: Automatic processing of Markdown files with frontmatter support
- **Intelligent Chunking**: Smart text chunking for optimal search performance
- **Work Item Integration**: Seamless integration with Work Items directory structure
- **Interactive Search**: Command-line interface for easy querying

## 📁 Project Structure

```
WorkItemDocumentationRetriever/
├── main.py                 # Main entry point with CLI interface
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
   cp config/.env.example .env
   # Edit .env with your Azure credentials and paths
   ```

## 🎯 Usage

### Quick Start

1. **Set up the search index:**

   ```bash
   python main.py setup
   ```

2. **Upload your documents:**

   ```bash
   python main.py upload
   ```

3. **Search your documents:**

   ```bash
   python main.py search "your search query"
   ```

4. **Interactive mode:**
   ```bash
   python main.py interactive
   ```

### Command Reference

- `python main.py setup` - Create Azure Search index with vector capabilities
- `python main.py upload` - Process and index all Work Items documents
- `python main.py search "<query>"` - Perform a single search query
- `python main.py interactive` - Start interactive search session

### Example Queries

```bash
# Search for specific topics
python main.py search "authentication implementation"

# Find work items by type
python main.py search "bug fixes security"

# Search for code examples
python main.py search "API integration examples"
```

## 🔧 Configuration

The system uses environment variables for configuration. Copy `config/.env.example` to `.env` and configure:

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

Run individual test files from the `tests/` directory:

```bash
python tests/test_full_upload.py
python tests/test_vector_formats.py
```

## 📊 Architecture

The system consists of several key components:

1. **Document Processor**: Extracts content and metadata from Markdown files
2. **Embedding Generator**: Creates vector embeddings using Azure OpenAI
3. **Search Index**: Stores documents and vectors in Azure Cognitive Search
4. **Query Engine**: Handles both text and semantic search queries

## 🔍 Search Features

- **Semantic Search**: AI-powered understanding of query intent
- **Vector Search**: Find conceptually similar documents
- **Metadata Filtering**: Filter by work item ID, tags, file paths
- **Hybrid Search**: Combines text and vector search for best results

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

## 📝 License

This project is for internal use and documentation purposes.

---

**Made with ❤️ for efficient Work Item documentation retrieval**
