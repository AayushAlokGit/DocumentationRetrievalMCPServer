# MCP Server Setup Guide 🔌

Sets up Model Context Protocol (MCP) server integration with VS Code, enabling GitHub Copilot to access your documentation through **5 universal tools** with **100% local ChromaDB processing**.

## ⚠️ Prerequisites

**Complete ChromaDB document upload setup first** - you need indexed documents in your local ChromaDB collection.

**Current Architecture**: **ChromaDB + Local Embeddings (100% Local)**

- **Primary Setup**: [ChromaDB Setup](DOCUMENT_UPLOAD_SETUP_FOR_CHROMADB.md) - Complete privacy, zero costs, local processing
- **Legacy Reference**: [Azure Setup](DOCUMENT_UPLOAD_SETUP_FOR_AZURE_COGNTIVE_SEARCH.md) - Deprecated, cloud-based

**Required:**

- Completed ChromaDB document upload setup with indexed documents
- VS Code with GitHub Copilot extension
- Active virtual environment with ChromaDB dependencies installed

**Quick Verification - ChromaDB Local Setup:**

```bash
# Activate environment and verify documents are indexed locally
.venv\Scripts\activate

# Check ChromaDB collection status
python -c "
from src.common.vector_search_services.chromadb_service import get_chromadb_service
search_service = get_chromadb_service()
count = search_service.get_document_count()
print('✅ Ready - ChromaDB with', count, 'documents' if count > 0 else '❌ No documents - run ChromaDB upload setup first')
"

# Verify local embedding service
python -c "
from src.common.embedding_services.embedding_service_factory import get_embedding_generator
embedder = get_embedding_generator()
if embedder.test_connection():
    print('✅ Local embeddings ready')
else:
    print('❌ Embedding service issue')
"
```

## 🚀 Setup Steps

### 1. Test MCP Server (ChromaDB Backend)

```bash
# Test server startup with ChromaDB
.venv\Scripts\activate
python run_mcp_server.py

# Expected output for ChromaDB setup:
# [START] Starting Documentation Retrieval MCP Server (ChromaDB)
# [INFO] Using embedding provider: local
# [INFO] Loading local embedding model: all-MiniLM-L6-v2
# [SUCCESS] Local Embedding Service initialized: all-MiniLM-L6-v2
# [SUCCESS] Connected to ChromaDB collection: X documents
# [TARGET] MCP Server ready for VS Code integration
# [READY] 5 ChromaDB tools available

# Press Ctrl+C to stop
```

### 2. Configure VS Code MCP

Create `.vscode/mcp.json` in your workspace:

```json
{
  "servers": {
    "documentation-retrieval-mcp": {
      "type": "stdio",
      "command": "C:\\Users\\aayushalok\\OneDrive - Microsoft\\Desktop\\Personal Projects\\DocumentationRetrievalMCPServer\\venv\\Scripts\\python.exe",
      "args": [
        "C:\\Users\\aayushalok\\OneDrive - Microsoft\\Desktop\\Personal Projects\\DocumentationRetrievalMCPServer\\run_mcp_server.py"
      ],
      "cwd": "C:\\Users\\aayushalok\\OneDrive - Microsoft\\Desktop\\Personal Projects\\DocumentationRetrievalMCPServer"
    }
  }
}
```

**Update all paths** to match your actual project location and Python environment (i.e the virtual env which has all the dependency packages installed, usually this would be in project root as the "venv" folder).

**Note:** The MCP server now runs exclusively on ChromaDB with local embeddings for complete privacy and zero cloud costs.

### 3. Verify Integration

1. Restart VS Code
2. Open GitHub Copilot Chat (Ctrl+Shift+I)
3. Check VS Code output panel: **View** → **Output** → **GitHub Copilot Language Server**
4. Look for: `[INFO] Connected to MCP server documentation-retrieval-mcp`

### 4. Test Functionality

In Copilot Chat, ask:

```
"What documents are available in my local documentation index?"
```

Expected response: List of contexts/documents found in your ChromaDB collection.

## 🔧 Available Tools (5 Universal ChromaDB Tools)

The MCP server provides 5 tools to GitHub Copilot for local document operations:

1. **`mcp_documentation_chromadb_search_documents`** - Semantic vector search with metadata filtering
2. **`mcp_documentation_chromadb_get_document_content`** - Retrieve full content from ChromaDB
3. **`mcp_documentation_chromadb_get_document_contexts`** - List all available contexts with statistics
4. **`mcp_documentation_chromadb_explore_document_structure`** - Browse ChromaDB collection structure
5. **`mcp_documentation_chromadb_get_index_summary`** - Get ChromaDB collection health and statistics

**All tools operate 100% locally with:**

- ✅ **Complete Privacy** - No external API calls or data transmission
- ✅ **Fast Performance** - Local vector search with sub-100ms response times
- ✅ **Rich Metadata** - Context-aware filtering and semantic understanding
- ✅ **Zero Costs** - No cloud services or API usage fees

## 📝 Usage Examples

### Local Semantic Search

```
"Search my local documentation for authentication setup"
"Find information about ChromaDB configuration in my docs"
```

### Document Discovery

```
"What document contexts are available in my local collection?"
"Show me all files in the 'Task-5559136' context"
```

### Content Retrieval

```
"Get the full content of my BinSkim documentation"
"Show me the document about local embedding setup"
```

## 🐛 Troubleshooting

### MCP Server Not Connecting

1. Check VS Code Output panel for errors
2. Verify virtual environment is activated
3. Ensure `cwd` path in mcp.json is correct (use double backslashes)
4. Test server manually: `python run_mcp_server.py`

### No Tools Available

1. Restart VS Code completely
2. Check GitHub Copilot Chat logs in Output panel
3. Verify MCP server shows "Available tools: 5" on startup

### No Documents Found

1. Verify document upload setup is complete for your chosen vector search engine:
   - **ChromaDB**: Run ChromaDB upload scripts
   - **Azure Cognitive Search**: Run Azure upload scripts
2. Run the verification command from Prerequisites section
3. Upload documents if needed:

   ```bash
   # For ChromaDB (recommended)
   python src\document_upload\personal_documentation_assistant_scripts\chroma_db_scripts\upload_with_pipeline.py

   # For Azure Cognitive Search
   python src\document_upload\personal_documentation_assistant_scripts\azure_cognitive_search_scripts\upload_with_pipeline.py
   ```

## ✅ Success Checklist

- [ ] Document upload setup completed with indexed documents (ChromaDB or Azure)
- [ ] MCP server starts successfully showing "Available tools: 5"
- [ ] VS Code mcp.json configured with correct paths
- [ ] VS Code shows "Connected to MCP server documentation-retrieval-mcp"
- [ ] Copilot Chat can find and list documents from your vector search engine
- [ ] Search queries return relevant results

Once complete, GitHub Copilot will have access to your documentation and can answer questions using your indexed content regardless of whether you're using ChromaDB or Azure Cognitive Search.
