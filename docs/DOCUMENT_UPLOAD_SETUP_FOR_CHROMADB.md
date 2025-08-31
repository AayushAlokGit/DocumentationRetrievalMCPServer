# Document Upload System Setup Guide for ChromaDB 📄

Complete setup guide for the **Document Processing & Upload System** using ChromaDB with local embeddings.

## 🎯 What This Component Does

The ChromaDB Document Upload System processes your documentation files locally and creates a searchable vector index using ChromaDB with local embedding generation. This provides **complete privacy** and **zero cloud costs** while enabling intelligent search capabilities through the MCP server.

**You need to complete this setup FIRST** before using the MCP server with ChromaDB.

## 📋 Prerequisites

### Local Requirements Only

- **Python 3.8+** with pip
- **Documentation directory** with files organized as:
  ```
  Documentation/
  ├── Project-A/
  │   ├── requirements.md
  │   └── implementation.md
  └── Research-B/
      └── analysis.md
  ```

### Hardware Recommendations

**Minimum:**

- **CPU**: 4+ cores, 2.5GHz+
- **RAM**: 8GB+ (4GB for models + 4GB for processing)
- **Storage**: 10GB+ free space (models + ChromaDB)

**Recommended:**

- **CPU**: 8+ cores, 3.0GHz+
- **RAM**: 16GB+ (better for batch processing)
- **Storage**: SSD with 20GB+ free space
- **GPU**: Optional NVIDIA GPU with CUDA (2-3x speedup)

## 🚀 Step-by-Step Setup

### Step 1: Environment Setup

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

3. **Install ChromaDB dependencies:**

   ```bash
   # Core ChromaDB and local embedding dependencies
   pip install chromadb sentence-transformers torch

   # Optional: GPU acceleration (NVIDIA)
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

   # Install remaining project dependencies
   pip install -r requirements.txt
   ```

### Step 2: Local Environment Configuration

1. **Create environment file:**

   ```bash
   cp .env.example .env
   ```

2. **Configure .env file:**
   Edit `.env` with your local settings:

   ```env
   # Document Processing Configuration
   PERSONAL_DOCUMENTATION_ROOT_DIRECTORY=C:\path\to\your\Documentation
   CHUNK_SIZE=1000
   CHUNK_OVERLAP=200
   SUPPORTED_FILE_EXTENSIONS=.md,.txt,.docx
   ```

### Step 3: Initialize Local Services

1. **Test local embedding service:**

   ```bash
   python src\common\embedding_services\test_local_embedding.py
   ```

   Expected output:

   ```
   🔧 Testing Local Embedding Service...
   📥 Downloading model: all-MiniLM-L6-v2
   ✅ Model loaded successfully
   🧠 Generated embeddings: 384 dimensions
   ⚡ Processing time: ~500ms
   ✅ Local embedding service ready!
   ```

2. **Initialize ChromaDB collection:**

   ChromaDB collection will be automatically created when you run your first upload script. No separate initialization script is needed.

3. **Verify system configuration:**

   ```bash
   python src\common\test_scripts\test_chromadb_with_local_embedding_generator.py
   ```

   Expected output:

   ```
   🔧 Testing ChromaDB Connection...
   ✅ ChromaDB client initialized
   ✅ Collection accessible: documentation_collection
   ✅ Local embedding service functional
   📊 Current collection status: 0 documents
   ✅ ChromaDB system ready for document upload!
   ```

### Step 4: Upload Your Documents

**Preview Upload (Recommended First Step):**

```bash
# Preview what will be processed locally
python src\document_upload\personal_documentation_assistant_scripts\chroma_db_scripts\upload_with_pipeline.py "C:\path\to\documentation" --dry-run
```

**Basic Upload:**

```bash
# Upload documents with local processing (processes only new/changed files)
python src\document_upload\personal_documentation_assistant_scripts\chroma_db_scripts\upload_with_pipeline.py "C:\path\to\documentation"

# Upload with verbose output
python src\document_upload\personal_documentation_assistant_scripts\chroma_db_scripts\upload_with_pipeline.py "C:\path\to\documentation" --verbose

# Force complete reprocessing
python src\document_upload\personal_documentation_assistant_scripts\chroma_db_scripts\upload_with_pipeline.py "C:\path\to\documentation" --force-reset
```

### 📋 Advanced Options with Logging

**Enable File Logging (Recommended for Production):**

