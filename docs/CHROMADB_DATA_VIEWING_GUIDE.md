# ChromaDB Data Viewing and Inspection Guide

## Overview

This guide provides comprehensive methods to view, inspect, and analyze ChromaDB data stored in your DocumentationRetrievalMCPServer project. ChromaDB stores vector embeddings, document content, and metadata in a persistent SQLite-based format that can be accessed through multiple methods.

## 🗂️ ChromaDB Data Structure

### Storage Location

```
DocumentationRetrievalMCPServer/
└── chromadb_data/
    ├── chroma.sqlite3              # Main SQLite database
    ├── 6126797c-1ee8-49e8-91f8-... # Collection UUID folders
    ├── 986419eb-69c5-4d8d-88b6-... # (contain additional metadata)
    └── ...
```

### Data Components

- **Collections**: Named groups of documents (e.g., "documentation_collection")
- **Documents**: Text chunks with embeddings and metadata
- **Embeddings**: Vector representations for semantic search
- **Metadata**: File information, tags, categories, context data

## 🔍 Method 1: Python Export Script (Recommended)

### Quick JSON Export

The `export_chromadb_data.py` script provides the easiest way to view your ChromaDB data by exporting it to a readable JSON format.

```bash
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Export with defaults (documentation_collection → chromadb_export.json)
python export_chromadb_data.py

# Export specific collection to custom file
python export_chromadb_data.py "my_collection" "my_export.json"

# Export with collection name only (uses default filename)
python export_chromadb_data.py "documentation_collection"
```

**Script Features:**

- ✅ **Simple Usage**: Just run without arguments for default export
- ✅ **Flexible Parameters**: Specify collection name and/or output filename
- ✅ **Complete Data Export**: Includes all document content and metadata
- ✅ **JSON Format**: Easy to read, search, and analyze
- ✅ **Error Handling**: Clear messages if collection not found

**Output:** Creates a JSON file with complete document data for detailed analysis.

### Sample Script Output

```bash
ChromaDB Data JSON Export
=========================
� Exporting collection 'documentation_collection' to 'chromadb_export.json'...
✅ Exported 21 documents to chromadb_export.json
```

### JSON Export Structure

The exported JSON follows this structure:

```json
{
  "collection_name": "documentation_collection",
  "document_count": 21,
  "documents": [
    {
      "id": "1371296e9b2226c51c56606d793cf536_chunk_0",
      "content": "Full document content here...",
      "metadata": {
        "chunk_index": "filename_chunk_0",
        "work_item_id": "DocumentationRetrievalMCPServer",
        "file_name": "INTELLIGENT_DOCUMENT_UPLOAD_WITH_VSCODE_AGENT.md",
        "title": "Intelligent Document Upload Using VS Code Agent Mode",
        "category": "Process Guide",
        "tags": "docs-workflow,vscode-agent,ai-powered-analysis...",
        "context_name": "DocumentationRetrievalMCPServer",
        "file_path": "C:\\Users\\...\\docs\\INTELLIGENT_DOCUMENT_UPLOAD_WITH_VSCODE_AGENT.md",
        "file_type": "md",
        "processing_strategy": "PersonalDocumentationAssistant_ChromaDB",
        "last_modified": "2025-08-28T12:32:54.151214"
      }
    }
  ]
}
```

## 🗄️ Method 2: SQLite Database Access

### Using DB Browser for SQLite (GUI - Recommended)

