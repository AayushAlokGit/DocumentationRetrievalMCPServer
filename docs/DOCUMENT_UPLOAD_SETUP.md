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

### Step 4: Verify Document Upload Setup

Run the comprehensive verification script to validate all system components:

```bash
python src\document_upload\common_scripts\verify_document_upload_setup.py
```

This script performs **comprehensive system validation** including:

- 🔍 **Environment Variables**: Validates all required Azure credentials and paths
- 🤖 **Azure OpenAI Connection**: Tests embedding service and model deployment
- 🔍 **Azure Cognitive Search**: Verifies service connectivity, index existence, and document counts
- 📁 **Documentation Directory**: Scans for context folders and supported documents (.md, .txt, .docx)
- 🧪 **Pipeline Components**: Tests import of processing strategies and document handling
- ⚡ **End-to-End Test**: Validates complete document processing pipeline

Expected output includes:

```
🔍 Environment Variables
✅ Environment file exists                Found: .env
✅ AZURE_OPENAI_ENDPOINT                 https://your-service.openai.azure.com/
✅ AZURE_OPENAI_KEY                      Configured (32 chars)
✅ AZURE_SEARCH_SERVICE                  your-search-service
✅ AZURE_SEARCH_KEY                      Configured (32 chars)
✅ PERSONAL_DOCUMENTATION_ROOT_DIRECTORY C:\path\to\Documentation

🤖 Azure OpenAI (Embeddings)
✅ Azure OpenAI connection               Service accessible
✅ Embedding service initialization      Using deployment: text-embedding-ada-002
✅ Test embedding generation             Generated 1536-dimensional vector

🔍 Azure Cognitive Search
✅ Azure Cognitive Search connection     Service accessible, found 2 indexes
✅ Azure Search Index exists             Index 'documentation-index' found
✅ Index document count                  Index contains 234 documents

📁 Documentation Directory Structure
✅ Documentation directory exists        Found: C:\path\to\Documentation
✅ Context directories found             Found 12 context directories
✅ Documents found                       Found 145 documents in first 10 contexts

📊 Verification Summary
✅ Environment: 6/6 tests passed
✅ Azure: 5/5 tests passed
✅ Directory: 3/3 tests passed
✅ Pipeline: 4/4 tests passed
✅ Test: 1/1 tests passed

📊 Overall: 19/19 tests passed
🎉 All verification tests passed! Your system is ready for document upload.

🚀 SYSTEM READY: You can now run document upload scripts!
📋 Next steps:
   1. Run: python src\document_upload\personal_documentation_assistant_scripts\upload_with_pipeline.py --dry-run
   2. Run: python src\document_upload\personal_documentation_assistant_scripts\upload_with_pipeline.py --context "Project-A"
   3. Force reprocess: python src\document_upload\personal_documentation_assistant_scripts\upload_with_pipeline.py --context "Project-A" --force
```

**🔧 System Readiness Assessment:**
The script evaluates both **critical requirements** (must pass for system to function) and **optional features** (nice-to-have enhancements).

### Step 5: Create Search Index

Create the Azure Cognitive Search index with vector search capabilities:

```bash
python src\document_upload\common_scripts\create_index.py
```

This script:

- **Creates index** with name from `AZURE_SEARCH_INDEX` environment variable
- **Configures vector search** with 1536-dimensional embeddings (matching OpenAI ada-002)
- **Checks existence** and safely handles index recreation if needed
- **Validates configuration** against your Azure Cognitive Search service tier

Expected output:

```
🔧 Creating Azure Cognitive Search index: documentation-index
✅ Index created successfully with vector search capabilities
📊 Index configuration:
   • Vector dimensions: 1536 (OpenAI ada-002 compatible)
   • Search fields: content, file_path, context_name, title
   • Vector field: content_vector
   • Hybrid search enabled
```

### Step 6: Upload Your Documents

