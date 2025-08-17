# MCP Server Setup Guide 🔌

Complete setup guide for the **MCP Server for VS Code Integration** component.

## 🎯 What This Component Does

The MCP Server provides intelligent search capabilities directly within VS Code through the Model Context Protocol. It exposes tools that allow VS Code's AI assistant to search and retrieve information from your indexed documentation.

## ⚠️ Prerequisites

**IMPORTANT**: You must complete the [Document Upload Setup](DOCUMENT_UPLOAD_SETUP.md) FIRST before setting up the MCP server. The MCP server requires an existing search index with your documentation.

### Required

- **Document Upload System** already set up and working
- **VS Code** with MCP support
- **Python environment** from Document Upload setup

### Verify Prerequisites

Run this to ensure your document index is ready:

```bash
python -c "
import sys; sys.path.append('src')
from common.azure_cognitive_search import get_azure_search_service
search_svc = get_azure_search_service()
doc_count = search_svc.get_document_count()
contexts = search_svc.get_unique_field_values('context_name')
if doc_count > 0:
    print(f'✅ Ready! Found {doc_count} indexed documents across {len(contexts)} contexts')
    print(f'📋 Sample contexts: {list(contexts)[:5]}...')
else:
    print('❌ No documents found. Complete Document Upload Setup first.')
"
```

**Expected Output**: `✅ Ready! Found [N] indexed documents across [M] contexts`

If you see 0 documents, run the upload command:

```bash
python src\document_upload\personal_documentation_assistant_scripts\upload_with_pipeline.py
```

## 🚀 MCP Server Setup

### Step 1: Test MCP Server

First, verify the MCP server can start and connect to your search index:

```bash
# Activate your virtual environment (if not already active)
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# Test MCP server startup
python run_mcp_server.py
```

Expected output:

```
🚀 Starting Personal Documentation Assistant MCP Server
🔌 Testing connections...
✅ Embedding service connection successful
✅ Connected to search index: 375 documents, 22 contexts
🎯 MCP Server ready for connections
🛠️  Available tools: 4 (search_documents, get_document_contexts, explore_document_structure, get_index_summary)
```

If successful, press `Ctrl+C` to stop the test server.

### Step 2: VS Code MCP Configuration

VS Code has built-in support for MCP servers starting from version 1.102. You configure MCP servers using a `.vscode/mcp.json` file in your workspace or in your user configuration.

#### Option 1: Local Workspace Configuration (Recommended)

For this specific project, create a `.vscode` folder at the project root and add a `mcp.json` file:

1. **Create the .vscode directory** in your project root:

   ```
   DocumentationRetrievalMCPServer/
   ├── .vscode/
   │   └── mcp.json
   ├── src/
   ├── docs/
   └── ...
   ```

2. **Create `.vscode/mcp.json`** with this exact configuration:

```json
{
  "servers": {
    "documentation-assistant": {
      "type": "stdio",
      "command": "C:\\Users\\aayushalok\\OneDrive - Microsoft\\Desktop\\Personal Projects\\DocumentationRetrievalMCPServer\\venv\\Scripts\\python.exe",
      "args": [
        "C:\\Users\\aayushalok\\OneDrive - Microsoft\\Desktop\\Personal Projects\\DocumentationRetrievalMCPServer\\run_mcp_server.py"
      ],
      "cwd": "C:\\Users\\aayushalok\\OneDrive - Microsoft\\Desktop\\Personal Projects\\DocumentationRetrievalMCPServer",
      "env": {
        "PYTHONPATH": "C:\\Users\\aayushalok\\OneDrive - Microsoft\\Desktop\\Personal Projects\\DocumentationRetrievalMCPServer\\src"
      }
    }
  }
}
```

This configuration:

- Uses the exact Python executable from your virtual environment
- Points to the correct `run_mcp_server.py` script
- Sets the working directory to your project root
- Configures PYTHONPATH to find the src modules

#### Option 2: Generic Workspace Configuration

Create a `.vscode/mcp.json` file in your project root:

