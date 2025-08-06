# VS Code MCP Configuration Guide

## Setting up MCP in VS Code

### 1. Locate Your MCP Settings File

The MCP settings file location depends on your VS Code setup:

**Windows:**

```
%APPDATA%\Code\User\globalStorage\rooveterinaryinc.roo-cline\settings\cline_mcp_settings.json
```

**macOS:**

```
~/Library/Application Support/Code/User/globalStorage/rooveterinaryinc.roo-cline/settings/cline_mcp_settings.json
```

**Linux:**

```
~/.config/Code/User/globalStorage/rooveterinaryinc.roo-cline/settings/cline_mcp_settings.json
```

### 2. MCP Configuration

Add this configuration to your MCP settings file:

```json
{
  "mcpServers": {
    "work-items-documentation": {
      "command": "python",
      "args": [
        "C:\\Users\\aayushalok\\OneDrive - Microsoft\\Desktop\\Personal Projects\\WorkItemDocumentationRetriever\\mcp_server.py"
      ],
      "cwd": "C:\\Users\\aayushalok\\OneDrive - Microsoft\\Desktop\\Personal Projects\\WorkItemDocumentationRetriever",
      "env": {
        "PYTHONPATH": "C:\\Users\\aayushalok\\OneDrive - Microsoft\\Desktop\\Personal Projects\\WorkItemDocumentationRetriever"
      }
    }
  }
}
```

**❗ Important:** Update the paths above to match your actual project location.

### 3. Alternative: PowerShell Script Path (Windows)

If you encounter path issues on Windows, you can also use:

```json
{
  "mcpServers": {
    "work-items-documentation": {
      "command": "powershell.exe",
      "args": [
        "-Command",
        "cd 'C:\\Users\\aayushalok\\OneDrive - Microsoft\\Desktop\\Personal Projects\\WorkItemDocumentationRetriever'; .\\venv\\Scripts\\activate; python mcp_server.py"
      ],
      "cwd": "C:\\Users\\aayushalok\\OneDrive - Microsoft\\Desktop\\Personal Projects\\WorkItemDocumentationRetriever"
    }
  }
}
```

### 4. Virtual Environment Considerations

If you're using a virtual environment (recommended), you have two options:

#### Option A: Use Virtual Environment Python

```json
{
  "mcpServers": {
    "work-items-documentation": {
      "command": "C:\\Users\\aayushalok\\OneDrive - Microsoft\\Desktop\\Personal Projects\\WorkItemDocumentationRetriever\\venv\\Scripts\\python.exe",
      "args": ["mcp_server.py"],
      "cwd": "C:\\Users\\aayushalok\\OneDrive - Microsoft\\Desktop\\Personal Projects\\WorkItemDocumentationRetriever"
    }
  }
}
```

#### Option B: Activation Script (Windows)

Create a batch file `start_mcp.bat`:

```batch
@echo off
cd /d "C:\Users\aayushalok\OneDrive - Microsoft\Desktop\Personal Projects\WorkItemDocumentationRetriever"
call venv\Scripts\activate
python mcp_server.py
```

Then use in MCP config:

```json
{
  "mcpServers": {
    "work-items-documentation": {
      "command": "C:\\Users\\aayushalok\\OneDrive - Microsoft\\Desktop\\Personal Projects\\WorkItemDocumentationRetriever\\start_mcp.bat",
      "cwd": "C:\\Users\\aayushalok\\OneDrive - Microsoft\\Desktop\\Personal Projects\\WorkItemDocumentationRetriever"
    }
  }
}
```

### 5. Testing MCP Connection

1. **Restart VS Code** after updating MCP configuration
2. **Check VS Code Console** (Help → Toggle Developer Tools → Console)
3. Look for MCP connection messages
4. **Test with Command Palette**: Look for work-items related commands

### 6. Troubleshooting

#### Issue: "Command not found" or "Python not found"

- **Solution**: Use full path to python executable (see Option A above)

#### Issue: "Module not found" errors

- **Solution**: Ensure PYTHONPATH includes project directory or use virtual environment

#### Issue: "Connection failed"

- **Solution**: Check that mcp_server.py can run independently:
  ```bash
  cd "C:\Users\aayushalok\OneDrive - Microsoft\Desktop\Personal Projects\WorkItemDocumentationRetriever"
  python mcp_server.py
  ```

#### Issue: "Environment variables not found"

- **Solution**: Ensure .env file exists and is properly configured

### 7. Available Commands in VS Code

Once connected, you can use these MCP tools:

- `search_work_items`: Search all work item documentation
- `get_work_item_list`: List all available work items
- `get_work_item_summary`: Get documentation statistics
- `search_by_work_item`: Search within specific work item
- `semantic_search`: Conceptual/semantic search

### 8. Example Usage in VS Code

Ask the AI assistant:

- "What work items contain authentication code?"
- "Show me the implementation details for WI-12345"
- "List all available work items"
- "Find documentation about API integration"

The MCP server will automatically search your indexed documentation and provide relevant answers!

---

**📝 Note**: Replace all paths with your actual project location before using these configurations.
