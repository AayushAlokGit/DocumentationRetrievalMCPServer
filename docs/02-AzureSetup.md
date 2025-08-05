# Azure Services Setup

## Required Azure Services

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

## Step-by-Step Setup Guide

### 1. Azure OpenAI Service Setup

1. **Create Azure OpenAI Resource**

   ```bash
   # Using Azure CLI
   az cognitiveservices account create \
     --name "your-openai-service" \
     --resource-group "your-resource-group" \
     --location "eastus" \
     --kind "OpenAI" \
     --sku "S0"
   ```

2. **Deploy Models**

   - Navigate to Azure OpenAI Studio
   - Deploy GPT-4 or GPT-3.5-turbo model
   - Deploy text-embedding-ada-002 model
   - Note deployment names for configuration

3. **Get Keys and Endpoints**

   ```bash
   # Get endpoint and keys
   az cognitiveservices account show \
     --name "your-openai-service" \
     --resource-group "your-resource-group" \
     --query "properties.endpoint"

   az cognitiveservices account keys list \
     --name "your-openai-service" \
     --resource-group "your-resource-group"
   ```

### 2. Azure Cognitive Search Setup

1. **Create Search Service**

   ```bash
   # Using Azure CLI
   az search service create \
     --name "your-search-service" \
     --resource-group "your-resource-group" \
     --location "eastus" \
     --sku "basic"
   ```

2. **Get Admin Keys**

   ```bash
   # Get admin keys
   az search admin-key show \
     --service-name "your-search-service" \
     --resource-group "your-resource-group"
   ```

3. **Create Search Index**
   - Use the index schema provided in `03-DocumentUpload.md`
   - Create index via REST API or Azure Portal

### 3. Azure Key Vault Setup (Optional)

1. **Create Key Vault**

   ```bash
   az keyvault create \
     --name "your-keyvault" \
     --resource-group "your-resource-group" \
     --location "eastus"
   ```

2. **Store Secrets**

   ```bash
   # Store OpenAI key
   az keyvault secret set \
     --vault-name "your-keyvault" \
     --name "openai-api-key" \
     --value "your-openai-key"

   # Store Search admin key
   az keyvault secret set \
     --vault-name "your-keyvault" \
     --name "search-admin-key" \
     --value "your-search-key"
   ```

## Configuration

### Environment Variables

```env
# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=https://your-openai-service.openai.azure.com/
AZURE_OPENAI_API_KEY=your-openai-api-key
AZURE_OPENAI_DEPLOYMENT_NAME=your-gpt4-deployment
AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME=your-embedding-deployment

# Azure Cognitive Search Configuration
AZURE_SEARCH_SERVICE_NAME=your-search-service
AZURE_SEARCH_ADMIN_KEY=your-search-admin-key
AZURE_SEARCH_INDEX_NAME=work-items-index

# Application Configuration
WORK_ITEMS_PATH=./data/work-items
MCP_SERVER_PORT=3000
LOG_LEVEL=info

# Optional: Azure Key Vault
AZURE_KEY_VAULT_URL=https://your-keyvault.vault.azure.net/
```

### Validation Script

```python
# scripts/validate_azure_setup.py
import os
from openai import AzureOpenAI
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential

async def validate_azure_openai():
    """Validate Azure OpenAI connection"""
    client = AzureOpenAI(
        azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT'),
        api_key=os.getenv('AZURE_OPENAI_API_KEY'),
        api_version="2024-02-01"
    )

    try:
        # Test embeddings
        response = client.embeddings.create(
            input=["test"],
            model=os.getenv('AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME')
        )
        print("✓ Azure OpenAI embeddings working")

        # Test chat completion
        response = client.chat.completions.create(
            model=os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME'),
            messages=[{"role": "user", "content": "Hello"}]
        )
        print("✓ Azure OpenAI chat completion working")

    except Exception as e:
        print(f"✗ Azure OpenAI error: {e}")

async def validate_azure_search():
    """Validate Azure Cognitive Search connection"""
    search_client = SearchClient(
        endpoint=f"https://{os.getenv('AZURE_SEARCH_SERVICE_NAME')}.search.windows.net",
        index_name=os.getenv('AZURE_SEARCH_INDEX_NAME'),
        credential=AzureKeyCredential(os.getenv('AZURE_SEARCH_ADMIN_KEY'))
    )

    try:
        # Test search
        results = search_client.search("*", top=1)
        print("✓ Azure Cognitive Search working")
    except Exception as e:
        print(f"✗ Azure Cognitive Search error: {e}")
```

## Cost Optimization Tips

1. **Use Free Tiers for Development**

   - Azure Cognitive Search: Free tier (50MB storage, 3 indexes)
   - Azure OpenAI: Pay per token usage

2. **Monitor Usage**

   - Set up Azure Cost Management alerts
   - Monitor token usage in Azure OpenAI

3. **Optimize Embedding Calls**

   - Cache embeddings locally
   - Use incremental updates only

4. **Right-size Search Service**
   - Start with Basic tier
   - Scale up only when needed
