# Document Upload System Setup Guide 📄

Complete setup guide for the **Document Processing & Upload System** component.

## 🎯 What This Component Does

The Document Upload System processes your documentation files and creates a searchable index in Azure Cognitive Search. This is the **foundation** that enables the MCP server to provide intelligent search capabilities.

**You need to complete this setup FIRST** before using the MCP server.

## 📋 Prerequisites

### Azure Services Required

- **Azure OpenAI Service** with text-embedding-ada-002 deployment
- **Azure Cognitive Search** service (Basic tier or higher for vector search)

### Local Requirements

- **Python 3.8+**
- **Documentation directory** with files organized as:
  ```
  Documentation/
  ├── Project-A/
  │   ├── requirements.md
  │   └── implementation.md
  └── Research-B/
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
   cd DocumentationRetrievalMCPServer
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
   AZURE_SEARCH_INDEX=documentation-index

   # Local Paths - UPDATE THIS PATH
   PERSONAL_DOCUMENTATION_ROOT_DIRECTORY=C:\path\to\your\Documentation

   # Processing Configuration (Optional)
   CHUNK_SIZE=1000
   CHUNK_OVERLAP=200
   VECTOR_DIMENSIONS=1536
   ```

### Step 4: Create Search Index

Create the Azure Cognitive Search index that will store your documents:

```bash
python src\document_upload\common_scripts\azure_cogntive_search_scripts\create_index.py
```

This script creates the Azure Cognitive Search index with vector search capabilities. It will:

- **Create index** with name from `AZURE_SEARCH_INDEX` environment variable
- **Configure vector search** with 1536-dimensional embeddings (matching OpenAI ada-002)
- **Check existence** and safely handle index recreation if needed
- **Validate configuration** against your Azure Cognitive Search service tier

Expected output:

```
🔍 Environment Variables
```

🔧 Creating Azure Cognitive Search index: documentation-index
✅ Index created successfully with vector search capabilities
📊 Index configuration:
• Vector dimensions: 1536 (OpenAI ada-002 compatible)
• Search fields: content, file_path, context_name, title
• Vector field: content_vector
• Hybrid search enabled

````

### Step 5: Upload Your Documents

**Basic Upload:**

```bash
# Preview what will be processed (recommended first step)
python src\document_upload\personal_documentation_assistant_scripts\azure_cognitive_search_scripts\upload_with_pipeline.py "C:\path\to\documentation" --dry-run

# Upload documents (processes only new/changed files)
python src\document_upload\personal_documentation_assistant_scripts\azure_cognitive_search_scripts\upload_with_pipeline.py "C:\path\to\documentation"

# Force complete reprocessing
python src\document_upload\personal_documentation_assistant_scripts\azure_cognitive_search_scripts\upload_with_pipeline.py "C:\path\to\documentation" --force-reset
```

**Custom Metadata Upload:**

```bash
# Validate metadata format before uploading (recommended first step)
python src\document_upload\personal_documentation_assistant_scripts\azure_cognitive_search_scripts\upload_with_custom_metadata.py "C:\path\to\document.md" --metadata '{"title": "My Doc", "tags": "api,docs", "category": "tutorial", "work_item_id": "PROJ-123"}' --validate-only

# Upload with custom metadata (requires: title, tags, category, work_item_id)
python src\document_upload\personal_documentation_assistant_scripts\azure_cognitive_search_scripts\upload_with_custom_metadata.py "C:\path\to\document.md" --metadata '{"title": "My Doc", "tags": "api,docs", "category": "tutorial", "work_item_id": "PROJ-123"}'
```

💡 **Tip**: Use `--validate-only` first to check your metadata format and ensure all required fields are present before actual upload.

The script will show progress and statistics for processed documents.

## 🧪 Testing Your Upload

### Test 1: Quick Document Count Check

```bash
python -c "
import sys; sys.path.append('src')
from common.vector_search_services.azure_cognitive_search import get_azure_search_service
search_svc = get_azure_search_service()
count = search_svc.get_document_count()
print(f'📊 Documents indexed: {count}')
"
```

### Test 2: Search Functionality Validation

```bash
python -c "
import sys; sys.path.append('src')
from common.vector_search_services.azure_cognitive_search import get_azure_search_service
import asyncio

async def test_search():
    search_svc = get_azure_search_service()

    # Test text search
    text_results = search_svc.text_search('authentication', {}, 3)
    print(f'🔍 Text search results: {len(text_results)} for \"authentication\"')

    # Test vector search
    vector_results = await search_svc.vector_search('security requirements', {}, 3)
    print(f'🧠 Vector search results: {len(vector_results)} for \"security requirements\"')

    # Test hybrid search
    hybrid_results = await search_svc.hybrid_search('API documentation', {}, 3)
    print(f'⚡ Hybrid search results: {len(hybrid_results)} for \"API documentation\"')

asyncio.run(test_search())
"
```