The main upload script provides comprehensive document processing with multiple operation modes:

```bash
# Preview what will be processed (recommended first step)
python src\document_upload\personal_documentation_assistant_scripts\upload_with_pipeline.py --dry-run
```

**Available Command Options:**

```bash
# Basic Operations
python src\document_upload\personal_documentation_assistant_scripts\upload_with_pipeline.py
# Processes all contexts, skipping unchanged files (using file signature tracking)

python src\document_upload\personal_documentation_assistant_scripts\upload_with_pipeline.py --context "Project-A"
# Process only specific context (supports partial matching)

python src\document_upload\personal_documentation_assistant_scripts\upload_with_pipeline.py --dry-run
# Preview mode: shows what would be processed without making changes

# Force Processing Options
python src\document_upload\personal_documentation_assistant_scripts\upload_with_pipeline.py --force --context "Project-A"
# Force reprocessing of specific context (deletes existing + re-uploads)

python src\document_upload\personal_documentation_assistant_scripts\upload_with_pipeline.py --reset
# Full system reset: clears tracking data + deletes all indexed documents + reprocesses everything
```

**Expected Output (Normal Processing):**

```
[TRACKER] Initialized DocumentProcessingTracker with: C:\Documentation\.processed_files.json
📁 Scanning documentation directory: C:\Documentation
📁 Discovered 12 context directories
📄 Found 45 documents (.md, .txt, .docx files)

🔄 Starting document processing pipeline...
📊 Processing batch 1/3 (15 files)
✅ Project-A\requirements.md → 3 chunks processed
✅ Project-A\implementation.md → 5 chunks processed
⏭️  Project-A\notes.md → skipped (no changes detected)

📊 Processing Summary:
   • Contexts Processed: 12
   • Files Discovered: 45
   • Files Processed: 30 (new/changed)
   • Files Skipped: 15 (unchanged)
   • Document Chunks Created: 234
   • Processing Time: 45.2 seconds
   • Index: documentation-index
```

**Expected Output (Dry Run):**

```
🏃 DRY RUN MODE - No actual processing will occur

📁 Would process contexts: Project-A, Research-B, API-Docs
📄 Would process 45 files (30 new/changed, 15 unchanged)
⚡ Would generate approximately 234 document chunks
📋 Would update index: documentation-index

💡 To proceed with actual processing, remove --dry-run flag
```

## 🧪 Testing Your Upload

### Test 1: Quick Document Count Check

```bash
python -c "
import sys; sys.path.append('src')
from common.azure_cognitive_search import AzureCognitiveSearch
search_svc = AzureCognitiveSearch()
count = search_svc.get_document_count()
contexts = search_svc.get_contexts()
print(f'📊 Documents indexed: {count}')
print(f'📋 Contexts: {len(contexts)}')
print(f'🏷️  Context Names: {list(contexts)[:5]}...')
"
```

### Test 2: Search Functionality Validation

```bash
python -c "
import sys; sys.path.append('src')
from mcp_server.tools.universal_tools import UniversalDocumentationTools
import asyncio

async def test_search():
    tools = UniversalDocumentationTools()

    # Test text search
    text_results = await tools.search_documents('authentication', 'text', max_results=3)
    print(f'🔍 Text search results: {len(text_results)} for \"authentication\"')

    # Test vector search
    vector_results = await tools.search_documents('security requirements', 'vector', max_results=3)
    print(f'🧠 Vector search results: {len(vector_results)} for \"security requirements\"')

    # Test hybrid search
    hybrid_results = await tools.search_documents('API documentation', 'hybrid', max_results=3)
    print(f'⚡ Hybrid search results: {len(hybrid_results)} for \"API documentation\"')

asyncio.run(test_search())
"
```

### Test 3: Comprehensive System Validation

Re-run the verification script to confirm everything is working:

```bash
python src\document_upload\common_scripts\verify_document_upload_setup.py
```

