# Work Item Documentation MCP Server - Project Plan

## Project Overview

This project aims to create a Model Context Protocol (MCP) server that enables VS Code agent mode to answer questions about work items using locally stored markdown documentation. The server will integrate with Azure OpenAI and use vector databases for efficient information retrieval.

## Key Requirements

- **MCP Server**: Expose tools for VS Code agent integration
- **Azure OpenAI Integration**: Use Azure OpenAI API for LLM interactions
- **Vector Database**: Store and retrieve work item documentation efficiently
- **Local Documentation**: Process markdown files containing work item information
- **VS Code Integration**: Work seamlessly with VS Code agent mode

## Technical Architecture

### 1. MCP Server Core

- **Language**: Python (using mcp package)
- **Framework**: Model Context Protocol Python SDK
- **Port**: Configurable (default: 3000)
- **Communication**: JSON-RPC over stdio/HTTP

### 2. Vector Database

- **Primary Choice**: Azure Cognitive Search (for both local and production)
- **Why Azure Cognitive Search**:
  - Native vector search capabilities
  - Hybrid search (keyword + semantic)
  - Seamless Azure ecosystem integration
  - Built-in scaling and security
  - Rich filtering and faceting
- **Alternative Options** (if needed):
  - Chroma (lightweight, local only)
  - Pinecone (cloud-based)
  - Weaviate (open-source)
- **Recommendation**: Azure Cognitive Search for consistent experience across environments

### 3. Azure OpenAI Integration

- **Service**: Azure OpenAI Service
- **Models**:
  - **Chat Completion**: GPT-4 or GPT-3.5-turbo for conversational responses and question answering
  - **Embeddings**: text-embedding-ada-002 for vector embeddings
- **Response Generation**: Use chat completion API with system prompts and retrieved context
- **Authentication**: Azure AD or API keys

### 4. Document Processing Pipeline

- **Input**: Local markdown files
- **Processing**: Text chunking, metadata extraction
- **Embedding**: Generate embeddings using Azure OpenAI
- **Storage**: Store in Azure Cognitive Search with metadata
- **Retrieval**: Vector similarity search to find relevant context
- **Response Generation**: Chat completion with retrieved context and system prompts

## Chat Completion Workflow

### 1. Retrieval-Augmented Generation (RAG) Pattern

1. **User Query Processing**: Receive question from VS Code agent
2. **Vector Search**: Generate embedding for query and search Azure Cognitive Search
3. **Context Retrieval**: Retrieve relevant work item chunks and metadata
4. **Prompt Construction**: Build chat completion prompt with:
   - System prompt defining role and behavior
   - Retrieved context from work items
   - User's original question
5. **Chat Completion**: Call Azure OpenAI chat completion API
6. **Response Delivery**: Return structured response to MCP client

### 2. System Prompt Strategy

```
You are a helpful assistant that answers questions about work items based on provided documentation.

Context: {retrieved_context}

Guidelines:
- Answer based only on the provided context
- If information is not available, say so clearly
- Provide specific references to work items when possible
- Be concise but comprehensive
- Use a professional, helpful tone
```

### 3. Chat Completion Benefits

- **Conversational**: Natural dialogue with follow-up questions
- **Context-Aware**: Maintains conversation history
- **Structured Responses**: Can format responses for VS Code display
- **Multi-turn Support**: Handles complex, multi-part queries

## Document Upload Process to Azure Cognitive Search

### 1. Azure Cognitive Search Index Schema

