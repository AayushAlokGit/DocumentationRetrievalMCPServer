# MCP Server Implementation

## Overview

This document provides the implementation details for the MCP (Model Context Protocol) server that will expose tools for VS Code agent integration.

## MCP Tools Definition

# Simplified MCP Server Implementation

## Overview

This document provides a simplified MCP (Model Context Protocol) server implementation that focuses on a single, powerful question-answering tool for VS Code agent integration.

**Work Items Directory Structure:**

- Root directory: `"Work Items"` folder on desktop
- Each subdirectory name serves as the work item identifier
- Markdown files within each subdirectory contain documentation
- The MCP server automatically extracts work item IDs from directory structure

**Key Features:**

- **Smart Work Item Recognition**: Automatically identifies work item IDs from directory names
- **Enhanced Context**: Search results include work item information for better answers
- **Flexible Searching**: Can search across all work items or filter by specific work item ID
- **Source Attribution**: Answers include references to specific work items and files

## Core Tool: ask_question

### Tool Schema Definition

```python
from mcp.server.models import Tool
from mcp.server import Server
from mcp.types import TextContent
from pydantic import BaseModel
from typing import List, Optional

class AskQuestionArgs(BaseModel):
    question: str
    context_limit: Optional[int] = 3

# Global server instance
app = None  # This will be initialized in main.py
```

### Unified Tool Handler

```python
@app.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List the single available MCP tool"""
    return [
        Tool(
            name="ask_question",
            description="Ask a question about work items and get an AI-generated answer with sources",
            inputSchema={
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "Question about work items"
                    },
                    "context_limit": {
                        "type": "integer",
                        "description": "Number of relevant documents to use as context",
                        "default": 3
                    }
                },
                "required": ["question"]
            }
        )
    ]

@app.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> List[TextContent]:
    """Handle tool calls"""
    try:
        if name == "ask_question":
            return await ask_question_tool(AskQuestionArgs(**arguments))
        else:
            raise ValueError(f"Unknown tool: {name}")
    except Exception as e:
        logger.error(f"Error in tool {name}: {e}")
        return [TextContent(type="text", text=f"Error executing {name}: {str(e)}")]
```

### Tool Implementation

```python
async def ask_question_tool(args: AskQuestionArgs) -> List[TextContent]:
    """Answer questions using RAG pattern"""
    try:
        # 1. Generate embedding for question
        embedding = await generate_query_embedding(args.question)

        # 2. Search for relevant context
        context_results = await vector_search(
            embedding=embedding,
            limit=args.context_limit
        )

        if not context_results:
            return [TextContent(
                type="text",
                text="I couldn't find any relevant information in the work items to answer your question. Please try rephrasing your question or check if the relevant documentation has been uploaded."
            )]

        # 3. Build context string with work item information
        context = "\n\n".join([
            f"**Work Item {result['work_item_id']}** - {result['title']} ({result['file_path']}):\n{result['content']}"
            for result in context_results
        ])

        # 4. Generate answer using chat completion
        answer = await generate_chat_completion(
            question=args.question,
            context=context
        )

        # 5. Include sources with work item IDs
        sources = "\n\n**Sources:**\n" + "\n".join([
            f"- **Work Item {result['work_item_id']}**: {result['title']} ({result['file_path']})"
            for result in context_results
        ])

        return [TextContent(
            type="text",
            text=f"{answer}{sources}"
        )]

    except Exception as e:
        logger.error(f"Error in ask_question_tool: {e}")
        return [TextContent(type="text", text=f"Error answering question: {str(e)}")]
```

## Simplified Server Implementation

```python
# src/server/main.py
import asyncio
import logging
from mcp.server import Server
from mcp.server.models import InitializationOptions, NotificationOptions
from mcp.types import Resource, ResourceContents, TextResourceContents, TextContent
import mcp.server.stdio
from services.azure_openai import AzureOpenAIService
from services.azure_search import AzureSearchService
from utils.config import load_config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize services
config = load_config()
openai_service = AzureOpenAIService(config)
search_service = AzureSearchService(config)

app = Server("work-items-mcp")

@app.list_resources()
async def handle_list_resources():
    """List available resources"""
    return [
        Resource(
            uri="work-items://search",
            name="Work Items Search",
            description="Search and query work items documentation",
            mimeType="text/plain"
        )
    ]

@app.read_resource()
async def handle_read_resource(uri: str):
    """Read resource content"""
    if uri == "work-items://search":
        # Return summary of available work items
        summary = await get_work_items_summary()
        return ResourceContents(
            contents=[TextResourceContents(
                uri=uri,
                mimeType="text/plain",
                text=summary
            )]
        )
    else:
        raise ValueError(f"Unknown resource: {uri}")

async def generate_query_embedding(query: str):
    """Generate embedding for search query"""
    return await openai_service.generate_embedding(query)

async def vector_search(embedding, limit=5, work_item_id=None, tags=None):
    """Perform vector search in Azure Cognitive Search"""
    return await search_service.vector_search(
        embedding=embedding,
        limit=limit,
        work_item_id=work_item_id,
        tags=tags
    )

async def get_work_items_summary():
    """Get summary of available work items from Azure Search"""
    return await search_service.get_work_items_summary()

async def generate_chat_completion(question: str, context: str):
    """Generate answer using chat completion"""
    system_prompt = """You are a helpful assistant that answers questions about work items based on provided documentation.

The work items are organized with unique identifiers (like WI-12345, BUG-67890, FEATURE-11111, etc.) and each has associated documentation files.

Context: {context}

Guidelines:
- Answer based only on the provided context
- If information is not available, say so clearly
- Always reference specific work item IDs when available in your answer
- Provide specific references to work items when possible
- Be concise but comprehensive
- Use a professional, helpful tone"""

    return await openai_service.chat_completion(
        system_prompt=system_prompt.format(context=context),
        user_message=question
    )

async def main():
    """Main server entry point"""
    try:
        # Initialize services
        await openai_service.initialize()
        await search_service.initialize()

        logger.info("Work Items MCP Server starting...")

        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await app.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="work-items",
                    server_version="1.0.0",
                    capabilities=app.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={}
                    )
                )
            )
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
```