```bash
# Auto-generated log file with IST timestamp in ScriptExecutionLogs/
python src\document_upload\personal_documentation_assistant_scripts\chroma_db_scripts\upload_with_pipeline.py "C:\docs" --log-file

# Custom log file name (also in ScriptExecutionLogs/)
python src\document_upload\personal_documentation_assistant_scripts\chroma_db_scripts\upload_with_pipeline.py "C:\docs" --log-file "my_upload.log"

# Absolute path log file (custom location)
python src\document_upload\personal_documentation_assistant_scripts\chroma_db_scripts\upload_with_pipeline.py "C:\docs" --log-file "C:\Logs\upload_session.log"
```

**Combined Logging and Processing Options:**

```bash
# Verbose upload with automatic logging
python src\document_upload\personal_documentation_assistant_scripts\chroma_db_scripts\upload_with_pipeline.py "C:\docs" --verbose --log-file

# Dry-run with logging to preview operations
python src\document_upload\personal_documentation_assistant_scripts\chroma_db_scripts\upload_with_pipeline.py "C:\docs" --dry-run --log-file "preview_run.log"

# Force reset with logging for audit trail
python src\document_upload\personal_documentation_assistant_scripts\chroma_db_scripts\upload_with_pipeline.py "C:\docs" --force-reset --log-file "reset_operation.log"
```

**Delete Operations with Logging:**

```bash
# Delete with automatic logging
python src\document_upload\personal_documentation_assistant_scripts\chroma_db_scripts\delete_by_context_and_filename.py "ProjectName" "filename.md" --log-file

# Delete with custom log file
python src\document_upload\personal_documentation_assistant_scripts\chroma_db_scripts\delete_by_context_and_filename.py "ProjectName" "filename.md" --log-file "deletion_audit.log"

# Dry-run deletion with logging for audit purposes
python src\document_upload\personal_documentation_assistant_scripts\chroma_db_scripts\delete_by_context_and_filename.py "ProjectName" "filename.md" --dry-run --log-file
```

#### Logging Features

- **📁 Automatic Directory Creation**: `ScriptExecutionLogs/` directory is created automatically
- **🕐 IST Timestamps**: All log files include India Standard Time timestamps
- **📊 Dual Output**: Operations logged to both console and file simultaneously
- **🔍 Detailed Tracking**: Complete operation history with timing and error details
- **📝 Auto-naming**: Default log files use format: `{script_name}_{YYYYMMDD}_{HHMMSS}_IST.log`

Example log file structure:

```
ScriptExecutionLogs/
├── upload_with_pipeline_20250831_143022_IST.log
├── delete_by_context_and_filename_20250831_143125_IST.log
└── custom_operation.log
```

**Custom Metadata Upload:**

```bash
# Validate metadata format before uploading
python src\document_upload\personal_documentation_assistant_scripts\chroma_db_scripts\upload_with_custom_metadata.py "C:\path\to\document.md" --metadata '{"title": "My Doc", "tags": "api,docs", "category": "tutorial", "context_name": "PROJ-123"}' --validate-only

# Upload with custom metadata
python src\document_upload\personal_documentation_assistant_scripts\chroma_db_scripts\upload_with_custom_metadata.py "C:\path\to\document.md" --metadata '{"title": "My Doc", "tags": "api,docs", "category": "tutorial", "context_name": "PROJ-123"}'
```

Expected upload output:

```
🔧 Starting ChromaDB Document Upload Pipeline...
🧠 Initializing local embedding service...
✅ Local embeddings ready: all-MiniLM-L6-v2 (384D)
📁 Scanning directory: C:\Documentation
🔍 Found 15 documents to process
📄 Processing: Project-A/requirements.md
🧠 Generating embeddings locally... (3 chunks)
💾 Storing in ChromaDB collection...
✅ Project-A/requirements.md → 3 chunks processed
📊 Upload Statistics:
• Documents processed: 15
• Total chunks: 47
• Average processing time: 2.3s per document
• Local storage used: 12.5 MB
✅ Upload completed successfully!
```

## 🧪 Testing Your Upload

### Test 1: Quick Document Count Check

```bash
python -c "
import sys; sys.path.append('src')
from common.vector_search_services.chromadb_service import get_chromadb_service
service = get_chromadb_service()
count = service.get_document_count()
print(f'📊 Documents indexed in ChromaDB: {count}')
"
```

### Test 2: Local Search Functionality Validation