```json
{
  "servers": {
    "documentation-assistant": {
      "type": "stdio",
      "command": "python",
      "args": ["run_mcp_server.py"],
      "cwd": "${workspaceFolder}",
      "env": {
        "PYTHONPATH": "${workspaceFolder}/src"
      }
    }
  }
}
```

This configuration:

- Uses your current Python environment (make sure virtual environment is activated)
- Runs the MCP server from your workspace folder
- Sets up proper Python path for imports

#### Option 3: User Configuration (Global)

For global availability across all workspaces, run the command:

```
MCP: Open User Configuration
```

From VS Code Command Palette (`Ctrl+Shift+P`) and add:

```json
{
  "servers": {
    "documentation-assistant": {
      "type": "stdio",
      "command": "C:\\path\\to\\your\\venv\\Scripts\\python.exe",
      "args": ["run_mcp_server.py"],
      "cwd": "C:\\Users\\aayushalok\\OneDrive - Microsoft\\Desktop\\Personal Projects\\DocumentationRetrievalMCPServer",
      "env": {
        "PYTHONPATH": "C:\\Users\\aayushalok\\OneDrive - Microsoft\\Desktop\\Personal Projects\\DocumentationRetrievalMCPServer\\src"
      }
    }
  }
}
```

**❗ Important**: Update the paths to match your actual project location and Python environment.

### Step 3: Verify MCP Server Integration

After setting up the MCP configuration:

1. **Restart VS Code** completely to load the new MCP server configuration
2. **Check MCP Server Status**:

   - Run `MCP: List Servers` from Command Palette (`Ctrl+Shift+P`)
   - Your "documentation-assistant" server should appear in the list
   - Check that the status shows as "Running" or "Connected"

3. **View Available Tools**:
   - Open Chat view (`Ctrl+Alt+I`)
   - Switch to **Agent** mode from the dropdown
   - Click the **Tools** button to see available MCP tools
   - You should see **4 tools**: `search_documents`, `get_document_contexts`, `explore_document_structure`, `get_index_summary`

### Step 4: Test GitHub Copilot Integration

GitHub Copilot Chat in VS Code will automatically detect and use your MCP tools when in **Agent Mode**.

#### Method 1: Using Agent Mode

1. Open GitHub Copilot Chat (`Ctrl+Alt+I`)
2. **Select "Agent" mode** from the chat mode dropdown
3. Try these test queries:

```
List all my available documentation contexts
→ Uses get_document_contexts tool
```

```
Search for documents related to authentication
→ Uses search_documents with "authentication" query
```

```
Show me documentation about API integration from my documents
→ Uses search_documents with hybrid search for "API integration"
```

```
Give me an overview of my documentation index
→ Uses get_index_summary for comprehensive statistics
```

```
Show me the structure of my documentation
→ Uses explore_document_structure for navigation assistance
```

#### Method 2: Direct Tool Reference

You can directly reference MCP tools in any chat mode:

```
#search_documents search for "testing" in my documentation
```

```
#get_index_summary show me an overview of my documentation
```

## 🔧 Available MCP Tools

Once integrated with VS Code, GitHub Copilot can use these **4 universal tools** in Agent mode:

### Universal Search Tool (1)

- **`search_documents`**: Multi-modal universal search across all documentation

  - Supports text, vector, semantic, and hybrid search modes
  - Context filtering and flexible result count control
  - Max results: 50 (default: 5)
  - Best for: All types of searches across your entire documentation base
  - Advanced filters: context, category, file type, tags

### Documentation Discovery Tools (3)

- **`get_document_contexts`**: List all available documentation contexts

  - Discover what contexts/projects are indexed
  - Includes statistics per context
  - Max contexts: 1000 (default: 100)
  - Best for: Understanding your documentation organization

- **`explore_document_structure`**: Navigate documentation hierarchy

  - Explore contexts, files, chunks, and categories
  - Structured navigation assistance
  - Max items: 200 (default: 50)
  - Best for: Understanding document structure and finding specific files

- **`get_index_summary`**: Comprehensive documentation statistics
  - Complete overview of indexed documentation
  - Document counts, contexts, categories, file types
  - Facet distributions and search capabilities
  - Best for: System overview and health monitoring

## 📝 Example Usage with GitHub Copilot

