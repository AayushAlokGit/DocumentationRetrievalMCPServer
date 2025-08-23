# MCP Server Setup Guide 🔌

Sets up Model Context Protocol (MCP) server integration with VS Code, enabling GitHub Copilot to access your documentation through 5 universal tools.

## ⚠️ Prerequisites

**Complete the [Document Upload Setup](DOCUMENT_UPLOAD_SETUP.md) first** - you need indexed documents in Azure Cognitive Search.

**Required:**

- Completed document upload setup with indexed documents
- VS Code with GitHub Copilot extension
- Active virtual environment with dependencies installed

**Quick Verification:**

```bash
# Activate environment and verify documents are indexed
.venv\Scripts\activate
python -c "
from src.common.azure_cognitive_search import AzureCognitiveSearchService
search_service = AzureCognitiveSearchService()
result = search_service.search('*', search_type='simple', max_results=1)
print('✅ Ready' if result and len(result) > 0 else '❌ No documents - run upload setup first')
"
```

## 🚀 Setup Steps

### 1. Test MCP Server

```bash
# Test server startup
.venv\Scripts\activate
python run_mcp_server.py
# Should show: "MCP server started. Tools: 5"
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

### 3. Verify Integration

1. Restart VS Code
2. Open GitHub Copilot Chat (Ctrl+Shift+I)
3. Check VS Code output panel: **View** → **Output** → **GitHub Copilot Language Server**
4. Look for: `[INFO] Connected to MCP server documentation-retrieval-mcp`

### 4. Test Functionality

In Copilot Chat, ask:

```
"What documents are available in the documentation index?"
```

Expected response: List of contexts/documents found in your search index.

## 🔧 Available Tools

The MCP server provides 5 tools to GitHub Copilot:

1. **`search_documents`** - Search for relevant content using keywords or questions
2. **`get_document_content`** - Retrieve full content of specific documents
3. **`get_document_contexts`** - List all available document contexts/categories
4. **`explore_document_structure`** - Browse contexts, files, and document structure
5. **`get_index_summary`** - Get comprehensive statistics about the document index

## 📝 Usage Examples

### Basic Search

```
"Search for information about Azure configuration"
```

### Document Discovery

```
"What contexts are available in the documentation?"
"Show me all files in the 'architecture' context"
```

### Content Retrieval

```
"Get the full content of the setup documentation"
"Show me the document about MCP server implementation"
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
3. Verify MCP server shows "Tools: 5" on startup

### No Documents Found

1. Verify document upload setup is complete
2. Run the verification command from Prerequisites section
3. Upload documents if needed: `python src\document_upload\personal_documentation_assistant_scripts\upload_with_pipeline.py`

## ✅ Success Checklist

- [ ] Document upload setup completed with indexed documents
- [ ] MCP server starts successfully showing "Tools: 5"
- [ ] VS Code mcp.json configured with correct path
- [ ] VS Code shows "Connected to MCP server documentation-retrieval-mcp"
- [ ] Copilot Chat can find and list documents
- [ ] Search queries return relevant results

Once complete, GitHub Copilot will have access to your documentation and can answer questions using your indexed content.