```json
{
  "name": "work-items-index",
  "fields": [
    {
      "name": "id",
      "type": "Edm.String",
      "key": true,
      "searchable": false,
      "filterable": false,
      "retrievable": true,
      "sortable": false,
      "facetable": false
    },
    {
      "name": "content",
      "type": "Edm.String",
      "searchable": true,
      "filterable": false,
      "retrievable": true,
      "sortable": false,
      "facetable": false,
      "analyzer": "standard.lucene"
    },
    {
      "name": "content_vector",
      "type": "Collection(Edm.Single)",
      "searchable": true,
      "filterable": false,
      "retrievable": true,
      "sortable": false,
      "facetable": false,
      "vectorSearchDimensions": 1536,
      "vectorSearchProfileName": "vector-profile"
    },
    {
      "name": "file_path",
      "type": "Edm.String",
      "searchable": false,
      "filterable": true,
      "retrievable": true,
      "sortable": false,
      "facetable": true
    },
    {
      "name": "title",
      "type": "Edm.String",
      "searchable": true,
      "filterable": false,
      "retrievable": true,
      "sortable": false,
      "facetable": false
    },
    {
      "name": "work_item_id",
      "type": "Edm.String",
      "searchable": false,
      "filterable": true,
      "retrievable": true,
      "sortable": false,
      "facetable": true
    },
    {
      "name": "tags",
      "type": "Collection(Edm.String)",
      "searchable": true,
      "filterable": true,
      "retrievable": true,
      "sortable": false,
      "facetable": true
    },
    {
      "name": "last_modified",
      "type": "Edm.DateTimeOffset",
      "searchable": false,
      "filterable": true,
      "retrievable": true,
      "sortable": true,
      "facetable": false
    },
    {
      "name": "chunk_index",
      "type": "Edm.Int32",
      "searchable": false,
      "filterable": true,
      "retrievable": true,
      "sortable": true,
      "facetable": false
    }
  ],
  "vectorSearch": {
    "profiles": [
      {
        "name": "vector-profile",
        "algorithm": "hnsw",
        "vectorizer": null
      }
    ],
    "algorithms": [
      {
        "name": "hnsw",
        "kind": "hnsw",
        "hnswParameters": {
          "metric": "cosine",
          "m": 4,
          "efConstruction": 400,
          "efSearch": 500
        }
      }
    ]
  }
}
```

### 2. Document Processing Pipeline

#### Step 1: File Discovery and Reading

```python
import os
from pathlib import Path
from typing import List, Dict
import frontmatter
import re

def discover_markdown_files(base_path: str) -> List[Path]:
    """Discover all markdown files in the directory tree"""
    return list(Path(base_path).rglob("*.md"))

def extract_metadata(content: str, file_path: Path) -> Dict:
    """Extract metadata from frontmatter or content"""
    try:
        # Try to parse frontmatter
        post = frontmatter.loads(content)
        metadata = post.metadata

        # If no frontmatter, extract from filename and content
        if not metadata:
            metadata = {}

        # Extract title from first heading or filename
        if 'title' not in metadata:
            title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
            metadata['title'] = title_match.group(1) if title_match else file_path.stem

        # Extract work item ID from filename or content
        if 'work_item_id' not in metadata:
            wi_match = re.search(r'(?:WI|workitem|work.item)[-_\s]*(\d+)', str(file_path), re.IGNORECASE)
            if wi_match:
                metadata['work_item_id'] = wi_match.group(1)

        # Set last modified time
        metadata['last_modified'] = file_path.stat().st_mtime

        return metadata

    except Exception as e:
        print(f"Error extracting metadata from {file_path}: {e}")
        return {
            'title': file_path.stem,
            'last_modified': file_path.stat().st_mtime
        }

def read_markdown_file(file_path: Path) -> Dict:
    """Read and parse markdown file with metadata"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract metadata from frontmatter or filename
    metadata = extract_metadata(content, file_path)

    # Remove frontmatter from content if present
    post = frontmatter.loads(content)
    clean_content = post.content if post.metadata else content

    return {
        'content': clean_content,
        'file_path': str(file_path),
        'metadata': metadata
    }
```

#### Step 2: Text Chunking

```python
import re
from typing import List

def chunk_document(content: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """Split document into overlapping chunks with sentence boundaries"""

    # Clean and normalize the content
    content = re.sub(r'\n+', '\n', content)  # Multiple newlines to single
    content = re.sub(r'\s+', ' ', content)   # Multiple spaces to single

    # Split into sentences (improved regex)
    sentence_endings = r'[.!?]+(?:\s+|$)'
    sentences = re.split(f'({sentence_endings})', content)

    # Reconstruct sentences with their endings
    reconstructed_sentences = []
    for i in range(0, len(sentences) - 1, 2):
        if i + 1 < len(sentences):
            reconstructed_sentences.append(sentences[i] + sentences[i + 1])
        else:
            reconstructed_sentences.append(sentences[i])

    chunks = []
    current_chunk = ""
    overlap_buffer = ""

    for sentence in reconstructed_sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        # Check if adding this sentence would exceed chunk size
        potential_chunk = current_chunk + " " + sentence if current_chunk else sentence

        if len(potential_chunk) <= chunk_size:
            current_chunk = potential_chunk
        else:
            # Save current chunk if it has content
            if current_chunk:
                chunks.append(current_chunk.strip())

                # Create overlap buffer from end of current chunk
                words = current_chunk.split()
                if len(words) > 20:  # Only create overlap if chunk is substantial
                    overlap_words = words[-int(overlap/5):]  # Rough word estimate
                    overlap_buffer = " ".join(overlap_words)
                else:
                    overlap_buffer = ""

            # Start new chunk with overlap and current sentence
            current_chunk = overlap_buffer + " " + sentence if overlap_buffer else sentence

    # Add the last chunk
    if current_chunk:
        chunks.append(current_chunk.strip())

    # Filter out very short chunks
    chunks = [chunk for chunk in chunks if len(chunk.strip()) > 50]

    return chunks
```

