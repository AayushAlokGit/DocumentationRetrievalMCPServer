# MCP Server Implementation

## Overview

This document provides the implementation details for the MCP (Model Context Protocol) server that will expose tools for VS Code agent integration.

## MCP Tools Definition

### Core Tools

#### Tools Schema Definitions

```python
from mcp.server.models import Tool
from mcp.server import Server
from mcp.types import TextContent
from pydantic import BaseModel
from typing import List, Optional

class SearchWorkItemsArgs(BaseModel):
    query: str
    limit: Optional[int] = 5
    work_item_id: Optional[str] = None
    tags: Optional[List[str]] = None

class AskQuestionArgs(BaseModel):
    question: str
    context_limit: Optional[int] = 3

class GetWorkItemDetailsArgs(BaseModel):
    work_item_id: str

class ListWorkItemsArgs(BaseModel):
    limit: Optional[int] = 10
    tags: Optional[List[str]] = None

# Global variable will be defined in main.py
app = None  # This will be initialized in main.py
```

#### Unified Tool Handlers

```python
@app.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List all available MCP tools"""
    return [
        Tool(
            name="search_work_items",
            description="Search for relevant work items using natural language query",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural language search query"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                        "default": 5
                    },
                    "work_item_id": {
                        "type": "string",
                        "description": "Filter by specific work item ID"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter by tags"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="ask_question",
            description="Ask a question about work items and get an AI-generated answer",
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
        ),
        Tool(
            name="get_work_item_details",
            description="Get detailed information about a specific work item",
            inputSchema={
                "type": "object",
                "properties": {
                    "work_item_id": {
                        "type": "string",
                        "description": "The work item ID to retrieve details for"
                    }
                },
                "required": ["work_item_id"]
            }
        ),
        Tool(
            name="list_work_items",
            description="List available work items with metadata",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of work items to return",
                        "default": 10
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter by tags"
                    }
                }
            }
        )
    ]

@app.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> List[TextContent]:
    """Handle tool calls"""
    try:
        if name == "search_work_items":
            return await search_work_items_tool(SearchWorkItemsArgs(**arguments))
        elif name == "ask_question":
            return await ask_question_tool(AskQuestionArgs(**arguments))
        elif name == "get_work_item_details":
            return await get_work_item_details_tool(GetWorkItemDetailsArgs(**arguments))
        elif name == "list_work_items":
            return await list_work_items_tool(ListWorkItemsArgs(**arguments))
        else:
            raise ValueError(f"Unknown tool: {name}")
    except Exception as e:
        logger.error(f"Error in tool {name}: {e}")
        return [TextContent(type="text", text=f"Error executing {name}: {str(e)}")]
```

#### Tool Implementation Functions

#### 1. search_work_items

```python
async def search_work_items_tool(args: SearchWorkItemsArgs) -> List[TextContent]:
    """Search for work items using vector similarity"""
    try:
        # Generate embedding for query
        embedding = await generate_query_embedding(args.query)

        # Search Azure Cognitive Search
        results = await vector_search(
            embedding=embedding,
            limit=args.limit,
            work_item_id=args.work_item_id,
            tags=args.tags
        )

        if not results:
            return [TextContent(type="text", text="No relevant work items found for your query.")]

        # Format results
        formatted_results = []
        for result in results:
            formatted_results.append(
                TextContent(
                    type="text",
                    text=f"**{result['title']}** (Score: {result['@search.score']:.2f})\n"
                         f"File: {result['file_path']}\n"
                         f"Content: {result['content'][:200]}...\n"
                         f"Work Item ID: {result.get('work_item_id', 'N/A')}\n"
                         f"Tags: {', '.join(result.get('tags', []))}\n\n"
                )
            )

        return formatted_results

    except Exception as e:
        return [TextContent(type="text", text=f"Error searching work items: {str(e)}")]
```

#### 2. ask_question

Answer questions about work items using RAG pattern.

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

        # 3. Build context string
        context = "\n\n".join([
            f"From {result['title']} ({result['file_path']}):\n{result['content']}"
            for result in context_results
        ])

        # 4. Generate answer using chat completion
        answer = await generate_chat_completion(
            question=args.question,
            context=context
        )

        # 5. Include sources
        sources = "\n\nSources:\n" + "\n".join([
            f"- {result['title']} ({result['file_path']})"
            for result in context_results
        ])

        return [TextContent(
            type="text",
            text=f"{answer}{sources}"
        )]

    except Exception as e:
        return [TextContent(type="text", text=f"Error answering question: {str(e)}")]