Look for the final status: **🚀 SYSTEM READY: You can now run document upload scripts!**

## 🔧 Available Scripts & Commands

The document upload system provides a comprehensive set of utilities for different workflows:

### 📄 Document Upload & Processing

**Main Upload Script** (Primary Interface):

```bash
# Upload all contexts (processes only new/changed files)
python src\document_upload\personal_documentation_assistant_scripts\upload_with_pipeline.py

# Preview changes before processing
python src\document_upload\personal_documentation_assistant_scripts\upload_with_pipeline.py --dry-run

# Process specific context
python src\document_upload\personal_documentation_assistant_scripts\upload_with_pipeline.py --context "Project-A"

# Force reprocessing (deletes existing documents for context + re-uploads)
python src\document_upload\personal_documentation_assistant_scripts\upload_with_pipeline.py --context "Project-A" --force

# Complete system reset (clears all tracking + deletes all documents + reprocesses everything)
python src\document_upload\personal_documentation_assistant_scripts\upload_with_pipeline.py --reset
```

**Alternative Upload Scripts**:

```bash
# Upload with custom metadata
python src\document_upload\personal_documentation_assistant_scripts\upload_with_custom_metadata.py "C:\Documentation\Project-A\requirements.md"
```

**Single File Upload** (Development/Testing):

```bash
# Upload individual file
python src\document_upload\common_scripts\upload_single_file.py "C:\Documentation\Project-A\requirements.md"
```

### 🗑️ Document Management & Cleanup

**Context-Based Deletion** (Targeted Cleanup):

```bash
# Delete all documents for specific context (with confirmation)
python src\document_upload\personal_documentation_assistant_scripts\delete_by_context_and_filename.py "Project-A"

# Delete without confirmation prompt
python src\document_upload\personal_documentation_assistant_scripts\delete_by_context_and_filename.py "Project-A" --no-confirm
```

**File Pattern Deletion** (Flexible Cleanup):

```bash
# Delete documents matching specific filename
python src\document_upload\common_scripts\delete_by_file_path.py "outdated_requirements.md"

# Delete using wildcard patterns
python src\document_upload\common_scripts\delete_by_file_path.py "temp_*.md"

# Delete without confirmation
python src\document_upload\common_scripts\delete_by_file_path.py "draft_*.md" --no-confirm
```

### 🏗️ Index & System Management

**Index Operations**:

```bash
# Create or recreate search index
python src\document_upload\common_scripts\create_index.py
```

**System Verification**:

```bash
# Comprehensive system health check
python src\document_upload\common_scripts\verify_document_upload_setup.py
```

### 🔄 Common Workflow Patterns

**Initial Setup & Bulk Upload**:

```bash
# 1. Verify system is ready
python src\document_upload\common_scripts\verify_document_upload_setup.py

# 2. Preview what will be processed
python src\document_upload\personal_documentation_assistant_scripts\upload_with_pipeline.py --dry-run

# 3. Perform actual upload
python src\document_upload\personal_documentation_assistant_scripts\upload_with_pipeline.py
```

**Adding New Context**:

```bash
# Process only the new context
python src\document_upload\personal_documentation_assistant_scripts\upload_with_pipeline.py --context "New-Project"
```

**Updating Existing Context**:

```bash
# Option 1: Let system detect changes automatically
python src\document_upload\personal_documentation_assistant_scripts\upload_with_pipeline.py --context "Existing-Project"

# Option 2: Force complete reprocessing
python src\document_upload\personal_documentation_assistant_scripts\upload_with_pipeline.py --context "Existing-Project" --force
```

**Cleaning Up Before Reprocessing**:

```bash
# 1. Delete existing documents
python src\document_upload\personal_documentation_assistant_scripts\delete_by_context_and_filename.py "Context-Name" --no-confirm

# 2. Reprocess with fresh upload
python src\document_upload\personal_documentation_assistant_scripts\upload_with_pipeline.py --context "Context-Name"
```