## Service Implementations

### Azure OpenAI Service

```python
# src/services/azure_openai.py
from openai import AzureOpenAI
from typing import List

class AzureOpenAIService:
    def __init__(self, config):
        self.config = config
        self.client = None

    async def initialize(self):
        """Initialize the Azure OpenAI client"""
        self.client = AzureOpenAI(
            azure_endpoint=self.config.azure_openai_endpoint,
            api_key=self.config.azure_openai_key,
            api_version="2024-02-01"
        )

    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text"""
        response = self.client.embeddings.create(
            input=[text],
            model=self.config.embedding_deployment_name
        )
        return response.data[0].embedding

    async def chat_completion(self, system_prompt: str, user_message: str) -> str:
        """Generate chat completion response"""
        response = self.client.chat.completions.create(
            model=self.config.chat_deployment_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        return response.choices[0].message.content
```

### Azure Search Service

```python
# src/services/azure_search.py
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from typing import List, Optional

class AzureSearchService:
    def __init__(self, config):
        self.config = config
        self.search_client = None

    async def initialize(self):
        """Initialize the search client"""
        self.search_client = SearchClient(
            endpoint=f"https://{self.config.search_service_name}.search.windows.net",
            index_name=self.config.search_index_name,
            credential=AzureKeyCredential(self.config.search_admin_key)
        )

    async def vector_search(
        self,
        embedding: List[float],
        limit: int = 5,
        work_item_id: Optional[str] = None,
        tags: Optional[List[str]] = None
    ):
        """Perform vector search with enhanced work item filtering"""
        search_params = {
            "vectors": [{
                "value": embedding,
                "k_nearest_neighbors": limit,
                "fields": "content_vector"
            }],
            "select": "id,content,title,file_path,work_item_id,tags,last_modified,chunk_index",
            "top": limit
        }

        # Add filters for work item structure
        filters = []
        if work_item_id:
            filters.append(f"work_item_id eq '{work_item_id}'")
        if tags:
            tag_filters = " or ".join([f"tags/any(t: t eq '{tag}')" for tag in tags])
            filters.append(f"({tag_filters})")

        if filters:
            search_params["filter"] = " and ".join(filters)

        # Execute search
        results = self.search_client.search(**search_params)

        # Process results to include work item context
        processed_results = []
        for result in results:
            result_dict = dict(result)
            # Ensure work_item_id is available for context
            if 'work_item_id' not in result_dict or not result_dict['work_item_id']:
                # Extract from file path as fallback
                file_path = result_dict.get('file_path', '')
                if 'Work Items' in file_path:
                    parts = file_path.split('\\')
                    work_items_idx = parts.index('Work Items') if 'Work Items' in parts else -1
                    if work_items_idx >= 0 and work_items_idx + 1 < len(parts):
                        result_dict['work_item_id'] = parts[work_items_idx + 1]

            processed_results.append(result_dict)

        return processed_results

    async def get_work_items_summary(self):
        """Get summary of available work items"""
        try:
            # Get unique work items with count
            search_params = {
                "search": "*",
                "facets": ["work_item_id"],
                "top": 0  # We only want facets
            }

            results = self.search_client.search(**search_params)
            facets = results.get_facets()

            if 'work_item_id' in facets:
                work_items = facets['work_item_id']
                summary_lines = [f"Available Work Items ({len(work_items)} total):"]
                for item in work_items:
                    summary_lines.append(f"- {item['value']}: {item['count']} documents")
                return "\n".join(summary_lines)
            else:
                return "No work items found in the index."

        except Exception as e:
            return f"Error getting work items summary: {str(e)}"
```