```

#### 3. get_work_item_details

Get detailed information about a specific work item.

```python
class GetWorkItemDetailsArgs(BaseModel):
    work_item_id: str

async def get_work_item_details_tool(args: GetWorkItemDetailsArgs) -> List[TextContent]:
    """Get detailed information about a specific work item"""
    try:
        # Search for all chunks related to this work item
        results = await search_by_work_item_id(args.work_item_id)

        if not results:
            return [TextContent(
                type="text",
                text=f"No information found for work item ID: {args.work_item_id}"
            )]

        # Group by file path and combine chunks
        files = {}
        for result in results:
            file_path = result['file_path']
            if file_path not in files:
                files[file_path] = {
                    'title': result['title'],
                    'chunks': [],
                    'tags': result.get('tags', []),
                    'last_modified': result.get('last_modified')
                }
            files[file_path]['chunks'].append({
                'content': result['content'],
                'chunk_index': result['chunk_index']
            })

        # Format response
        response_parts = []
        for file_path, file_data in files.items():
            # Sort chunks by index
            sorted_chunks = sorted(file_data['chunks'], key=lambda x: x['chunk_index'])
            combined_content = "\n\n".join([chunk['content'] for chunk in sorted_chunks])

            response_parts.append(
                f"**{file_data['title']}**\n"
                f"File: {file_path}\n"
                f"Tags: {', '.join(file_data['tags'])}\n"
                f"Last Modified: {file_data['last_modified']}\n\n"
                f"{combined_content}\n\n---\n"
            )

        return [TextContent(type="text", text="\n".join(response_parts))]

    except Exception as e:
        return [TextContent(type="text", text=f"Error getting work item details: {str(e)}")]
```

#### 4. list_work_items

List available work items with metadata.

```python
class ListWorkItemsArgs(BaseModel):
    limit: Optional[int] = 10
    tags: Optional[List[str]] = None

async def list_work_items_tool(args: ListWorkItemsArgs) -> List[TextContent]:
    """List available work items"""
    try:
        # Get unique work items
        results = await get_unique_work_items(
            limit=args.limit,
            tags=args.tags
        )

        if not results:
            return [TextContent(type="text", text="No work items found")]

        # Format as table
        table_rows = ["| Title | Work Item ID | Tags | File Path |"]
        table_rows.append("|-------|--------------|------|-----------|")

        for result in results:
            tags_str = ", ".join(result.get('tags', []))
            table_rows.append(
                f"| {result['title']} | {result.get('work_item_id', 'N/A')} | {tags_str} | {result['file_path']} |"
            )

        return [TextContent(type="text", text="\n".join(table_rows))]

    except Exception as e:
        return [TextContent(type="text", text=f"Error listing work items: {str(e)}")]