1. **Download**: [DB Browser for SQLite](https://sqlitebrowser.org/) (Free)
2. **Open**: `chromadb_data/chroma.sqlite3`
3. **Explore Tables**:
   - `collections` - Collection metadata
   - `embeddings` - Document content and vectors
   - `metadata` - Document metadata

### Using SQLite Command Line

```bash
# Connect to database
sqlite3 chromadb_data/chroma.sqlite3

# View all collections
SELECT * FROM collections;

# Count total documents
SELECT COUNT(*) FROM embeddings;

# View sample metadata
SELECT * FROM metadata LIMIT 5;

# Exit SQLite
.exit
```

### Useful SQLite Queries

```sql
-- Collection statistics
SELECT name, metadata FROM collections;

-- Document count by collection
SELECT collection_uuid, COUNT(*) as document_count
FROM embeddings
GROUP BY collection_uuid;

-- Search documents by metadata
SELECT key, string_value
FROM metadata
WHERE key = 'file_name'
LIMIT 10;

-- Find documents by context
SELECT DISTINCT string_value
FROM metadata
WHERE key = 'context_name';
```

## 📄 Method 3: JSON Export Analysis

### Generated JSON Structure

```json
{
  "collection_name": "documentation_collection",
  "document_count": 17,
  "documents": [
    {
      "id": "document_chunk_id",
      "content": "Full document content...",
      "metadata": {
        "chunk_index": "filename_chunk_0",
        "work_item_id": "DocumentationRetrievalMCPServer",
        "file_name": "README.md",
        "title": "Document Title",
        "category": "Project Overview",
        "tags": "tag1,tag2,tag3",
        "context_name": "DocumentationRetrievalMCPServer",
        "file_path": "C:\\path\\to\\file",
        "file_type": "md",
        "processing_strategy": "PersonalDocumentationAssistant_ChromaDB",
        "last_modified": "2025-08-28T12:32:54.151214"
      }
    }
  ]
}
```

### JSON Analysis Tools

- **VS Code**: Open `chromadb_export.json` with syntax highlighting
- **Online JSON Viewers**: JSONFormatter.org, JSONLint.com
- **Command Line**: `cat chromadb_export.json | jq '.documents[0]'` (requires jq)

## 🔧 Method 4: MCP Server Tools (Interactive)

### Start MCP Server

```bash
.\venv\Scripts\Activate.ps1
python run_mcp_server.py
```

### Use in VS Code Copilot

After configuring MCP integration, ask questions like:

- "List all documentation contexts"
- "Show me the document structure"
- "Find documents about ChromaDB"
- "Get the index summary"

## 📊 Understanding Your Data

### Common Metadata Fields

| Field                 | Description               | Example                                   |
| --------------------- | ------------------------- | ----------------------------------------- |
| `id`                  | Unique chunk identifier   | `abc123_chunk_0`                          |
| `file_name`           | Original filename         | `README.md`                               |
| `context_name`        | Work item/project context | `DocumentationRetrievalMCPServer`         |
| `title`               | Document title            | `Project Overview`                        |
| `category`            | Document category         | `Process Guide`                           |
| `tags`                | Searchable tags           | `setup-guide,chromadb-primary`            |
| `chunk_index`         | Chunk position            | `README.md_chunk_0`                       |
| `file_type`           | File extension            | `md`                                      |
| `processing_strategy` | Upload strategy used      | `PersonalDocumentationAssistant_ChromaDB` |
| `last_modified`       | Processing timestamp      | `2025-08-28T12:32:54.151214`              |

### Document Chunking

- Files are split into **chunks** for better search performance
- Each chunk has a **unique ID** with format: `{file_hash}_chunk_{index}`
- **Chunk size**: Typically ~1000 characters with ~200 character overlap
- **Metadata**: Shared across all chunks from the same file

## 🔍 Advanced Inspection Techniques

### Find Specific Content

```python
# Using the inspection script
import chromadb
client = chromadb.PersistentClient(path="./chromadb_data")
collection = client.get_collection("documentation_collection")

# Search for specific content
results = collection.query(
    query_texts=["ChromaDB setup"],
    n_results=5
)

print(f"Found {len(results['ids'][0])} results")
for i, doc_id in enumerate(results['ids'][0]):
    print(f"Document: {doc_id}")
    print(f"Content: {results['documents'][0][i][:200]}...")
```

### Metadata Analysis

```python
# Get all documents and analyze metadata
results = collection.get(include=['metadatas'])

# Analyze tag distribution
tag_counts = {}
for metadata in results['metadatas']:
    if metadata and 'tags' in metadata:
        tags = metadata['tags'].split(',')
        for tag in tags:
            tag_counts[tag.strip()] = tag_counts.get(tag.strip(), 0) + 1

print("Most common tags:")
for tag, count in sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
    print(f"{tag}: {count}")
```

## 🚀 Practical Use Cases

### 1. Content Audit

**Purpose**: Review what content has been indexed
**Method**: Use JSON export + text analysis tools
**Benefits**: Understand coverage, find gaps, verify processing

### 2. Metadata Quality Check

**Purpose**: Ensure consistent tagging and categorization
**Method**: SQL queries on metadata table
**Benefits**: Improve search quality, standardize taxonomy

### 3. Search Performance Analysis

**Purpose**: Understand how content is chunked and embedded
**Method**: Python inspection with similarity analysis
**Benefits**: Optimize chunking strategy, improve relevance

### 4. Data Migration/Backup

**Purpose**: Export data for backup or migration
**Method**: JSON export + SQLite backup
**Benefits**: Data portability, disaster recovery

## 🛠️ Troubleshooting

### Common Issues

**Issue**: "Collection not found"

```bash
# List all available collections
python -c "import chromadb; client = chromadb.PersistentClient(path='./chromadb_data'); print([c.name for c in client.list_collections()])"
```

**Issue**: "Empty results" or "No documents exported"

```bash
# Check document count in collection
python -c "import chromadb; client = chromadb.PersistentClient(path='./chromadb_data'); collection = client.get_collection('documentation_collection'); print(f'Documents: {collection.count()}')"
```

**Issue**: "Database locked" or "Permission denied"

- Stop MCP server: `Ctrl+C` in MCP server terminal
- Close DB Browser if open
- Ensure virtual environment is activated
- Retry export script

### Script Usage Examples

```bash
# Default export (most common)
python export_chromadb_data.py

# Custom collection name
python export_chromadb_data.py "my_custom_collection"

# Custom collection and output file
python export_chromadb_data.py "documentation_collection" "backup_export.json"

# Check if export was successful
python -c "import json; data = json.load(open('chromadb_export.json')); print(f'Exported {data[\"document_count\"]} documents')"
```

### Data Recovery and Backup

```bash
# Backup ChromaDB data directory
cp -r chromadb_data chromadb_data_backup

# Export all data for backup
python export_chromadb_data.py "documentation_collection" "backup_$(date +%Y%m%d).json"

# Verify export contains data
python -c "import json; data = json.load(open('chromadb_export.json')); print(f'Exported {data[\"document_count\"]} documents from {data[\"collection_name\"]}')"

# Quick data check
python -c "import chromadb; client = chromadb.PersistentClient(path='./chromadb_data'); collections = client.list_collections(); [print(f'{c.name}: {c.count()} docs') for c in collections]"
```

## 📋 Best Practices

### Regular Inspection

- **Weekly**: Check document counts and new additions
- **Monthly**: Review metadata quality and tag consistency
- **Before major changes**: Create full JSON export backup

### Data Quality

- **Consistent tagging**: Use standardized tag formats
- **Clear categories**: Maintain category taxonomy
- **Regular cleanup**: Remove outdated or duplicate content

### Performance Monitoring

- **Collection size**: Monitor growth over time
- **Search performance**: Test query response times
- **Storage usage**: Check ChromaDB data directory size

## 📚 Additional Resources

### ChromaDB Documentation

- [ChromaDB Official Docs](https://docs.trychroma.com/)
- [ChromaDB Python Client](https://docs.trychroma.com/reference/py-client)
- [SQLite Documentation](https://www.sqlite.org/docs.html)

### Tools and Utilities

- [DB Browser for SQLite](https://sqlitebrowser.org/) - Free GUI
- [SQLiteStudio](https://sqlitestudio.pl/) - Alternative GUI
- [jq](https://stedolan.github.io/jq/) - JSON processor

## 🔄 Integration with MCP Tools

The inspection methods work alongside MCP server tools:

1. **Inspection** → Understand data structure
2. **MCP Tools** → Query and retrieve documents
3. **JSON Export** → Detailed analysis and backup
4. **SQLite Access** → Advanced queries and reports

This creates a comprehensive data viewing ecosystem for your DocumentationRetrievalMCPServer project.

---

**Created**: August 2025  
**For**: DocumentationRetrievalMCPServer Project  
**Compatibility**: ChromaDB v1.0+, Python 3.8+