```bash
python -c "
import sys; sys.path.append('src')
from common.vector_search_services.chromadb_service import get_chromadb_service

service = get_chromadb_service()

# Test vector search
print('🔍 Testing local vector search...')
results = service.search_documents('authentication requirements', max_results=3)
print(f'✅ Vector search results: {len(results)} documents found')

# Test metadata filtering
print('🔍 Testing metadata filtering...')
filtered = service.search_documents('API', filters={'file_type': 'md'}, max_results=3)
print(f'✅ Filtered search results: {len(filtered)} markdown documents found')

# Test context exploration
print('🔍 Testing context discovery...')
contexts = service.get_unique_field_values('context_name')
print(f'✅ Available contexts: {contexts}')

print('🎉 Local search functionality verified!')
"
```

### Test 3: Verify MCP Server Integration

```bash
python run_mcp_server.py
```

Look for successful initialization:

- ✅ `[START] Starting Documentation Retrieval MCP Server (ChromaDB)`
- ✅ `Local Embedding Service initialized: all-MiniLM-L6-v2`
- ✅ `[SUCCESS] Connected to ChromaDB collection: N documents`
- ✅ `[READY] 5 ChromaDB tools available`
- ✅ `[TARGET] MCP Server ready for VS Code integration`

Press Ctrl+C to stop the test server.

## 🔄 Updating Documentation

### Automatic Change Detection

ChromaDB system uses **signature-based tracking** for efficient updates:

- **File Path**: Tracks document location
- **File Size**: Detects content additions/deletions
- **Modification Time**: Identifies when files were last edited
- **Content Hash**: Optional deep change detection

**When you run upload scripts:**

1. ✅ **New files** → Automatically processed with local embeddings
2. ✅ **Modified files** → Automatically reprocessed and re-embedded
3. ⏭️ **Unchanged files** → Automatically skipped (improves performance)
4. 🗑️ **Deleted files** → Automatically detected and removed from ChromaDB

### 📁 Adding New Documentation

**For new contexts:**

```bash
# 1. Add files to your Documentation directory structure:
#    Documentation/New-Project/requirements.md
#    Documentation/New-Project/implementation.md

# 2. Process the new project directory
python src\document_upload\personal_documentation_assistant_scripts\chroma_db_scripts\upload_with_pipeline.py "C:\Documentation" --verbose
```

**For adding files to existing contexts:**

```bash
# Run regular upload - system detects new files automatically
python src\document_upload\personal_documentation_assistant_scripts\chroma_db_scripts\upload_with_pipeline.py "C:\Documentation"
```

### ✏️ Updating Existing Documentation

**For minor edits (recommended):**

```bash
# 1. Edit your files in Documentation directory
# 2. Run upload - system detects changes and re-embeds locally
python src\document_upload\personal_documentation_assistant_scripts\chroma_db_scripts\upload_with_pipeline.py "C:\Documentation"
```

**For major restructuring:**

```bash
# Complete local refresh - recreates ChromaDB collection and reprocesses everything
python src\document_upload\personal_documentation_assistant_scripts\chroma_db_scripts\upload_with_pipeline.py "C:\Documentation" --force-reset
```

**Delete specific context:**

```bash
python src\document_upload\personal_documentation_assistant_scripts\chroma_db_scripts\delete_by_context_and_filename.py "Project-A" "*" --force
```

## ✅ Success Checklist

- [ ] Python 3.8+ installed with virtual environment activated
- [ ] ChromaDB and required dependencies installed successfully
- [ ] Environment variables configured in `.env`
- [ ] Documents uploaded and indexed with ChromaDB scripts
- [ ] Local search functionality verified with test scripts
- [ ] MCP server can start and connect to ChromaDB

## 🔗 Next Steps

Once ChromaDB document upload is complete, you can set up the **MCP Server component**:

- See [MCP_SERVER_SETUP.md](MCP_SERVER_SETUP.md) for VS Code integration
- Review [02-Architecture-with-chromadb-local-embeddings.md](02-Architecture-with-chromadb-local-embeddings.md) for system architecture

---

**📄 ChromaDB Document Upload System is now ready!** Your documentation is indexed locally with complete privacy and zero cloud costs.

**Key Benefits Achieved:**

- ✅ **100% Privacy**: All processing happens on your machine
- ✅ **Zero Recurring Costs**: No cloud service fees
- ✅ **Fast Performance**: Local vector search with ChromaDB
- ✅ **Complete Control**: Full ownership of your data and processing
- ✅ **Offline Capable**: Works without internet connection