```

## Server Implementation

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

async def generate_chat_completion(question: str, context: str):
    """Generate answer using chat completion"""
    system_prompt = """You are a helpful assistant that answers questions about work items based on provided documentation.

Context: {context}

Guidelines:
- Answer based only on the provided context
- If information is not available, say so clearly
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
        """Perform vector search"""
        search_params = {
            "vectors": [{
                "value": embedding,
                "k_nearest_neighbors": limit,
                "fields": "content_vector"
            }],
            "select": "id,content,title,file_path,work_item_id,tags,last_modified",
            "top": limit
        }

        # Add filters
        filters = []
        if work_item_id:
            filters.append(f"work_item_id eq '{work_item_id}'")
        if tags:
            tag_filters = " or ".join([f"tags/any(t: t eq '{tag}')" for tag in tags])
            filters.append(f"({tag_filters})")

        if filters:
            search_params["filter"] = " and ".join(filters)

        results = self.search_client.search(**search_params)
        return [dict(result) for result in results]

    async def search_by_work_item_id(self, work_item_id: str):
        """Search for all documents with a specific work item ID"""
        search_params = {
            "search_text": "*",
            "filter": f"work_item_id eq '{work_item_id}'",
            "select": "id,content,title,file_path,work_item_id,tags,last_modified,chunk_index",
            "top": 50,  # Get all chunks for the work item
            "order_by": "chunk_index asc"
        }

        results = self.search_client.search(**search_params)
        return [dict(result) for result in results]

    async def get_unique_work_items(self, limit: int = 10, tags: List[str] = None):
        """Get unique work items with their metadata"""
        # Use faceted search to get unique work items
        search_params = {
            "search_text": "*",
            "facets": ["work_item_id", "title", "tags"],
            "select": "title,file_path,work_item_id,tags",
            "top": 0  # We only want facets, not results
        }

        if tags:
            tag_filters = " or ".join([f"tags/any(t: t eq '{tag}')" for tag in tags])
            search_params["filter"] = f"({tag_filters})"

        results = self.search_client.search(**search_params)

        # Process facets to get unique work items
        unique_items = []
        if hasattr(results, 'get_facets'):
            facets = results.get_facets()
            # Implementation depends on facet structure
            # This is a simplified version
            pass

        # Alternative approach: use group by or distinct query
        search_params = {
            "search_text": "*",
            "select": "title,file_path,work_item_id,tags",
            "top": limit * 3  # Get more results to filter duplicates
        }

        if tags:
            tag_filters = " or ".join([f"tags/any(t: t eq '{tag}')" for tag in tags])
            search_params["filter"] = f"({tag_filters})"

        results = self.search_client.search(**search_params)

        # Deduplicate by work_item_id
        seen_items = set()
        unique_items = []

        for result in results:
            item_id = result.get('work_item_id', result.get('title', ''))
            if item_id and item_id not in seen_items:
                seen_items.add(item_id)
                unique_items.append(dict(result))
                if len(unique_items) >= limit:
                    break

        return unique_items
```

## Helper Functions

```python
# Additional helper functions used by the MCP server

async def get_work_items_summary():
    """Generate a summary of available work items"""
    try:
        # Get basic statistics about work items
        search_results = await search_service.get_unique_work_items(limit=100)

        total_items = len(search_results)

        # Collect tags
        all_tags = set()
        for item in search_results:
            if item.get('tags'):
                all_tags.update(item['tags'])

        summary = f"""Work Items Documentation Summary

Total Work Items: {total_items}
Available Tags: {', '.join(sorted(all_tags)) if all_tags else 'None'}

Recent Work Items:
"""

        # Add recent items (first 5)
        for item in search_results[:5]:
            title = item.get('title', 'Untitled')
            work_item_id = item.get('work_item_id', 'N/A')
            tags = ', '.join(item.get('tags', []))
            summary += f"- {title} (ID: {work_item_id}) [Tags: {tags}]\n"

        return summary

    except Exception as e:
        return f"Error generating summary: {str(e)}"
```

## Configuration

```python
# src/utils/config.py
import os
from dataclasses import dataclass
from dotenv import load_dotenv

@dataclass
class Config:
    # Azure OpenAI
    azure_openai_endpoint: str
    azure_openai_key: str
    chat_deployment_name: str
    embedding_deployment_name: str

    # Azure Search
    search_service_name: str
    search_admin_key: str
    search_index_name: str

    # Application
    work_items_path: str
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
        work_items_path=os.getenv('WORK_ITEMS_PATH', './data/work-items'),
        log_level=os.getenv('LOG_LEVEL', 'INFO')
    )
```

## VS Code Integration

### MCP Server Configuration

```json
{
  "mcp.servers": {
    "work-items": {
      "command": "python",
      "args": ["src/server/main.py"],
      "cwd": "/path/to/WorkItemDocumentationRetriever",
      "env": {
        "WORK_ITEMS_PATH": "./data/work-items"
      }
    }
  }
}
```

## Testing

```python
# tests/test_mcp_server.py
import pytest
import asyncio
from src.server.main import app
from mcp.client import ClientSession
from mcp.client.stdio import stdio_client

@pytest.mark.asyncio
async def test_search_work_items():
    """Test the search_work_items tool"""
    async with stdio_client() as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Test search
            result = await session.call_tool(
                "search_work_items",
                {"query": "authentication issues"}
            )

            assert result is not None
            assert len(result) > 0

@pytest.mark.asyncio
async def test_ask_question():
    """Test the ask_question tool"""
    async with stdio_client() as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Test question
            result = await session.call_tool(
                "ask_question",
                {"question": "How do I fix authentication problems?"}
            )

            assert result is not None
            assert "authentication" in result[0].text.lower()
```