#### Step 3: Generate Embeddings

```python
from openai import AzureOpenAI
from typing import List
import asyncio
import time

class EmbeddingGenerator:
    def __init__(self, client: AzureOpenAI, deployment_name: str):
        self.client = client
        self.deployment_name = deployment_name

    async def generate_embeddings_batch(self, texts: List[str], batch_size: int = 16) -> List[List[float]]:
        """Generate embeddings for text chunks in batches with rate limiting"""
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]

            try:
                # Add delay to respect rate limits
                if i > 0:
                    await asyncio.sleep(1)  # 1 second between batches

                response = self.client.embeddings.create(
                    input=batch,
                    model=self.deployment_name  # Use your deployment name
                )

                batch_embeddings = [data.embedding for data in response.data]
                all_embeddings.extend(batch_embeddings)

                print(f"Generated embeddings for batch {i//batch_size + 1}/{(len(texts) + batch_size - 1)//batch_size}")

            except Exception as e:
                print(f"Error generating embeddings for batch {i//batch_size + 1}: {e}")
                # Add empty embeddings for failed batch to maintain alignment
                empty_embedding = [0.0] * 1536  # Dimension for text-embedding-ada-002
                all_embeddings.extend([empty_embedding] * len(batch))

        return all_embeddings

# Usage function
async def generate_embeddings(texts: List[str], client: AzureOpenAI, deployment_name: str) -> List[List[float]]:
    """Generate embeddings for text chunks"""
    generator = EmbeddingGenerator(client, deployment_name)
    return await generator.generate_embeddings_batch(texts)
```

#### Step 4: Upload to Azure Cognitive Search

