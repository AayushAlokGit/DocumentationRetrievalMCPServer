# Document Upload System Setup Guide 📄

Complete setup guide for the **Document Processing & Upload System** component.

## 🎯 What This Component Does

The Document Upload System processes your work item documentation and creates a searchable index in Azure Cognitive Search. This is the **foundation** that enables the MCP server to provide intelligent search capabilities.

**You need to complete this setup FIRST** before using the MCP server.

## 📋 Prerequisites

### Azure Services Required

- **Azure OpenAI Service** with text-embedding-ada-002 deployment
- **Azure Cognitive Search** service (Basic tier or higher for vector search)

### Local Requirements

- **Python 3.8+**
- **Work Items directory** with markdown files organized as:
  ```
  Work Items/
  ├── WI-12345/
  │   ├── requirements.md
  │   └── implementation.md
  └── BUG-67890/
      └── analysis.md
  ```

## 🚀 Step-by-Step Setup

### Step 1: Azure OpenAI Service Setup

1. **Create Azure OpenAI Resource:**

   - Go to [Azure Portal](https://portal.azure.com)
   - Create new resource → AI + Machine Learning → Azure OpenAI
   - Choose region (e.g., East US, West Europe)

2. **Deploy Embedding Model:**

   - Navigate to Azure OpenAI Studio
   - Go to Deployments → Create new deployment
   - Deploy **text-embedding-ada-002** model
   - Note down the deployment name

3. **Get Credentials:**
   - Copy the **Endpoint URL** (e.g., `https://your-service.openai.azure.com/`)
   - Copy one of the **API keys**

### Step 2: Azure Cognitive Search Setup

1. **Create Search Service:**

   - Go to Azure Portal
   - Create new resource → Web → Azure Cognitive Search
   - **Important**: Choose **Basic tier or higher** (Free tier doesn't support vector search)
   - Choose same region as OpenAI service for better performance

2. **Get Credentials:**
   - Note down the **Service name** (e.g., `my-search-service`)
   - Go to Keys section → Copy the **Primary admin key**

### Step 3: Environment Configuration

1. **Navigate to project directory:**

   ```bash
   cd WorkItemDocumentationRetriever
   ```

2. **Create virtual environment:**

   ```bash
   python -m venv venv

   # Activate (Windows)
   venv\Scripts\activate

   # Activate (macOS/Linux)
   source venv/bin/activate
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Create environment file:**

   ```bash
   cp .env.example .env
   ```

5. **Configure .env file:**
   Edit `.env` with your Azure credentials:

   ```env
   # Azure OpenAI Configuration
   AZURE_OPENAI_ENDPOINT=https://your-openai-service.openai.azure.com/
   AZURE_OPENAI_KEY=your-openai-api-key-here
   EMBEDDING_DEPLOYMENT=text-embedding-ada-002
   OPENAI_API_VERSION=2024-05-01-preview

   # Azure Cognitive Search Configuration
   AZURE_SEARCH_SERVICE=your-search-service-name
   AZURE_SEARCH_KEY=your-search-admin-key-here
   AZURE_SEARCH_INDEX=work-items-index

   # Local Paths - UPDATE THIS PATH
   WORK_ITEMS_PATH=C:\path\to\your\Work Items

   # Processing Configuration (Optional)
   CHUNK_SIZE=1000
   CHUNK_OVERLAP=200
   VECTOR_DIMENSIONS=1536
   ```

### Step 4: Verify Document Upload Setup

Run the document upload verification script to check all connections:

```bash
python src/upload/scripts/verify_document_upload_setup.py
```

Expected output:

```
🔍 Document Upload System - Environment Variables
✅ PASS Required: AZURE_OPENAI_ENDPOINT
✅ PASS Required: AZURE_OPENAI_KEY
✅ PASS Required: AZURE_SEARCH_SERVICE
✅ PASS Required: AZURE_SEARCH_KEY
✅ PASS Required: WORK_ITEMS_PATH

🤖 Document Upload System - Azure OpenAI (Embeddings)
✅ PASS Embedding Service Initialization
✅ PASS Azure OpenAI Connection
✅ PASS Embedding Generation

🔍 Document Upload System - Azure Cognitive Search
✅ PASS Search Service Initialization
✅ PASS File Processing Tracker (DocumentProcessingTracker)
```

### Step 5: Create Search Index

Create the Azure Cognitive Search index with vector search capabilities:

```bash
python src/upload/scripts/create_index.py
```

Expected output:

```
🔧 Creating Azure Cognitive Search index: work-items-index
✅ Search index created successfully
📊 Index features:
   • Vector search enabled (1536 dimensions)
   • Hybrid search capabilities
   • Semantic search configuration
```

### Step 6: Upload Your Documents

Upload all your work item documentation:

```bash
# Upload all work items
python src/upload/scripts/upload_work_items.py

# Or test with dry run first
python src/upload/scripts/upload_work_items.py --dry-run
```

Expected output:

```
[TRACKER] Initialized with work items tracking source: C:\Work Items\processed_files.json
🚀 Starting document upload process...
📁 Discovered 45 markdown files across 12 work items
🔄 Processing documents in batches...
✅ Uploaded 234 document chunks successfully
⏭️  Skipped 15 files (already processed - no changes detected)
📊 Processing complete:
   • Work Items: 12
   • Files: 45 (30 processed, 15 skipped)
   • Chunks: 234
   • Index: work-items-index
```

## 🧪 Testing Your Upload

### Test 1: Verify Document Count

```bash
python -c "
import sys; sys.path.append('src')
from common.azure_cognitive_search import get_azure_search_service
search_svc = get_azure_search_service()
print(f'📊 Documents indexed: {search_svc.get_document_count()}')
print(f'📋 Work items: {len(search_svc.get_work_items())}')
"
```

### Test 2: Test Search Functionality

```bash
python -c "
import sys; sys.path.append('src')
from workitem_mcp.search_documents import DocumentSearcher
import asyncio

async def test_search():
    searcher = DocumentSearcher()
    results = searcher.text_search('authentication', None, 3)
    print(f'🔍 Found {len(results)} results for \"authentication\"')

asyncio.run(test_search())
"
```

## 🔧 Available Commands

### Upload Commands

```bash
# Upload all work items
python src/upload/scripts/upload_work_items.py

# Upload specific work item
python src/upload/scripts/upload_work_items.py --work-item WI-12345

# Preview what will be uploaded (dry run)
python src/upload/scripts/upload_work_items.py --dry-run

# Force reprocessing of all files (clears DocumentProcessingTracker and deletes all search documents)
python src/upload/scripts/upload_work_items.py --reset

# Upload single file
python src/upload/scripts/upload_single_file.py path/to/file.md
```

### Index Management

```bash
# Create/recreate index
python src/upload/scripts/create_index.py

# Verify setup
python verify_document_upload_setup.py
```

## 🔄 Updating Documentation

When you add new work item documentation:

1. **Add new files** to your Work Items directory
2. **Run upload script** to process new files:
   ```bash
   python scripts/upload_work_items.py
   ```
3. The system automatically **tracks processed files** and only uploads new/changed documents

To force reprocessing of all files:

```bash
python scripts/upload_work_items.py --reset
```

## 🐛 Troubleshooting

### "Failed to connect to Azure OpenAI"

- Check `AZURE_OPENAI_ENDPOINT` and `AZURE_OPENAI_KEY` in `.env`
- Verify the embedding model is deployed in Azure OpenAI Studio
- Ensure the deployment name matches `EMBEDDING_DEPLOYMENT`

### "Search service connection failed"

- Check `AZURE_SEARCH_SERVICE` and `AZURE_SEARCH_KEY` in `.env`
- Verify Azure Cognitive Search service is running
- Ensure service tier is Basic or higher (Free tier doesn't support vectors)

### "No work items found"

- Check `WORK_ITEMS_PATH` points to correct directory
- Ensure work item directories contain `.md` files
- Verify directory structure: `Work Items/WI-123/file.md`

### "Vector search not supported"

- Upgrade Azure Cognitive Search to Basic tier or higher
- Free tier doesn't support vector search capabilities

## ✅ Success Checklist

- [ ] Azure OpenAI service created and embedding model deployed
- [ ] Azure Cognitive Search service created (Basic tier+)
- [ ] Environment variables configured in `.env`
- [ ] `python verify_document_upload_setup.py` passes all checks
- [ ] Search index created successfully
- [ ] Documents uploaded and indexed
- [ ] Test searches return relevant results

## 🔗 Next Steps

Once document upload is complete, you can set up the **MCP Server component**:

- See [MCP_SERVER_SETUP.md](MCP_SERVER_SETUP.md) for VS Code integration

---

**📄 Document Upload System is now ready!** Your work item documentation is indexed and searchable.
