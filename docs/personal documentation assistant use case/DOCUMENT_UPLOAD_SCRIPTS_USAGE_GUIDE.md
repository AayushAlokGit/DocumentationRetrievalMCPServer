# Document Upload Scripts Usage Guide 📚

Complete guide for using the Personal Documentation Assistant upload and deletion scripts to successfully manage documents in your Azure Cognitive Search index.

## 🎯 Overview

This guide covers three essential scripts for document management:

1. **`upload_with_custom_metadata.py`** - Upload with complete metadata control
2. **`upload_with_pipeline.py`** - Full pipeline processing with automatic features
3. **`delete_by_context_and_filename.py`** - Precise document deletion

## 📋 Prerequisites

**Before using any scripts:**

1. ✅ Complete [Document Upload Setup](../DOCUMENT_UPLOAD_SETUP.md)
2. ✅ Azure services configured and running
3. ✅ Virtual environment activated
4. ✅ All dependencies installed

**Quick verification:**

```bash
# Activate environment
.venv\Scripts\activate

# Test Azure connection
python -c "
from src.common.azure_cognitive_search import AzureCognitiveSearchService
search_service = AzureCognitiveSearchService()
print('✅ Connected' if search_service.index_exists() else '❌ Connection failed')
"
```

---

## 🚀 Script 1: Custom Metadata Upload

**Purpose**: Upload documents with complete control over metadata fields

### Basic Usage

```bash
# Upload single file with custom metadata
python src/document_upload/personal_documentation_assistant_scripts/upload_with_custom_metadata.py "path/to/file.md" --metadata '{"title": "My Document", "tags": "important,guide", "category": "Documentation", "work_item_id": "PROJECT-123"}'

# Upload entire directory with same metadata
python src/document_upload/personal_documentation_assistant_scripts/upload_with_custom_metadata.py "path/to/directory" --metadata '{"title": "Project Documents", "tags": "project,batch", "category": "Project Files", "work_item_id": "PROJECT-123"}'
```

### Required Metadata Fields

```json
{
  "title": "Document title for search results",
  "tags": "comma,separated,keywords",
  "category": "Document category for filtering",
  "work_item_id": "Context grouping identifier"
}
```

### Optional Fields (Auto-generated if not provided)

- `file_type` - Detected from file extension
- `last_modified` - File modification timestamp

### Examples by Use Case

#### API Documentation Upload

```bash
python src/document_upload/personal_documentation_assistant_scripts/upload_with_custom_metadata.py "docs/api/" --metadata '{"title": "REST API Documentation", "tags": "api,endpoints,authentication,swagger", "category": "API Reference", "work_item_id": "API-DOCS-2024"}'
```

#### Project Documentation Upload

```bash
python src/document_upload/personal_documentation_assistant_scripts/upload_with_custom_metadata.py "project-docs/" --metadata '{"title": "Project Implementation Guide", "tags": "implementation,architecture,deployment,testing", "category": "Project Documentation", "work_item_id": "PROJECT-ALPHA"}'
```

#### Research Papers Upload

```bash
python src/document_upload/personal_documentation_assistant_scripts/upload_with_custom_metadata.py "research/" --metadata '{"title": "Machine Learning Research", "tags": "machine-learning,neural-networks,deep-learning,papers", "category": "Research", "work_item_id": "ML-RESEARCH-2024"}'
```

---

## 🔄 Script 2: Pipeline Upload (Recommended)

**Purpose**: Full-featured pipeline processing with automatic metadata generation and safety features

### Basic Usage

```bash
# Process single file
python src/document_upload/personal_documentation_assistant_scripts/upload_with_pipeline.py "docs/readme.md"

# Process entire directory
python src/document_upload/personal_documentation_assistant_scripts/upload_with_pipeline.py "C:/Work Items"

# Preview what would be processed (dry run)
python src/document_upload/personal_documentation_assistant_scripts/upload_with_pipeline.py "docs/" --dry-run
```

### Advanced Options

#### Complete Reset (Delete All + Reprocess)

```bash
# DANGER: Deletes ALL documents from index and reprocesses everything
python src/document_upload/personal_documentation_assistant_scripts/upload_with_pipeline.py "docs/" --force-reset

# Safe: Preview what reset would do
python src/document_upload/personal_documentation_assistant_scripts/upload_with_pipeline.py "docs/" --force-reset --dry-run
```

#### Statistics and Monitoring