## Configuration```python

# src/utils/config.py

import os
from dataclasses import dataclass
from dotenv import load_dotenv

@dataclass
class Config: # Azure OpenAI
azure_openai_endpoint: str
azure_openai_key: str
chat_deployment_name: str
embedding_deployment_name: str

    # Azure Search
    search_service_name: str
    search_admin_key: str
    search_index_name: str

    # Application
    PERSONAL_DOCUMENTATION_ROOT_DIRECTORY: str
    log_level: str

def load_config() -> Config:
"""Load configuration from environment variables"""
load_dotenv()

    return Config(
        azure_openai_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT'),
        azure_openai_key=os.getenv('AZURE_OPENAI_API_KEY'),
        chat_deployment_name=os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME'),
        embedding_deployment_name=os.getenv('AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME'),
        search_service_name=os.getenv('AZURE_SEARCH_SERVICE_NAME'),
        search_admin_key=os.getenv('AZURE_SEARCH_ADMIN_KEY'),
        search_index_name=os.getenv('AZURE_SEARCH_INDEX_NAME', 'work-items-index'),
        PERSONAL_DOCUMENTATION_ROOT_DIRECTORY=os.getenv('PERSONAL_DOCUMENTATION_ROOT_DIRECTORY', r'C:\Users\YourUsername\Desktop\Work Items'),
        log_level=os.getenv('LOG_LEVEL', 'INFO')
    )

````

## VS Code Integration

### MCP Server Configuration for VS Code

Add this to your VS Code settings or MCP configuration:

```json
{
  "mcp.servers": {
    "work-items": {
      "command": "python",
      "args": ["src/server/main.py"],
      "cwd": "/path/to/WorkItemDocumentationRetriever",
      "env": {
        "PERSONAL_DOCUMENTATION_ROOT_DIRECTORY": "C:\\Users\\YourUsername\\Desktop\\Work Items"
      }
    }
  }
}
```

**Important**: Update the `PERSONAL_DOCUMENTATION_ROOT_DIRECTORY` to point to your actual "Work Items" directory on desktop.`

## Usage Examples

### Example 1: General Question
**VS Code Prompt**: "What authentication issues have been documented?"

**MCP Tool Call**:
```json
{
  "tool": "ask_question",
  "arguments": {
    "question": "What authentication issues have been documented?",
    "context_limit": 3
  }
}
```

**Expected Response**:
```
Based on the work item documentation, here are the authentication issues found:

**Work Item WI-12345** had OAuth token expiration problems where users were getting 401 errors after 1 hour. The solution involved implementing automatic token refresh...

**Work Item BUG-67890** documented LDAP integration failures where users couldn't authenticate against Active Directory...

**Sources:**
- **Work Item WI-12345**: OAuth Implementation Guide (C:\Users\...\Desktop\Work Items\WI-12345\auth-issues.md)
- **Work Item BUG-67890**: LDAP Troubleshooting (C:\Users\...\Desktop\Work Items\BUG-67890\ldap-fix.md)
```

### Example 2: Work Item Specific Question
**VS Code Prompt**: "Tell me about the implementation details for work item FEATURE-11111"

**MCP Tool Call**:
```json
{
  "tool": "ask_question",
  "arguments": {
    "question": "Tell me about the implementation details for work item FEATURE-11111",
    "context_limit": 5
  }
}
```

### Example 3: Technical Deep Dive
**VS Code Prompt**: "How do I configure the new search feature?"

The MCP server will automatically find relevant documentation across all work items and provide comprehensive answers with proper work item attribution.

## Simplified Testing

```python
# tests/test_mcp_server.py
import pytest
import asyncio
from src.server.main import app
from mcp.client import ClientSession
from mcp.client.stdio import stdio_client

@pytest.mark.asyncio
async def test_ask_question():
    """Test the ask_question tool"""
    async with stdio_client() as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Test basic question
            result = await session.call_tool(
                "ask_question",
                {"question": "How do I fix authentication problems?"}
            )

            assert result is not None
            assert len(result) > 0
            assert isinstance(result[0].text, str)
            # Should contain either answer or "couldn't find" message
            assert len(result[0].text) > 0

@pytest.mark.asyncio
async def test_ask_question_with_context_limit():
    """Test the ask_question tool with custom context limit"""
    async with stdio_client() as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Test with custom context limit
            result = await session.call_tool(
                "ask_question",
                {
                    "question": "What are the common issues?",
                    "context_limit": 5
                }
            )

            assert result is not None
            assert len(result) > 0

@pytest.mark.asyncio
async def test_ask_question_no_results():
    """Test asking question that should return no results"""
    async with stdio_client() as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Test with question unlikely to have results
            result = await session.call_tool(
                "ask_question",
                {"question": "xyzabc123 nonexistent topic"}
            )

            assert result is not None
            assert "couldn't find" in result[0].text.lower() or "no" in result[0].text.lower()
```
````