### Test 3: Verify System Configuration

Test your configuration by running the MCP server startup test:

```bash
python run_mcp_server.py
```

Look for successful initialization:

- ✅ `[START] Starting Documentation Retrieval MCP Server`
- ✅ `EmbeddingGenerator initialized` (or warning - both are acceptable)
- ✅ `[SUCCESS] Connected to search index: N documents, M contexts`
- ✅ `[TARGET] MCP Server ready for connections`

💡 **Note**: Index not found errors are normal if you haven't created the index yet.

Press Ctrl+C to stop the test server.

##  Updating Documentation

- **File Path**: Tracks document location
- **File Size**: Detects content additions/deletions
- **Modification Time**: Identifies when files were last edited

**When you run upload scripts:**

1. ✅ **New files** → Automatically processed
2. ✅ **Modified files** → Automatically reprocessed
3. ⏭️ **Unchanged files** → Automatically skipped (improves performance)

### 📁 Adding New Documentation

**For new contexts:**

```bash
# 1. Add files to your Documentation directory structure:
#    Documentation/New-Project/requirements.md
#    Documentation/New-Project/implementation.md

# 2. Process the new project directory
python src\document_upload\personal_documentation_assistant_scripts\azure_cognitive_search_scripts\upload_with_pipeline.py "C:\Documentation" --verbose
```

**For adding files to existing contexts:**

```bash
# Just run regular upload - system detects new files automatically
python src\document_upload\personal_documentation_assistant_scripts\azure_cognitive_search_scripts\upload_with_pipeline.py "C:\Documentation"
```

### ✏️ Updating Existing Documentation

**For minor edits (recommended):**

```bash
# 1. Edit your files in Documentation directory
# 2. Run upload - system detects changes automatically
python src\document_upload\personal_documentation_assistant_scripts\azure_cognitive_search_scripts\upload_with_pipeline.py "C:\Documentation"
```

**For major restructuring:**

```bash
# Complete system refresh - deletes all documents and reprocesses everything
python src\document_upload\personal_documentation_assistant_scripts\azure_cognitive_search_scripts\upload_with_pipeline.py "C:\Documentation" --force-reset
```

**Delete specific context and reprocess:**

```bash
python src\document_upload\personal_documentation_assistant_scripts\azure_cognitive_search_scripts\delete_by_context_and_filename.py "Project-A" "*" --force
python src\document_upload\personal_documentation_assistant_scripts\azure_cognitive_search_scripts\upload_with_pipeline.py "C:\Documentation"
```

**Complete system reset:**

```bash
python src\document_upload\personal_documentation_assistant_scripts\azure_cognitive_search_scripts\upload_with_pipeline.py "C:\Documentation" --force-reset
```

## 🐛 Common Issues

**Azure OpenAI connection issues:**
- Check `AZURE_OPENAI_ENDPOINT` and `AZURE_OPENAI_KEY` in `.env`
- Verify embedding model deployment exists in Azure OpenAI Studio

**Azure Search connection issues:**
- Check `AZURE_SEARCH_SERVICE` and `AZURE_SEARCH_KEY` in `.env`
- Ensure service tier is **Basic or higher** (Free tier lacks vector search)

**Documents not processing:**
- Verify directory structure: `Documentation\Project-A\file.md`
- Check file permissions and supported formats (`.md`, `.txt`, `.docx`)

**Documents not updating:**
- Force reprocessing: `--force-reset`
- Or delete specific context first

**Test MCP server connection:**
```bash
python run_mcp_server.py
```

## ✅ Success Checklist

- [ ] Azure OpenAI service created and embedding model deployed
- [ ] Azure Cognitive Search service created (Basic tier+)
- [ ] Environment variables configured in `.env`
- [ ] Search index created successfully with `azure_cogntive_search_scripts\create_index.py`
- [ ] Documents uploaded and indexed with `azure_cognitive_search_scripts\upload_with_pipeline.py`
- [ ] MCP server can start and connect to services
- [ ] Test searches return relevant results

## 🔗 Next Steps

Once document upload is complete, you can set up the **MCP Server component**:

- See [MCP_SERVER_SETUP.md](MCP_SERVER_SETUP.md) for VS Code integration

---

**📄 Document Upload System is now ready!** Your documentation is indexed and searchable.
````
