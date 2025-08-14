# MCP Server Setup Guide 🔌

Complete setup guide for the **MCP Server for VS Code Integration** component.

## 🎯 What This Component Does

The MCP Server provides intelligent search capabilities directly within VS Code through the Model Context Protocol. It exposes tools that allow VS Code's AI assistant to search and retrieve information from your indexed work item documentation.

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
work_items = search_svc.get_unique_field_values('context_id')
if doc_count > 0:
    print(f'✅ Ready! Found {doc_count} indexed documents across {len(work_items)} work items')
    print(f'📋 Sample work items: {list(work_items)[:5]}...')
else:
    print('❌ No documents found. Complete Document Upload Setup first.')
"
```

**Expected Output**: `✅ Ready! Found [N] indexed documents across [M] work items`

If you see 0 documents, run the upload command:

```bash
python src\document_upload\personal_documentation_assistant_scripts\upload_work_items.py
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
🚀 Starting Work Item Documentation MCP Server
🔌 Testing connections...
✅ Embedding service connection successful
✅ Connected to search index: 375 documents, 22 work items
🎯 MCP Server ready for connections
🛠️  Available tools: 8 (search_work_items, search_by_work_item, semantic_search, search_by_chunk, search_file_chunks, search_chunk_range, get_work_item_list, get_work_item_summary)
```

If successful, press `Ctrl+C` to stop the test server.

### Step 2: VS Code MCP Configuration

VS Code has built-in support for MCP servers starting from version 1.102. You configure MCP servers using a `.vscode/mcp.json` file in your workspace or in your user configuration.

#### Option 1: Local Workspace Configuration (Recommended)

For this specific project, create a `.vscode` folder at the project root and add a `mcp.json` file:

1. **Create the .vscode directory** in your project root:

   ```
   PersonalDocumentationAssistantMCPServer/
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
    "work-items-documentation": {
      "type": "stdio",
      "command": "C:\\Users\\aayushalok\\OneDrive - Microsoft\\Desktop\\Personal Projects\\PersonalDocumentationAssistantMCPServer\\venv\\Scripts\\python.exe",
      "args": [
        "C:\\Users\\aayushalok\\OneDrive - Microsoft\\Desktop\\Personal Projects\\PersonalDocumentationAssistantMCPServer\\run_mcp_server.py"
      ],
      "cwd": "C:\\Users\\aayushalok\\OneDrive - Microsoft\\Desktop\\Personal Projects\\PersonalDocumentationAssistantMCPServer",
      "env": {
        "PYTHONPATH": "C:\\Users\\aayushalok\\OneDrive - Microsoft\\Desktop\\Personal Projects\\PersonalDocumentationAssistantMCPServer\\src"
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
    "work-items-documentation": {
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
    "work-items-documentation": {
      "type": "stdio",
      "command": "C:\\path\\to\\your\\venv\\Scripts\\python.exe",
      "args": ["run_mcp_server.py"],
      "cwd": "C:\\Users\\aayushalok\\OneDrive - Microsoft\\Desktop\\Personal Projects\\PersonalDocumentationAssistantMCPServer",
      "env": {
        "PYTHONPATH": "C:\\Users\\aayushalok\\OneDrive - Microsoft\\Desktop\\Personal Projects\\PersonalDocumentationAssistantMCPServer\\src"
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
   - Your "work-items-documentation" server should appear in the list
   - Check that the status shows as "Running" or "Connected"

3. **View Available Tools**:
   - Open Chat view (`Ctrl+Alt+I`)
   - Switch to **Agent** mode from the dropdown
   - Click the **Tools** button to see available MCP tools
   - You should see **8 tools**: `search_work_items`, `search_by_work_item`, `semantic_search`, `search_by_chunk`, `search_file_chunks`, `search_chunk_range`, `get_work_item_list`, `get_work_item_summary`

### Step 4: Test GitHub Copilot Integration

GitHub Copilot Chat in VS Code will automatically detect and use your MCP tools when in **Agent Mode**.

#### Method 1: Using Agent Mode

1. Open GitHub Copilot Chat (`Ctrl+Alt+I`)
2. **Select "Agent" mode** from the chat mode dropdown
3. Try these test queries:

```
List all my available work items
→ Uses get_work_item_list tool
```

```
Search for work items related to authentication
→ Uses search_work_items with "authentication" query
```

```
Show me documentation about API integration from my work items
→ Uses search_work_items with hybrid search for "API integration"
```

```
Find the setup instructions in PersonalDocumentationAssistantMCPServer
→ Uses search_by_work_item for targeted search
```

```
Show me all chunks from the README.md file
→ Uses search_file_chunks for complete file content
```

#### Method 2: Direct Tool Reference

You can directly reference MCP tools in any chat mode:

```
#search_work_items search for "testing" in my documentation
```

```
#get_work_item_summary show me an overview of my work items
```

## 🔧 Available MCP Tools

Once integrated with VS Code, GitHub Copilot can use these **8 specialized tools** in Agent mode:

### Core Search Tools (3)

- **`search_work_items`**: Multi-modal search across all work item documentation

  - Supports text, vector, and hybrid search modes
  - Optional work item filtering and result count control
  - Max results: 20 (default: 5)
  - Best for: General searches across entire documentation base

- **`search_by_work_item`**: Targeted search within specific work item

  - Focuses search on single work item's documents
  - Max results: 10 (default: 5)
  - Ideal for deep-dive investigations
  - Best for: "Find X in work item Y" type queries

- **`semantic_search`**: Pure vector-based conceptual search
  - Uses AI embeddings to find conceptually similar content
  - Max results: 15 (default: 5)
  - Great for finding related topics with different wording
  - Best for: Discovering related concepts and ideas

### Chunk Navigation Tools (3)

- **`search_by_chunk`**: Precise chunk identification and retrieval

  - Search using enhanced chunk index field
  - Find specific document sections by chunk pattern
  - Best for: Locating exact document parts

- **`search_file_chunks`**: File-specific chunk retrieval

  - Get all chunks from a specific file with optional content filtering
  - Max results: 20 (default: 10)
  - Best for: Reading entire files or file sections

- **`search_chunk_range`**: Sequential chunk reading
  - Retrieve specific ranges of chunks from files
  - Max results: 20 (default: 10)
  - Best for: Reading document sections in sequence

### Information Tools (2)

- **`get_work_item_list`**: List all available work item IDs

  - Discover what work items are indexed
  - No parameters required

- **`get_work_item_summary`**: Get comprehensive statistics and overview
  - Shows total work items, documents, and index information
  - Provides complete work item list
  - No parameters required

## 📝 Example Usage with GitHub Copilot

### Basic Queries

```
"List all available work items"
→ Uses get_work_item_list tool

"What work items dealt with authentication?"
→ Uses search_work_items tool with query "authentication"

"Show me information about PersonalDocumentationAssistantMCPServer"
→ Uses search_by_work_item tool with work_item_id "PersonalDocumentationAssistantMCPServer"

"Give me a summary of my documentation"
→ Uses get_work_item_summary tool
```

### Advanced Search Queries

```
"Find work items similar to database connectivity issues"
→ Uses semantic_search tool for conceptual similarity

"Search for API integration examples in work items"
→ Uses search_work_items with hybrid search (default)

"What testing approaches were used across work items?"
→ Uses search_work_items with broad query scope

"Show me error handling patterns from completed work"
→ Uses semantic_search for concept-based discovery
```

### Document Navigation Queries

```
"Show me all sections of the README.md file"
→ Uses search_file_chunks to get all chunks from README.md

"Get the first 3 sections of the setup documentation"
→ Uses search_chunk_range with start_chunk=0, end_chunk=2

"Find the introduction section of AppDescription.md"
→ Uses search_by_chunk with chunk_pattern="AppDescription.md_chunk_0"

"Show me chunks 5-10 from the architecture document"
→ Uses search_chunk_range for specific section reading
```

### Work Item Scoped Queries

```
"What documentation exists for PersonalDocumentationAssistantMCPServer?"
→ Uses search_by_work_item for targeted search

"Find all testing-related content in Task 5215074"
→ Uses search_by_work_item with specific work item and query

"Show me setup instructions from Bug 5238380"
→ Uses search_by_work_item for scoped investigation
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
2. Search for "work" - you should see your work item tools listed
3. Enable the tools you want to use

### Test 3: Basic Functionality Test

In GitHub Copilot Chat:

```
"Please use the get_work_item_summary tool to show me information about my work item documentation."
```

Expected response should include:

- Total number of work items (e.g., 22)
- Total number of documents (e.g., 375)
- Search index name: work-items-index
- List of work item IDs (Bug numbers, Task numbers, project names)

### Test 4: Search Test

```
"Search my work items for documentation about 'testing' or 'quality assurance'"
```

Expected response should include:

- Relevant document excerpts from actual work items
- Work item IDs (like Task 5215074, PersonalDocumentationAssistantMCPServer)
- File paths and chunk information
- Relevance scores
- Usage tips for additional tools

### Test 5: Specific Work Item Test

```
"Show me all documentation for work item PersonalDocumentationAssistantMCPServer"
```

Expected response should include:

- Documents specific to that work item
- File structure and chunk navigation options
- Suggestions for using chunk-based tools for detailed exploration

### Test 6: Chunk Navigation Test

```
"Show me the first section of the MCP_SEARCH_CAPABILITIES_ANALYSIS.md file"
```

Expected response should include:

- Specific chunk content (chunk_0)
- Chunk index information
- Options for sequential reading

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
python mcp_server.py
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

### "No work items found" in responses

- Verify Document Upload System is working:
  ```bash
  python verify_document_upload_setup.py
  ```
- Check Azure Cognitive Search index contains documents
- Ensure environment variables are properly configured

### Performance Tips

### Optimal Query Types

- **Text search**: Exact keywords, specific terms, precise matches
- **Vector search**: Conceptual queries, natural language, "find similar"
- **Hybrid search**: Best of both worlds (default for most tools)
- **Chunk navigation**: Document structure exploration, sequential reading

### Response Management

- Use `max_results` parameter to limit response size (varies by tool: 10-20 max)
- Be specific in queries for better relevance and focused results
- Use work item filtering (`search_by_work_item`) for focused searches
- Use chunk tools for detailed document exploration
- Combine tools for comprehensive analysis (e.g., list → search → navigate chunks)

### Tool Selection Strategy

- **General discovery**: `search_work_items` with hybrid search
- **Targeted investigation**: `search_by_work_item` for specific work items
- **Concept exploration**: `semantic_search` for related ideas
- **Document reading**: `search_file_chunks` → `search_chunk_range` for sequential content
- **Precise location**: `search_by_chunk` for exact sections

## ✅ Success Checklist

- [ ] Document Upload System is working (prerequisite)
- [ ] MCP server starts without errors (`python mcp_server.py`)
- [ ] `.vscode/mcp.json` configuration file created
- [ ] VS Code restarted after configuration
- [ ] MCP server appears as "Running" in `MCP: List Servers`
- [ ] Work item tools visible in GitHub Copilot Agent mode Tools list
- [ ] Test queries return expected results from your documentation
- [ ] GitHub Copilot can successfully use all 8 work-items tools
- [ ] Chunk navigation tools work for document exploration
- [ ] Search filtering and scoping functions properly

## 🔗 GitHub Copilot Integration Examples

### Code Context Queries

```
"Based on my work item documentation, what patterns do we use for error handling?"
→ Uses semantic_search to find error handling concepts across work items

"Find examples of database integration approaches from completed work items"
→ Uses search_work_items with "database integration" query

"What security considerations are mentioned across work items?"
→ Uses search_work_items with "security" + semantic_search for comprehensive coverage

"Show me authentication implementation details from PersonalDocumentationAssistantMCPServer"
→ Uses search_by_work_item for targeted search
```

### Project Planning Queries

```
"What work items involved similar functionality to what I'm currently working on?"
→ Uses semantic_search with current context description

"Show me lessons learned from previous bug fix work items"
→ Uses search_work_items filtered to Bug work items

"Find work items that dealt with performance optimization"
→ Uses semantic_search for "performance optimization" concepts

"Get detailed setup instructions from completed projects"
→ Uses search_work_items + search_file_chunks for comprehensive documentation
```

### Architecture and Design Queries

```
"How did we approach authentication in previous work items?"
→ Uses search_work_items + semantic_search for comprehensive coverage

"What API design patterns appear most frequently in our documentation?"
→ Uses search_work_items with "API design" query

"Find work items that document integration with external services"
→ Uses semantic_search for "external integration" concepts

"Show me the complete architecture documentation from PersonalDocumentationAssistantMCPServer"
→ Uses search_by_work_item + search_file_chunks for detailed exploration
```

### Document Exploration Queries

```
"Walk me through the setup process step by step"
→ Uses search_file_chunks + search_chunk_range for sequential reading

"Find all troubleshooting information across work items"
→ Uses search_work_items + semantic_search for comprehensive troubleshooting

"Show me the complete documentation structure for my largest work item"
→ Uses get_work_item_list + search_by_work_item + search_file_chunks for exploration

"Get specific implementation details from chunk 5 of the analysis document"
→ Uses search_by_chunk for precise content retrieval
```

---

**🔌 MCP Server is now integrated with VS Code and GitHub Copilot!** You can now ask GitHub Copilot questions about your work item documentation using Agent mode with access to **8 specialized search and navigation tools** for comprehensive document exploration and analysis.