```python
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import SearchIndex
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import HttpResponseError
from typing import List, Dict
from datetime import datetime
import json

class AzureSearchUploader:
    def __init__(self, service_name: str, admin_key: str, index_name: str):
        self.service_endpoint = f"https://{service_name}.search.windows.net"
        self.credential = AzureKeyCredential(admin_key)
        self.index_name = index_name
        self.search_client = SearchClient(
            endpoint=self.service_endpoint,
            index_name=self.index_name,
            credential=self.credential
        )
        self.index_client = SearchIndexClient(
            endpoint=self.service_endpoint,
            credential=self.credential
        )

    async def ensure_index_exists(self):
        """Create the search index if it doesn't exist"""
        try:
            # Check if index exists
            self.index_client.get_index(self.index_name)
            print(f"Index '{self.index_name}' already exists")
        except HttpResponseError as e:
            if e.status_code == 404:
                # Create the index - you would need to define the index schema here
                print(f"Index '{self.index_name}' not found. Please create it first.")
                raise Exception("Index does not exist. Please create it manually first.")
            else:
                raise e

    async def upload_documents_batch(self, documents: List[Dict]) -> bool:
        """Upload documents to Azure Cognitive Search in batches"""
        try:
            await self.ensure_index_exists()

            # Prepare documents for indexing
            search_documents = []

            for doc in documents:
                for i, (chunk, embedding) in enumerate(zip(doc['chunks'], doc['embeddings'])):
                    # Generate unique ID
                    file_name = Path(doc['file_path']).stem
                    doc_id = f"{file_name}_chunk_{i}".replace(" ", "_").replace("/", "_").replace("\\", "_")

                    search_doc = {
                        'id': doc_id,
                        'content': chunk,
                        'content_vector': embedding,
                        'file_path': doc['file_path'],
                        'title': doc['metadata'].get('title', ''),
                        'work_item_id': doc['metadata'].get('work_item_id', ''),
                        'tags': doc['metadata'].get('tags', []),
                        'last_modified': datetime.fromtimestamp(
                            doc['metadata'].get('last_modified', time.time())
                        ).isoformat() + 'Z',
                        'chunk_index': i
                    }
                    search_documents.append(search_doc)

            # Upload in batches (Azure Cognitive Search limit is 1000 docs per batch)
            batch_size = 1000
            total_batches = (len(search_documents) + batch_size - 1) // batch_size

            for i in range(0, len(search_documents), batch_size):
                batch = search_documents[i:i + batch_size]

                try:
                    result = self.search_client.upload_documents(documents=batch)

                    # Check for any failed uploads
                    failed_count = sum(1 for r in result if not r.succeeded)
                    if failed_count > 0:
                        print(f"Batch {i//batch_size + 1}/{total_batches}: {failed_count} documents failed to upload")
                        # Log failed documents for debugging
                        for r in result:
                            if not r.succeeded:
                                print(f"  Failed: {r.key} - {r.error_message}")
                    else:
                        print(f"Successfully uploaded batch {i//batch_size + 1}/{total_batches}: {len(batch)} documents")

                except HttpResponseError as e:
                    print(f"HTTP Error uploading batch {i//batch_size + 1}: {e}")
                    return False
                except Exception as e:
                    print(f"Error uploading batch {i//batch_size + 1}: {e}")
                    return False

            return True

        except Exception as e:
            print(f"Error in upload process: {e}")
            return False

    async def delete_documents_by_file_path(self, file_path: str):
        """Delete all document chunks for a specific file"""
        try:
            # Search for documents with the specific file path
            search_results = self.search_client.search(
                search_text="*",
                filter=f"file_path eq '{file_path}'",
                select="id"
            )

            # Collect document IDs to delete
            docs_to_delete = [{"id": result["id"]} for result in search_results]

            if docs_to_delete:
                result = self.search_client.delete_documents(documents=docs_to_delete)
                successful_deletes = sum(1 for r in result if r.succeeded)
                print(f"Deleted {successful_deletes} document chunks for {file_path}")

        except Exception as e:
            print(f"Error deleting documents for {file_path}: {e}")

# Usage function
async def upload_documents_to_search(
    documents: List[Dict],
    service_name: str,
    admin_key: str,
    index_name: str
) -> bool:
    """Upload processed documents to Azure Cognitive Search"""
    uploader = AzureSearchUploader(service_name, admin_key, index_name)
    return await uploader.upload_documents_batch(documents)
```

### 3. Complete Upload Process

