# Quick Setup Guide

## 🚀 Quick Start (5 Minutes)

### 1. Install Dependencies

```bash
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 2. Configure Environment

Create `.env` file with your Azure credentials:

```env
AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com/
AZURE_OPENAI_KEY=your-key-here
AZURE_SEARCH_SERVICE=your-search-service
AZURE_SEARCH_KEY=your-search-key-here
WORK_ITEMS_PATH=C:\path\to\your\Work Items
```

### 3. Setup Search Index

```bash
python scripts/create_azure_cognitive_search_index.py
```

### 4. Upload Documentation

```bash
python scripts/upload_work_items.py
```

### 5. Configure VS Code MCP

Add to your MCP settings:

```json
{
  "mcpServers": {
    "work-items-documentation": {
      "command": "python",
      "args": ["C:\\...\\mcp_server.py"],
      "cwd": "C:\\...\\WorkItemDocumentationRetriever"
    }
  }
}
```

### 6. Test

```bash
python mcp_server.py
```

✅ **Done!** Your work item documentation is now searchable in VS Code.

---

📖 **Need detailed instructions?** See [COMPLETE_SETUP_GUIDE.md](COMPLETE_SETUP_GUIDE.md)