```bash
# Show detailed processing statistics
python src/document_upload/personal_documentation_assistant_scripts/upload_with_pipeline.py "docs/" --stats

# Verbose output with detailed progress
python src/document_upload/personal_documentation_assistant_scripts/upload_with_pipeline.py "docs/" --verbose

# Combined: stats + verbose for comprehensive monitoring
python src/document_upload/personal_documentation_assistant_scripts/upload_with_pipeline.py "docs/" --stats --verbose
```

### Key Features

- **Idempotent Processing**: Automatically skips unchanged files
- **File Tracking**: Maintains `processed_files.json` for state management
- **Automatic Metadata**: Generates context-aware metadata from file paths
- **Error Recovery**: Continues processing after individual file failures
- **Progress Tracking**: Real-time progress updates and statistics

### When to Use Pipeline vs Custom Metadata

| Use Pipeline When                | Use Custom Metadata When              |
| -------------------------------- | ------------------------------------- |
| First-time bulk upload           | Specific metadata requirements        |
| Regular maintenance updates      | Custom tagging strategies             |
| Directory-based organization     | Cross-project document batches        |
| Automatic metadata is sufficient | Need consistent metadata across files |

---

## 🗑️ Script 3: Document Deletion

**Purpose**: Safely delete specific documents from the search index

### Basic Usage

```bash
# Delete specific file by context and filename
python src/document_upload/personal_documentation_assistant_scripts/delete_by_context_and_filename.py "PROJECT-123" "readme.md"

# Preview what would be deleted (recommended first step)
python src/document_upload/personal_documentation_assistant_scripts/delete_by_context_and_filename.py "PROJECT-123" "readme.md" --preview
```

### Matching Modes

#### Exact Match (Default)

```bash
# Exact context name + exact filename
python src/document_upload/personal_documentation_assistant_scripts/delete_by_context_and_filename.py "Documentation Retrieval MCP Server" "01-Architecture-Simplified.md"
```

#### Contains Match

```bash
# Exact context + filename contains pattern
python src/document_upload/personal_documentation_assistant_scripts/delete_by_context_and_filename.py "PROJECT-123" "setup" --mode contains
```

#### Flexible Match

```bash
# Tries exact first, then contains if no results
python src/document_upload/personal_documentation_assistant_scripts/delete_by_context_and_filename.py "PROJECT-123" "setup" --mode flexible
```

### Safety Features

#### Preview Mode (Highly Recommended)

```bash
# Show what would be deleted with detailed information
python src/document_upload/personal_documentation_assistant_scripts/delete_by_context_and_filename.py "PROJECT-123" "readme.md" --preview --detailed

# Quick preview without detailed chunk information
python src/document_upload/personal_documentation_assistant_scripts/delete_by_context_and_filename.py "PROJECT-123" "readme.md" --preview
```

#### Force Mode (Skip Confirmations)

```bash
# Delete without confirmation prompts (use carefully)
python src/document_upload/personal_documentation_assistant_scripts/delete_by_context_and_filename.py "PROJECT-123" "readme.md" --force
```

### Common Deletion Scenarios

#### Remove Outdated Documentation

```bash
# 1. Preview to verify correct documents
python src/document_upload/personal_documentation_assistant_scripts/delete_by_context_and_filename.py "OLD-PROJECT" "outdated-guide.md" --preview

# 2. Delete after confirmation
python src/document_upload/personal_documentation_assistant_scripts/delete_by_context_and_filename.py "OLD-PROJECT" "outdated-guide.md"
```

#### Clean Up Test Uploads

```bash
# Remove all files containing "test" in filename
python src/document_upload/personal_documentation_assistant_scripts/delete_by_context_and_filename.py "TEST-UPLOADS" "test" --mode contains --preview

# Delete after verification
python src/document_upload/personal_documentation_assistant_scripts/delete_by_context_and_filename.py "TEST-UPLOADS" "test" --mode contains
```

---

## 🔧 Best Practices

### Upload Strategy

1. **Start Small**: Test with single files before batch uploads
2. **Use Dry Run**: Always preview large operations with `--dry-run`
3. **Monitor Progress**: Use `--verbose` and `--stats` for large uploads
4. **Organize by Context**: Use meaningful `work_item_id` values for grouping

### Metadata Strategy

1. **Consistent Tags**: Develop a tagging convention and stick to it
2. **Functional Categories**: Use categories that match your search patterns
3. **Descriptive Titles**: Make titles searchable and distinctive
4. **Logical Grouping**: Group related documents with same `work_item_id`

### Deletion Safety