## 🔄 Updating Documentation

The system is designed for **efficient incremental updates** using sophisticated file tracking:

### 🎯 Smart Change Detection

The **DocumentProcessingTracker** automatically detects file changes using:

- **File Path**: Tracks document location
- **File Size**: Detects content additions/deletions
- **Modification Time**: Identifies when files were last edited
- **Signature Hash**: Creates unique fingerprint for each file state

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

# 2. Process the new context
python src\document_upload\personal_documentation_assistant_scripts\upload_with_pipeline.py --context "New-Project"
```

**For adding files to existing contexts:**

```bash
# Just run regular upload - system detects new files automatically
python src\document_upload\personal_documentation_assistant_scripts\upload_with_pipeline.py --context "Existing-Project"
```

### ✏️ Updating Existing Documentation

**For minor edits (recommended):**

```bash
# 1. Edit your files in Documentation directory
# 2. Run upload - system detects changes automatically
python src\document_upload\personal_documentation_assistant_scripts\upload_with_pipeline.py
```

**For major restructuring:**

```bash
# Force complete reprocessing of specific context
python src\document_upload\personal_documentation_assistant_scripts\upload_with_pipeline.py --context "Project-A" --force
```

### 🔄 Force Reprocessing Options

**Targeted Reprocessing** (Recommended for specific updates):

```bash
# Deletes existing documents for context + reprocesses everything
python src\document_upload\personal_documentation_assistant_scripts\upload_with_pipeline.py --force --context "Project-A"
```

**Complete System Refresh** (Use sparingly):

```bash
# ⚠️  WARNING: Clears ALL tracking data + deletes ALL documents + reprocesses everything
python src\document_upload\personal_documentation_assistant_scripts\upload_with_pipeline.py --reset
```

### 🧹 Document Cleanup Workflows

**Before reprocessing a context:**

```bash
# 1. Clean up existing documents
python src\document_upload\personal_documentation_assistant_scripts\delete_by_context_and_filename.py "Project-A" --no-confirm

# 2. Reprocess with fresh upload
python src\document_upload\personal_documentation_assistant_scripts\upload_with_pipeline.py --context "Project-A"
```

**Remove outdated files by pattern:**

```bash
# Clean up old temporary or draft files
python src\document_upload\common_scripts\delete_by_file_path.py "temp_*.md" --no-confirm
python src\document_upload\common_scripts\delete_by_file_path.py "draft_*.md" --no-confirm
```

### 🎛️ Performance Optimization Tips

1. **Use context targeting** for faster processing:

   ```bash
   python src\document_upload\personal_documentation_assistant_scripts\upload_with_pipeline.py --context "Specific-Project"
   ```

2. **Preview changes** before processing large datasets:

   ```bash
   python src\document_upload\personal_documentation_assistant_scripts\upload_with_pipeline.py --dry-run
   ```

3. **Let the tracker work** - avoid unnecessary `--force` operations which bypass change detection

4. **Clean up before bulk operations** to avoid processing outdated content

## 🐛 Troubleshooting

### 🔧 Environment & Configuration Issues

**"Failed to connect to Azure OpenAI"**

- ✅ Check `AZURE_OPENAI_ENDPOINT` format: `https://your-service.openai.azure.com/`
- ✅ Verify `AZURE_OPENAI_KEY` is valid (32+ characters)
- ✅ Confirm embedding model deployment exists in Azure OpenAI Studio
- ✅ Ensure `EMBEDDING_DEPLOYMENT` matches exact deployment name
- ✅ Test connection: Run verification script for detailed diagnostics

**"Search service connection failed"**

- ✅ Verify `AZURE_SEARCH_SERVICE` is just the service name (not full URL)
- ✅ Check `AZURE_SEARCH_KEY` is the admin key (not query key)
- ✅ Confirm Azure Cognitive Search service is running and accessible
- ✅ Ensure service tier is **Basic or higher** (Free tier lacks vector search)

