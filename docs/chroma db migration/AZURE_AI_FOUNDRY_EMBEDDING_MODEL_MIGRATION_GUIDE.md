# Azure AI Foundry Migration Guide

## Overview

Migrate from local embedding models to Azure AI Foundry (Azure OpenAI) for improved performance, scalability, and access to state-of-the-art embedding models.

**Benefits**: Latest OpenAI models, enterprise reliability, reduced local compute  
**Trade-offs**: Pay-per-token pricing, internet dependency, API rate limits

## Prerequisites

- Azure AI Foundry Resource with embedding model deployment
- API keys and endpoint configuration
- Current system assessment (embedding model, document count, dimensions)

## Step 1: Azure Configuration

### 1.1 Get Configuration Details

**From Azure AI Foundry Studio** (https://ai.azure.com):

- Project → **Settings** → **Keys and Endpoint**
- Copy **Models API Endpoint** and **API Key**
- Note your **Deployment Name** from **Models + Endpoints**

### 1.2 Endpoint Types

**Project Endpoint** (Management):

```
https://aayush-azure-ai-foundry.services.ai.azure.com/api/projects/FirstProject
```

- Purpose: Project administration and resource management

**Target Endpoint** (Inference):

```
https://aayush-azure-ai-foundry.cognitiveservices.azure.com/openai/deployments/text-embedding-3-large/embeddings?api-version=2023-05-15
```

- Purpose: Direct model inference for embedding generation
- **Use this base URL for configuration**: `https://aayush-azure-ai-foundry.cognitiveservices.azure.com/`

## Step 2: Environment Configuration

Add to your `.env` file:

```env
# Azure AI Foundry Configuration
AZURE_AI_FOUNDRY_ENDPOINT=https://aayush-azure-ai-foundry.cognitiveservices.azure.com/
AZURE_AI_FOUNDRY_EMBEDDING_MODEL_KEY=your-api-key-here  # Azure AI Foundry embedding model API key
EMBEDDING_DEPLOYMENT=text-embedding-3-large  # Update deployment name

# Embedding Configuration
EMBEDDING_PROVIDER=azure_openai  # Change from 'local'
EMBEDDING_DIMENSIONS=3072  # text-embedding-3-large dimensions
```

Install dependencies:

```bash
pip install openai>=1.0.0 azure-identity>=1.12.0
```

## Step 3: Update Existing OpenAI Embedding Service

Instead of creating a new service, update your existing `OpenAIEmbeddingGenerator` class in `src/common/embedding_services/openai_embedding_service.py`:

### 3.1 Update the Constructor

```python
def __init__(self):
    # Load configuration from environment
    self.azure_openai_endpoint = os.getenv('AZURE_AI_FOUNDRY_ENDPOINT')
    self.azure_openai_key = os.getenv('AZURE_AI_FOUNDRY_EMBEDDING_MODEL_KEY')
    self.embedding_deployment = os.getenv('EMBEDDING_DEPLOYMENT', 'text-embedding-3-large')

    # Dynamic embedding dimensions based on model
    embedding_dims = os.getenv('EMBEDDING_DIMENSIONS', '3072')
    self.embedding_dimension = int(embedding_dims)

    # Validate required environment variables
    if not all([self.azure_openai_endpoint, self.azure_openai_key]):
        raise ValueError("Missing required Azure AI Foundry environment variables")

    # Initialize OpenAI service
    self.openai_service = get_openai_service()

    print(f"[INFO] OpenAIEmbeddingGenerator initialized:")
    print(f"   - Endpoint: {self.azure_openai_endpoint}")
    print(f"   - Deployment: {self.embedding_deployment}")
    print(f"   - Dimension: {self.embedding_dimension}")
```

### 3.2 Update Method Names for Clarity

Update existing method names to clearly indicate they are async:

```python
# Update method names to be more explicit
async def generate_embedding_async(self, text: str) -> Optional[List[float]]:
    """Generate embedding for a single text query (async)"""
    # Keep existing implementation

async def generate_embeddings_batch_async(self, texts: List[str], batch_size: int = 16) -> List[List[float]]:
    """Generate embeddings for text chunks in batches (async)"""
    # Keep existing implementation
```

## Step 4: ChromaDB Configuration

The existing `ChromaDBService` class in `src/common/vector_search_services/chromadb_service.py` already supports multiple embedding providers through the embedding service factory pattern. No changes needed to ChromaDB configuration.

**How it works:**

1. **Embedding Service Factory**: The `get_embedding_service()` function in `embedding_service_factory.py` automatically selects the embedding provider based on `EMBEDDING_PROVIDER` environment variable
2. **ChromaDB Integration**: The `ChromaDBService` class uses this factory to get the appropriate embedding service
3. **Service Creation**: Use the existing `get_chromadb_service()` factory function

**Verification:**

```python
# The existing service automatically picks up your new Azure configuration
from src.common.vector_search_services.chromadb_service import get_chromadb_service

# This will use Azure AI Foundry embeddings when EMBEDDING_PROVIDER=azure_openai
chromadb_service = get_chromadb_service()
print(f"ChromaDB service initialized with embedding provider: {os.getenv('EMBEDDING_PROVIDER')}")
```

## Step 5: Testing & Validation

### Connection Test

```python
# test_azure_connection.py
from src.common.embedding_services.openai_embedding_service import get_openai_service
from src.common.vector_search_services.chromadb_service import get_chromadb_service
import asyncio

async def test_connection():
    # Test embedding service directly
    embedding_service = get_openai_service()

    if hasattr(embedding_service, 'test_connection') and embedding_service.test_connection():
        print("✅ Azure AI Foundry connection successful")

        # Test embedding generation
        embeddings = await embedding_service.generate_embeddings_batch(["Test document", "Another test"])
        print(f"✅ Generated {len(embeddings)} embeddings with {len(embeddings[0])} dimensions")

        # Test ChromaDB service integration
        chromadb_service = get_chromadb_service()
        print("✅ ChromaDB service initialized with Azure embeddings")
    else:
        print("❌ Connection failed")

# Run the test
asyncio.run(test_connection())
```

### Migration Script

```python
# migrate_to_azure.py
import os
from src.common.vector_search_services.chromadb_service import get_chromadb_service

def migrate_embeddings():
    # Backup existing data
    os.system("cp -r ./chromadb_data ./chromadb_data_backup")

    # Test new configuration with existing service
    chromadb_service = get_chromadb_service()

    print("Migration complete. Test with a few documents before full migration.")
    print(f"Using embedding provider: {os.getenv('EMBEDDING_PROVIDER')}")

if __name__ == "__main__":
    migrate_embeddings()
```

## Troubleshooting

**Common Issues:**

1. **Authentication Error**: Verify API key and endpoint
2. **Rate Limits**: Modify batch size in code or add delays between requests
3. **Dimension Mismatch**: Update `EMBEDDING_DIMENSIONS` to match your model:
   - `text-embedding-3-large`: 3072 dimensions
   - `text-embedding-3-small`: 1536 dimensions

**Debugging:**

```python
# Check configuration using actual service functions
from src.common.embedding_services.openai_embedding_service import get_openai_service

service = get_openai_service()
print(f"Service type: {type(service).__name__}")
print(f"Embedding provider: {os.getenv('EMBEDDING_PROVIDER')}")
```

## Rollback Plan

To revert to local embeddings:

1. Set `EMBEDDING_PROVIDER=local` in `.env`
2. Restart services
3. Restore from backup if needed: `cp -r ./chromadb_data_backup ./chromadb_data`

## Conclusion

This migration provides access to state-of-the-art embedding models with enterprise reliability. Monitor usage and costs to ensure the setup meets your requirements. The modular design allows easy switching between providers if needed.