```python
import os
import time
from pathlib import Path
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential
from azure.core.credentials import AzureKeyCredential

async def process_and_upload_markdown_files(
    base_path: str,
    azure_openai_endpoint: str,
    azure_openai_key: str,
    embedding_deployment_name: str,
    search_service_name: str,
    search_admin_key: str,
    search_index_name: str
):
    """Complete pipeline to process and upload markdown files"""

    # Initialize Azure OpenAI client
    openai_client = AzureOpenAI(
        azure_endpoint=azure_openai_endpoint,
        api_key=azure_openai_key,
        api_version="2024-02-01"  # Use latest API version
    )

    # 1. Discover files
    markdown_files = discover_markdown_files(base_path)
    print(f"Found {len(markdown_files)} markdown files")

    if not markdown_files:
        print("No markdown files found!")
        return

    all_documents = []

    for file_path in markdown_files:
        try:
            print(f"Processing {file_path}...")

            # 2. Read and parse file
            file_data = read_markdown_file(file_path)

            # Skip empty files
            if not file_data['content'].strip():
                print(f"Skipping empty file: {file_path}")
                continue

            # 3. Chunk the content
            chunks = chunk_document(file_data['content'])

            if not chunks:
                print(f"No chunks generated for {file_path}")
                continue

            # 4. Generate embeddings
            embeddings = await generate_embeddings(
                chunks,
                openai_client,
                embedding_deployment_name
            )

            # Verify we have embeddings for all chunks
            if len(embeddings) != len(chunks):
                print(f"Warning: Mismatch between chunks ({len(chunks)}) and embeddings ({len(embeddings)}) for {file_path}")
                continue

            # 5. Prepare document
            doc = {
                'file_path': file_data['file_path'],
                'chunks': chunks,
                'embeddings': embeddings,
                'metadata': file_data['metadata']
            }
            all_documents.append(doc)

            print(f"✓ Processed {file_path}: {len(chunks)} chunks")

        except Exception as e:
            print(f"✗ Error processing {file_path}: {e}")
            continue

    if not all_documents:
        print("No documents to upload!")
        return

    # 6. Upload to Azure Cognitive Search
    print(f"\nUploading {len(all_documents)} documents to Azure Cognitive Search...")

    success = await upload_documents_to_search(
        all_documents,
        search_service_name,
        search_admin_key,
        search_index_name
    )

    if success:
        total_chunks = sum(len(doc['chunks']) for doc in all_documents)
        print(f"✓ Upload complete! Indexed {total_chunks} chunks from {len(all_documents)} files")
    else:
        print("✗ Upload failed!")

# Environment-based configuration
async def main():
    """Main function using environment variables"""
    from dotenv import load_dotenv
    load_dotenv()

    # Required environment variables
    base_path = os.getenv('WORK_ITEMS_PATH', './data/work-items')
    azure_openai_endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
    azure_openai_key = os.getenv('AZURE_OPENAI_API_KEY')
    embedding_deployment = os.getenv('AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME')
    search_service_name = os.getenv('AZURE_SEARCH_SERVICE_NAME')
    search_admin_key = os.getenv('AZURE_SEARCH_ADMIN_KEY')
    search_index_name = os.getenv('AZURE_SEARCH_INDEX_NAME', 'work-items-index')

    # Validate required environment variables
    required_vars = {
        'AZURE_OPENAI_ENDPOINT': azure_openai_endpoint,
        'AZURE_OPENAI_API_KEY': azure_openai_key,
        'AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME': embedding_deployment,
        'AZURE_SEARCH_SERVICE_NAME': search_service_name,
        'AZURE_SEARCH_ADMIN_KEY': search_admin_key
    }

    missing_vars = [var for var, value in required_vars.items() if not value]
    if missing_vars:
        print(f"Missing required environment variables: {', '.join(missing_vars)}")
        return

    await process_and_upload_markdown_files(
        base_path=base_path,
        azure_openai_endpoint=azure_openai_endpoint,
        azure_openai_key=azure_openai_key,
        embedding_deployment_name=embedding_deployment,
        search_service_name=search_service_name,
        search_admin_key=search_admin_key,
        search_index_name=search_index_name
    )

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

### 4. Incremental Updates

```python
import hashlib
from datetime import datetime

def file_changed(file_path: Path, stored_hash: str = None) -> bool:
    """Check if file has changed since last processing"""
    with open(file_path, 'rb') as f:
        current_hash = hashlib.md5(f.read()).hexdigest()
    return current_hash != stored_hash

async def incremental_update(
    base_path: str,
    search_client: SearchClient,
    openai_client: AzureOpenAI
):
    """Update only changed files"""

    # Track file hashes in a local database/file
    file_hashes = load_file_hashes()  # Load from storage

    markdown_files = discover_markdown_files(base_path)

    for file_path in markdown_files:
        file_key = str(file_path)
        stored_hash = file_hashes.get(file_key)

        if file_changed(file_path, stored_hash):
            print(f"File changed: {file_path}")

            # Delete old chunks for this file
            await delete_file_chunks(search_client, str(file_path))

            # Process and upload new version
            await process_single_file(file_path, search_client, openai_client)

            # Update hash
            with open(file_path, 'rb') as f:
                file_hashes[file_key] = hashlib.md5(f.read()).hexdigest()

    # Save updated hashes
    save_file_hashes(file_hashes)
```

### 5. Usage Commands

```bash
# Initial upload of all markdown files
python scripts/upload_documents.py --path ./data/work-items --initial

# Incremental update (only changed files)
python scripts/upload_documents.py --path ./data/work-items --incremental