**"Index not found" / "404 errors"**

- ✅ Run index creation: `python src\document_upload\common_scripts\create_index.py`
- ✅ Check `AZURE_SEARCH_INDEX` environment variable matches created index name
- ✅ Verify Azure Search service has adequate capacity for new indexes

### 📁 Directory & File Issues

**"No documentation found"**

- ✅ Verify `PERSONAL_DOCUMENTATION_ROOT_DIRECTORY` path exists and is accessible
- ✅ Check directory structure: `Documentation\Project-A\file.md` (not flat file structure)
- ✅ Ensure context directories contain supported files (`.md`, `.txt`, `.docx`)
- ✅ Run verification script to see directory scanning results

**"Documents not processing"**

- ✅ Check file permissions (read access required)
- ✅ Verify file encoding (UTF-8 recommended)
- ✅ Ensure files aren't locked by other applications
- ✅ Check file size limits (very large files may cause memory issues)

### 🔄 Processing & Upload Issues

**"Documents not updating after changes"**

- 🔍 **Check file tracking**: System uses file signature (path + size + mtime)
- ✅ Verify files were actually saved with new modification time
- ✅ Force reprocessing for specific context:
  ```bash
  python src\document_upload\personal_documentation_assistant_scripts\upload_with_pipeline.py --context "Project-A" --force
  ```
- ✅ Clear tracking data if necessary:
  ```bash
  python src\document_upload\personal_documentation_assistant_scripts\upload_with_pipeline.py --reset
  ```

**"Vector search not supported"**

- ✅ Upgrade Azure Cognitive Search to **Basic tier or higher**
- ✅ Free tier doesn't support vector search capabilities
- ✅ Recreate index after tier upgrade

**"Memory errors during processing"**

- ✅ Process smaller batches using `--context` targeting
- ✅ System uses generators for O(1) memory complexity, but very large files can still cause issues
- ✅ Split large documents into smaller files
- ✅ Ensure adequate system RAM (4GB+ recommended for large document sets)

### 📊 Index & Search Issues

**"Inconsistent document counts"**

- 🧹 Clean up orphaned documents:
  ```bash
  python src\document_upload\personal_documentation_assistant_scripts\delete_by_context_and_filename.py "Project-A" --no-confirm
  ```
- ✅ Reprocess with clean upload:
  ```bash
  python src\document_upload\personal_documentation_assistant_scripts\upload_with_pipeline.py --context "Project-A"
  ```

**"Search returns no results"**

- ✅ Verify documents were actually indexed (check document count)
- ✅ Test with broader search terms
- ✅ Check that search index contains expected context names
- ✅ Try different search modes (text, vector, hybrid)

**"Duplicate documents appearing"**

- 🧹 Clear specific context and reprocess:
  ```bash
  python src\document_upload\personal_documentation_assistant_scripts\delete_by_context_and_filename.py "Project-A" --no-confirm
  python src\document_upload\personal_documentation_assistant_scripts\upload_with_pipeline.py --context "Project-A"
  ```

### 🛠️ Diagnostic Commands

**Run comprehensive diagnostics:**

```bash
python src\document_upload\common_scripts\verify_document_upload_setup.py
```

**Check specific context processing:**

```bash
python src\document_upload\personal_documentation_assistant_scripts\upload_with_pipeline.py --context "Project-A" --dry-run
```

**Test search functionality:**

```bash
python -c "
import sys; sys.path.append('src')
from mcp_server.tools.universal_tools import UniversalDocumentationTools
import asyncio
async def test():
    tools = UniversalDocumentationTools()
    results = await tools.search_documents('test', 'text', max_results=1)
    print(f'Search test: {len(results)} results')
asyncio.run(test())
"
```

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

**📄 Document Upload System is now ready!** Your documentation is indexed and searchable.