### Basic Queries

```
"List all available documentation contexts"
→ Uses get_document_contexts tool

"What documentation deals with authentication?"
→ Uses search_documents tool with query "authentication"

"Show me information about my documentation structure"
→ Uses explore_document_structure tool

"Give me a summary of my documentation"
→ Uses get_index_summary tool
```

### Advanced Search Queries

```
"Find documents similar to database connectivity issues"
→ Uses search_documents with semantic search mode

"Search for API integration examples in my documentation"
→ Uses search_documents with hybrid search (default)

"What testing approaches are documented across contexts?"
→ Uses search_documents with broad query scope

"Show me error handling patterns from my documentation"
→ Uses search_documents with semantic search for concept discovery
```

### Document Navigation Queries

```
"Show me all contexts in my documentation"
→ Uses get_document_contexts for complete overview

"What file types do I have in my documentation?"
→ Uses get_index_summary to show file type distribution

"Find documents related to setup and configuration"
→ Uses search_documents with category filtering

"Show me documentation from a specific project context"
→ Uses search_documents with context filtering
```

### Context-Specific Queries

```
"What documentation exists for Project-A?"
→ Uses search_documents with context filter

"Find all API-related content in my documentation"
→ Uses search_documents with category or tag filtering

"Show me setup instructions from any context"
→ Uses search_documents for cross-context search
```

## 🧪 Testing GitHub Copilot Integration

### Test 1: MCP Server Connection

Check that your MCP server is properly connected:

```
MCP: List Servers
```

From Command Palette - your server should show as "Running"

### Test 2: Tool Availability

In GitHub Copilot Chat (Agent mode):

1. Click the **Tools** button
2. Search for "document" - you should see your documentation tools listed
3. Enable the tools you want to use

### Test 3: Basic Functionality Test

In GitHub Copilot Chat:

```
"Please use the get_index_summary tool to show me information about my documentation."
```

Expected response should include:

- Total number of contexts (e.g., 22)
- Total number of documents (e.g., 375)
- Search index name: documentation-index
- Document categories and file types
- Context names and distribution

### Test 4: Search Test

```
"Search my documentation for content about 'testing' or 'quality assurance'"
```

Expected response should include:

- Relevant document excerpts from various contexts
- Context names (like Project-A, Research-B)
- File paths and metadata
- Relevance scores
- Usage suggestions for additional searches

### Test 5: Context Discovery Test

```
"Show me all available documentation contexts"
```

Expected response should include:

- Complete list of contexts with statistics
- Document counts per context
- Suggestions for exploring specific contexts

### Test 6: Structure Exploration Test

```
"Show me the structure of my documentation index"
```

Expected response should include:

- File types and categories
- Context organization
- Navigation suggestions

## 🔄 Using the MCP Server with VS Code

### Automatic Operation

- MCP server runs **automatically** when GitHub Copilot needs it (Agent mode)
- No need to manually start for normal usage
- VS Code manages the MCP server lifecycle

### Manual Testing

For testing purposes, you can manually start the server:

```bash
# Activate virtual environment
venv\Scripts\activate  # Windows

# Test MCP server
python run_mcp_server.py
```

### Monitoring and Debugging

Monitor MCP server status and logs:

1. **MCP Server List**: Run `MCP: List Servers` from Command Palette
2. **Server Logs**: Right-click server → "Show Output" to view logs
3. **Developer Console**: Help → Toggle Developer Tools → Console for VS Code logs

## 🐛 Troubleshooting

### "MCP server not connecting"

**Check MCP Configuration:**

- Verify `.vscode/mcp.json` file exists and has correct JSON syntax
- Ensure Python path and working directory are correct
- Check that `.env` file exists with proper Azure configuration

**Common Solutions:**

- Use absolute paths for Python executable and working directory
- Ensure virtual environment contains all required dependencies
- Restart VS Code after configuration changes
- Check MCP server logs via `MCP: List Servers` → "Show Output"

### "No tools available" in Agent mode

- Verify MCP server is running via `MCP: List Servers`
- Check that tools are enabled in Agent mode Tools picker
- Ensure GitHub Copilot has required permissions