# Force re-upload all files
python scripts/upload_documents.py --path ./data/work-items --force
```

## Implementation Plan

### Phase 1: Project Setup and Foundation (Week 1)

#### 1.1 Initialize MCP Server Project

- [ ] Set up Python project structure with virtual environment
- [ ] Install MCP Python SDK and dependencies
- [ ] Configure development environment (Poetry or pip)
- [ ] Set up basic MCP server skeleton

#### 1.2 Azure OpenAI Setup

- [ ] Create Azure OpenAI resource
- [ ] Configure API keys and endpoints
- [ ] Set up environment variables
- [ ] Test basic API connectivity

#### 1.3 Vector Database Setup

- [ ] Create Azure Cognitive Search service
- [ ] Configure search service and get admin keys
- [ ] Define search index schema for work item documents
- [ ] Set up vector search configuration
- [ ] Test basic indexing and search operations

### Phase 2: Document Processing System (Week 2)

#### 2.1 File System Integration

- [ ] Implement markdown file discovery
- [ ] Create file watcher for automatic updates
- [ ] Handle file metadata extraction
- [ ] Implement incremental processing

#### 2.2 Text Processing Pipeline

- [ ] Implement text chunking strategy
- [ ] Extract work item metadata (title, tags, dates)
- [ ] Generate embeddings using Azure OpenAI
- [ ] Handle error cases and retries

#### 2.3 Vector Database Integration

- [ ] Store document chunks with embeddings in Azure Cognitive Search
- [ ] Implement batch upload for initial document indexing
- [ ] Create incremental update mechanism for changed files
- [ ] Implement similarity search using vector fields
- [ ] Add metadata filtering capabilities (tags, dates, work item IDs)
- [ ] Optimize for query performance and indexing speed

### Phase 3: MCP Tools Implementation (Week 3)

#### 3.1 Core MCP Tools

- [ ] `search_work_items`: Search for relevant work items
- [ ] `get_work_item_details`: Retrieve specific work item information
- [ ] `ask_question`: Answer questions about work items
- [ ] `list_work_items`: List available work items

#### 3.2 Advanced Tools

- [ ] `summarize_work_items`: Generate summaries
- [ ] `find_related_items`: Find related work items
- [ ] `update_knowledge_base`: Refresh document index
- [ ] `get_work_item_history`: Track changes over time

#### 3.3 Tool Integration

- [ ] Implement tool calling interface
- [ ] Add input validation and sanitization
- [ ] Implement proper error handling
- [ ] Add logging and monitoring

### Phase 4: VS Code Integration (Week 4)

#### 4.1 MCP Server Configuration

- [ ] Create VS Code settings configuration
- [ ] Set up MCP server registration
- [ ] Configure agent mode integration
- [ ] Test basic connectivity

#### 4.2 Agent Capabilities

- [ ] Configure natural language processing
- [ ] Implement context-aware responses
- [ ] Add conversation memory
- [ ] Handle multi-turn conversations

#### 4.3 User Experience

- [ ] Create clear command descriptions
- [ ] Implement helpful error messages
- [ ] Add usage examples and documentation
- [ ] Optimize response times

### Phase 5: Testing and Optimization (Week 5)

#### 5.1 Unit Testing

- [ ] Test document processing pipeline
- [ ] Test vector database operations
- [ ] Test Azure OpenAI integration
- [ ] Test MCP tool implementations

#### 5.2 Integration Testing

- [ ] Test end-to-end workflows
- [ ] Test VS Code agent integration
- [ ] Test error handling scenarios
- [ ] Performance testing and optimization

#### 5.3 Documentation

- [ ] API documentation
- [ ] Setup and configuration guide
- [ ] Usage examples
- [ ] Troubleshooting guide

## File Structure

```
WorkItemDocumentationRetriever/
├── src/
│   ├── server/
│   │   ├── __init__.py
│   │   ├── main.py                  # MCP server entry point
│   │   ├── tools/                   # MCP tool implementations
│   │   │   ├── __init__.py
│   │   │   ├── search.py
│   │   │   ├── details.py
│   │   │   ├── question.py
│   │   │   └── list.py
│   │   └── handlers/                # Request handlers
│   │       └── __init__.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── azure_openai.py          # Azure OpenAI integration
│   │   ├── azure_search.py          # Azure Cognitive Search operations
│   │   ├── document_processor.py    # Document processing
│   │   └── file_watcher.py          # File system monitoring
│   ├── types/
│   │   ├── __init__.py
│   │   ├── work_item.py             # Type definitions
│   │   └── mcp_types.py
│   └── utils/
│       ├── __init__.py
│       ├── config.py                # Configuration management
│       ├── logger.py                # Logging utilities
│       └── helpers.py
├── data/
│   └── work-items/                  # Local markdown files
├── config/
│   ├── .env.example                 # Environment variables template
│   └── mcp-config.json              # MCP server configuration
├── tests/
│   ├── __init__.py
│   ├── test_server.py
│   ├── test_tools.py
│   └── test_services.py
├── docs/
├── requirements.txt                 # Python dependencies
├── pyproject.toml                   # Poetry configuration (optional)
├── .gitignore
└── README.md
```

## Azure Services Required

### Essential Services

1. **Azure OpenAI Service**

   - **Purpose**: Chat completion for responses and embeddings for search
   - **Deployments needed**:
     - **GPT-4 or GPT-3.5-turbo** (chat completion for generating responses)
     - **text-embedding-ada-002** (for document and query embeddings)
   - **API Usage**:
     - Chat Completion API for question answering
     - Embeddings API for vector search
   - **Estimated cost**: $10-50/month for moderate usage

2. **Azure Cognitive Search**
   - **Purpose**: Vector database for storing and searching document embeddings
   - **Tier**: Basic ($250/month) or Free (limited features)
   - **Features used**: Vector search, hybrid search, semantic search
   - **Why for local**: Consistent experience, no local database management

### Optional Services

3. **Azure Key Vault** (Recommended)
   - **Purpose**: Secure storage of API keys and secrets
   - **Cost**: ~$0.03 per 10K operations

### Setup Requirements

- Azure subscription with access to Azure OpenAI (requires approval)
- Azure Cognitive Search service in same region as OpenAI for best performance
- Sufficient quotas for chosen models

## Configuration Requirements

### Python Dependencies

```txt
# Core MCP and server dependencies
mcp>=1.0.0
fastapi>=0.104.0
uvicorn>=0.24.0
pydantic>=2.0.0