1. **Always Preview**: Use `--preview` before actual deletion
2. **Start Specific**: Begin with exact matches, expand to flexible if needed
3. **Backup Important**: Consider exporting before large deletions
4. **Verify Results**: Check search results after deletion to confirm

---

## 📊 Monitoring and Troubleshooting

### Check Index Status

```bash
# View current index statistics
python -c "
from src.common.azure_cognitive_search import AzureCognitiveSearchService
service = AzureCognitiveSearchService()
stats = service.get_index_stats()
print(f'Documents: {stats.get(\"document_count\", 0):,}')
print(f'Storage: {stats.get(\"storage_size\", 0)} bytes')
"
```

### View Recently Processed Files

```bash
# Check processing tracker status
python -c "
import json
from pathlib import Path
tracker_file = Path('C:/Users/aayushalok/OneDrive - Microsoft/Desktop/PersonalDocumentation/processed_files.json')
if tracker_file.exists():
    with open(tracker_file) as f:
        data = json.load(f)
        print(f'Tracked files: {len(data)}')
        # Show last 5 processed
        items = list(data.items())[-5:]
        for path, info in items:
            print(f'  {Path(path).name} - {info.get(\"last_processed\", \"unknown\")}')
else:
    print('No tracker file found')
"
```

### Common Error Solutions

#### "No documents found" during deletion

- Verify context name matches exactly (case-sensitive)
- Check filename spelling and extension
- Use `--mode flexible` to try broader matching

#### "Azure connection failed"

- Verify `.env` file has correct credentials
- Check Azure services are running and accessible
- Confirm search index exists

#### "File already processed" during upload

- This is normal - file hasn't changed since last upload
- Use `--force-reset` in pipeline script to reprocess all files
- Check file modification date if expecting changes

---

## 🎯 Complete Workflow Examples

### Initial Project Setup

```bash
# 1. Create index (if needed)
python src/document_upload/common_scripts/create_index.py

# 2. Upload project documentation with custom metadata
python src/document_upload/personal_documentation_assistant_scripts/upload_with_custom_metadata.py "project-docs/" --metadata '{"title": "Project Alpha Documentation", "tags": "project-alpha,implementation,architecture", "category": "Project Documentation", "work_item_id": "PROJECT-ALPHA"}'

# 3. Verify upload
python -c "from src.common.azure_cognitive_search import AzureCognitiveSearchService; print(f'Total docs: {AzureCognitiveSearchService().get_index_stats()[\"document_count\"]}')"
```

### Regular Maintenance

```bash
# 1. Process any new or changed files
python src/document_upload/personal_documentation_assistant_scripts/upload_with_pipeline.py "project-docs/" --stats

# 2. Clean up obsolete documents (preview first)
python src/document_upload/personal_documentation_assistant_scripts/delete_by_context_and_filename.py "PROJECT-ALPHA" "old-spec" --mode contains --preview

# 3. Delete confirmed obsolete docs
python src/document_upload/personal_documentation_assistant_scripts/delete_by_context_and_filename.py "PROJECT-ALPHA" "old-spec" --mode contains
```

### Complete Reset and Rebuild

```bash
# 1. Preview what would be reset
python src/document_upload/personal_documentation_assistant_scripts/upload_with_pipeline.py "all-docs/" --force-reset --dry-run

# 2. Perform complete reset and reprocessing
python src/document_upload/personal_documentation_assistant_scripts/upload_with_pipeline.py "all-docs/" --force-reset --verbose --stats
```

---

## ⚠️ Important Notes

### File Path Requirements

- Use forward slashes (`/`) or double backslashes (`\\`) in paths
- Avoid spaces in paths when possible
- Use quotes around paths with spaces: `"path with spaces/"`

### Supported File Formats

- **Markdown**: `.md` files with optional frontmatter
- **Text**: `.txt` files with UTF-8 encoding
- **Word Documents**: `.docx` files (metadata extraction supported)

### Azure Limits

- **Document Size**: Max 16 MB per document
- **Field Size**: Max 32 KB per field (content fields can be larger)
- **Batch Size**: Scripts automatically handle batch sizing
- **Rate Limits**: Built-in rate limiting prevents API overload

### Performance Tips

- **Batch Processing**: Process directories rather than individual files
- **Parallel Processing**: Scripts use async processing for embeddings
- **Network Optimization**: Ensure stable internet connection for large uploads
- **Memory Management**: Large directories are processed in chunks

This comprehensive guide should enable successful document management in your Personal Documentation Assistant system!