### "Module not found" errors

- Verify virtual environment has all required packages:
  ```bash
  pip list | findstr "azure-search-documents openai python-dotenv"
  ```
- Check that `PYTHONPATH` is set correctly in MCP configuration

### "No documentation found" in responses

- Verify Document Upload System is working:
  ```bash
  python src\document_upload\common_scripts\verify_document_upload_setup.py
  ```
- Check Azure Cognitive Search index contains documents
- Ensure environment variables are properly configured

### Performance Tips

### Optimal Query Types

- **Text search**: Exact keywords, specific terms, precise matches
- **Vector search**: Conceptual queries, natural language questions
- **Semantic search**: "Find similar" and related concept discovery
- **Hybrid search**: Comprehensive search combining all approaches (default)

### Response Management

- Use `max_results` parameter to control response size (up to 50)
- Be specific in queries for better relevance and focused results
- Use context filtering for targeted searches within specific projects
- Use category and tag filters for organized searches
- Combine tools for comprehensive analysis (contexts → search → structure)

### Tool Selection Strategy

- **General discovery**: `search_documents` with hybrid search (default)
- **Context exploration**: `get_document_contexts` for overview
- **Targeted investigation**: `search_documents` with context filtering
- **Structure understanding**: `explore_document_structure` for navigation
- **System overview**: `get_index_summary` for comprehensive statistics

## ✅ Success Checklist

- [ ] Document Upload System is working (prerequisite)
- [ ] MCP server starts without errors (`python run_mcp_server.py`)
- [ ] `.vscode/mcp.json` configuration file created
- [ ] VS Code restarted after configuration
- [ ] MCP server appears as "Running" in `MCP: List Servers`
- [ ] Documentation tools visible in GitHub Copilot Agent mode Tools list
- [ ] Test queries return expected results from your documentation
- [ ] GitHub Copilot can successfully use all 4 universal documentation tools
- [ ] Context discovery and structure exploration work properly
- [ ] Search filtering and advanced queries function properly

## 🔗 GitHub Copilot Integration Examples

### Code Context Queries

```
"Based on my documentation, what patterns do we use for error handling?"
→ Uses search_documents to find error handling concepts across contexts

"Find examples of database integration approaches from documented projects"
→ Uses search_documents with "database integration" query

"What security considerations are mentioned across my documentation?"
→ Uses search_documents with "security" + semantic search for comprehensive coverage

"Show me authentication implementation details from Project-A"
→ Uses search_documents with context filtering for targeted search
```

### Project Planning Queries

```
"What contexts contain similar functionality to what I'm currently working on?"
→ Uses search_documents with semantic search using current context description

"Show me lessons learned from previous project documentation"
→ Uses search_documents filtered to specific categories or tags

"Find documentation that deals with performance optimization"
→ Uses search_documents with semantic search for "performance optimization" concepts

"Get detailed setup instructions from completed projects"
→ Uses search_documents with category filtering for comprehensive setup documentation
```

### Architecture and Design Queries

```
"How did we approach authentication in previous projects?"
→ Uses search_documents with comprehensive search for authentication patterns

"What API design patterns appear most frequently in our documentation?"
→ Uses search_documents with "API design" query across all contexts

"Find documentation about integration with external services"
→ Uses search_documents with semantic search for "external integration" concepts

"Show me the complete architecture documentation from my main project"
→ Uses search_documents with context filtering + category filtering for detailed exploration
```

### Document Exploration Queries

```
"Walk me through the setup process step by step"
→ Uses search_documents with category filtering for setup documentation

"Find all troubleshooting information across my documentation"
→ Uses search_documents with semantic search for comprehensive troubleshooting

"Show me the complete documentation structure for my largest context"
→ Uses get_document_contexts + explore_document_structure + search_documents for exploration

"What file types and categories do I have in my documentation?"
→ Uses get_index_summary for comprehensive structure analysis
```

---

**🔌 MCP Server is now integrated with VS Code and GitHub Copilot!** You can now ask GitHub Copilot questions about your documentation using Agent mode with access to **4 universal search and navigation tools** for comprehensive document exploration and analysis.