# Azure OpenAI integration
openai>=1.0.0
azure-identity>=1.15.0

# Azure Cognitive Search
azure-search-documents>=11.4.0
azure-core>=1.29.0

# Document processing
python-markdown>=3.5.0
python-frontmatter>=1.0.0
beautifulsoup4>=4.12.0
pypdf>=3.17.0
python-docx>=0.8.11

# File system monitoring
watchdog>=3.0.0

# Utilities
python-dotenv>=1.0.0
aiofiles>=23.2.1
httpx>=0.25.0
numpy>=1.24.0
pandas>=2.1.0
```

### Environment Variables

```env
AZURE_OPENAI_ENDPOINT=your-endpoint
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_DEPLOYMENT_NAME=your-deployment
AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME=your-embedding-deployment
AZURE_SEARCH_SERVICE_NAME=your-search-service
AZURE_SEARCH_ADMIN_KEY=your-search-admin-key
AZURE_SEARCH_INDEX_NAME=work-items-index
WORK_ITEMS_PATH=./data/work-items
MCP_SERVER_PORT=3000
LOG_LEVEL=info
```

### VS Code Settings

```json
{
  "mcp.servers": {
    "work-items": {
      "command": "python",
      "args": ["src/server/main.py"],
      "env": {
        "WORK_ITEMS_PATH": "./data/work-items"
      }
    }
  }
}
```

## Success Metrics

1. **Functionality**

   - Successfully processes markdown documentation
   - Accurately answers questions about work items
   - Integrates seamlessly with VS Code agent mode

2. **Performance**

   - Query response time < 2 seconds
   - Document processing < 1 minute for 100 files
   - Memory usage < 500MB

3. **Reliability**

   - 99% uptime for MCP server
   - Graceful error handling
   - Automatic recovery from failures

4. **User Experience**
   - Intuitive natural language interface
   - Relevant and accurate responses
   - Fast and responsive interactions

## Risk Mitigation

1. **Azure OpenAI Rate Limits**: Implement exponential backoff and request queuing
2. **Vector Database Performance**: Use appropriate indexing and chunking strategies
3. **File System Changes**: Implement robust file watching and incremental updates
4. **MCP Protocol Changes**: Stay updated with MCP specification updates

## Future Enhancements

1. **Multi-language Support**: Support for additional document formats
2. **Advanced Analytics**: Work item trend analysis and insights
3. **Collaboration Features**: Shared knowledge base across teams
4. **Integration Extensions**: Connect with project management tools
5. **AI Capabilities**: Automated work item categorization and tagging

## Next Steps

1. Review and approve this plan
2. Set up Python development environment (Python 3.9+ recommended)
3. Create virtual environment and install dependencies
4. Begin Phase 1 implementation
5. Establish regular progress check-ins
6. Prepare test data and documentation samples

### Quick Start Commands

```bash
# Create project directory
mkdir WorkItemDocumentationRetriever
cd WorkItemDocumentationRetriever

# Set up Python virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp config/.env.example .env
# Edit .env with your Azure OpenAI credentials

# Run the MCP server
python src/server/main.py
```

---

_This plan provides a comprehensive roadmap for building a production-ready MCP server for work item documentation retrieval and question answering._
