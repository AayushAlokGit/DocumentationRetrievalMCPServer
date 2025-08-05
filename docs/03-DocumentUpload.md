# Document Upload Process

## Overview

This document provides detailed instructions for uploading local markdown files to Azure Cognitive Search, including code examples and implementation details.

## Azure Cognitive Search Index Schema

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

## Document Processing Pipeline

### Step 1: File Discovery and Reading

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

### Step 2: Text Chunking

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

### Step 3: Generate Embeddings

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

### Step 4: Upload to Azure Cognitive Search

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

## Complete Upload Script

```python
# scripts/upload_documents.py
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

## Usage Commands

```bash
# Initial upload of all markdown files
python scripts/upload_documents.py --path ./data/work-items --initial

# Incremental update (only changed files)
python scripts/upload_documents.py --path ./data/work-items --incremental

# Force re-upload all files
python scripts/upload_documents.py --path ./data/work-items --force
```

## Incremental Updates

For incremental updates, see the implementation in `04-IncrementalUpdates.md`.
