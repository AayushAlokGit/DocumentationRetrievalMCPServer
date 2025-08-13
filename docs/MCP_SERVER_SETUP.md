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
if doc_count > 0:
    print(f'✅ Ready! Found {doc_count} indexed documents')
else:
    print('❌ No documents found. Complete Document Upload Setup first.')
"
```

**Expected Output**: `✅ Ready! Found [N] indexed documents`

If you see 0 documents, run the upload command:

```bash
python src/upload/scripts/upload_work_items.py
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
✅ Connected to search index: 234 documents, 12 work items
🎯 MCP Server ready for connections
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
   - You should see tools like `search_work_items`, `get_work_item_list`, etc.

### Step 4: Test GitHub Copilot Integration

GitHub Copilot Chat in VS Code will automatically detect and use your MCP tools when in **Agent Mode**.

#### Method 1: Using Agent Mode

1. Open GitHub Copilot Chat (`Ctrl+Alt+I`)
2. **Select "Agent" mode** from the chat mode dropdown
3. Try these test queries:

```
List all my available work items
```

```
Search for work items related to authentication
```

```
Show me documentation about API integration from my work items
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

Once integrated with VS Code, GitHub Copilot can use these tools in Agent mode:

### Core Search Tools

- **`search_work_items`**: Search across all work item documentation

  - Supports text, vector, and hybrid search
  - Can filter by specific work item ID
  - Configurable result count

- **`semantic_search`**: Find conceptually similar content

  - AI-powered semantic understanding
  - Great for finding related concepts

- **`search_by_work_item`**: Search within a specific work item
  - Focused search within one work item's documentation

### Information Tools

- **`get_work_item_list`**: List all available work item IDs
- **`get_work_item_summary`**: Get statistics and overview

## 📝 Example Usage with GitHub Copilot

### Basic Queries

```
"List all available work items"
→ Uses get_work_item_list tool

"What work items dealt with authentication?"
→ Uses search_work_items tool with query "authentication"

"Show me information about WI-12345"
→ Uses search_by_work_item tool with work_item_id "WI-12345"
```

### Advanced Queries

```
"Find work items similar to user login functionality"
→ Uses semantic_search tool for conceptual similarity

"Search for API integration examples in work items"
→ Uses search_work_items with hybrid search

"What are the common themes across all my work items?"
→ Uses multiple tools to analyze patterns
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

- Total number of work items
- Total number of documents
- List of work item IDs

### Test 4: Search Test

```
"Search my work items for documentation about 'testing' or 'quality assurance'"
```

Expected response should include:

- Relevant document excerpts
- Work item IDs
- File paths
- Relevance scores

### Test 5: Specific Work Item Test

```
"Show me all documentation for work item [YOUR-WORK-ITEM-ID]"
```

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

## 📊 Performance Tips

### Optimal Query Types

- **Text search**: Exact keywords, specific terms
- **Vector search**: Conceptual queries, natural language
- **Hybrid search**: Best of both (default for most tools)

### Response Management

- Use `max_results` parameter to limit response size
- Be specific in queries for better relevance
- Use work item filtering for focused searches

## ✅ Success Checklist

- [ ] Document Upload System is working (prerequisite)
- [ ] MCP server starts without errors (`python mcp_server.py`)
- [ ] `.vscode/mcp.json` configuration file created
- [ ] VS Code restarted after configuration
- [ ] MCP server appears as "Running" in `MCP: List Servers`
- [ ] Work item tools visible in GitHub Copilot Agent mode Tools list
- [ ] Test queries return expected results from your documentation
- [ ] GitHub Copilot can successfully use work-items tools

## 🔗 GitHub Copilot Integration Examples

### Code Context Queries

```
"Based on my work item documentation, what patterns do we use for error handling?"

"Find examples of database integration approaches from completed work items"

"What security considerations are mentioned across work items?"
```

### Project Planning Queries

```
"What work items involved similar functionality to what I'm currently working on?"

"Show me lessons learned from previous bug fix work items"

"Find work items that dealt with performance optimization"
```

### Architecture and Design Queries

```
"How did we approach authentication in previous work items?"

"What API design patterns appear most frequently in our documentation?"

"Find work items that document integration with external services"
```

---

**🔌 MCP Server is now integrated with VS Code and GitHub Copilot!** You can now ask GitHub Copilot questions about your work item documentation using Agent mode.
