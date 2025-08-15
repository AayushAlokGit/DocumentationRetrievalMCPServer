# Refined MCP Tools Plan: Use Case Agnostic Design

## 🎯 **Executive Summary**

This document outlines the strategy to transform the MCP server from a work item-specific system to a **use case agnostic documentation querying platform**. The goal is to leverage the existing generic Azure Cognitive Search index structure whi expressions.append(f"file_name eq '{filters['file_name']}'")

        if filters.get("file_type"):
            expressions.append(f"file_type eq '{filters['file_type']}'")

        # Tag filtering - CORRECTED: tags stored as comma-separated string
        if filters.get("tags"):
            tags = filters["tags"] if isinstance(filters["tags"], list) else [filters["tags"]]
            if len(tags) == 1:
                # Use search.ismatch for partial string matching within comma-separated string
                expressions.append(f"search.ismatch('{tags[0]}', 'tags')")
            else:
                # For multiple tags, create OR expressions using search.ismatch
                tag_exprs = [f"search.ismatch('{tag}', 'tags')" for tag in tags]
                expressions.append(f"({' or '.join(tag_exprs)})")

        # Chunk-specific filtering
        if filters.get("chunk_pattern"):
            expressions.append(f"chunk_index eq '{filters['chunk_pattern']}''")ools that can intelligently query any type of documentation without being tied to specific use cases.

---

## 🔍 **Current Problem Analysis**

### **Current State Issues**

- **Tool Names**: Hardcoded "work_item" terminology throughout tool names and descriptions
- **Schema Constraints**: Tool schemas assume work item structure (`work_item_id`, work item-specific terminology)
- **Limited Flexibility**: Cannot easily adapt to other document types (API docs, legal documents, project documentation, etc.)
- **Tool Proliferation**: 8 tools with overlapping functionality but minor parameter differences

### **Existing Strengths to Leverage**

- **Generic Index Schema**: Already uses generic field names (`context_id`, `context_name`, `category`)
- **Strategy Pattern**: Document processing pipeline is already use case agnostic
- **Robust Azure Search**: Powerful search infrastructure with multiple search types
- **Rich Metadata**: Comprehensive document metadata extraction and storage

---

## 🚀 **Refined Tool Architecture**

### **Core Design Principles**

1. **Use Case Agnostic**: Tools should work regardless of document type or domain
2. **Semantic Clarity**: Tool names and descriptions should be generic and intuitive
3. **Minimal Cognitive Load**: Reduce number of tools while maintaining functionality
4. **LLM Friendly**: Easy for AI agents to understand and select appropriate tools
5. **Extensible**: Support future document types without tool changes

### **Simplified Tool Set: 4 Universal Tools**

| Tool                             | Purpose                   | Replaces                | Use Case Agnostic Design       |
| -------------------------------- | ------------------------- | ----------------------- | ------------------------------ |
| **`search_documents`**           | Universal document search | 6 search tools          | Works for any document type    |
| **`get_document_contexts`**      | List available contexts   | `get_work_item_list`    | Generic context discovery      |
| **`get_index_summary`**          | System overview           | `get_work_item_summary` | General index statistics       |
| **`explore_document_structure`** | Navigate documents        | New utility             | Universal document exploration |

---

## 🛠️ **Tool Specifications**

### **1. Universal `search_documents` Tool**

```json
{
  "name": "search_documents",
  "description": "Search across all indexed documents with flexible filtering and multiple search modes. Supports any document type including work items, API documentation, legal documents, project files, and more.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "Search query - can be keywords, natural language questions, or concepts",
        "required": true
      },
      "search_type": {
        "type": "string",
        "enum": ["text", "vector", "hybrid", "semantic"],
        "description": "Search algorithm: 'text' for exact keywords, 'vector' for semantic similarity, 'hybrid' for balanced relevance, 'semantic' for advanced understanding",
        "default": "hybrid"
      },
      "filters": {
        "type": "object",
        "description": "Optional filters to narrow search scope",
        "properties": {
          "context_id": {
            "type": ["string", "array"],
            "description": "Filter by context ID(s) - work item ID, project ID, contract ID, etc."
          },
          "context_name": {
            "type": "string",
            "description": "Filter by context name - work item title, project name, document title, etc."
          },
          "category": {
            "type": ["string", "array"],
            "description": "Filter by document category - technical, legal, design, api, etc."
          },
          "file_name": {
            "type": "string",
            "description": "Filter by specific file name"
          },
          "file_type": {
            "type": "string",
            "description": "Filter by file extension - md, txt, docx, pdf, etc."
          },
          "tags": {
            "type": ["string", "array"],
            "description": "Filter by document tags or labels"
          },
          "chunk_pattern": {
            "type": "string",
            "description": "Filter by specific chunk identifier for precise document sections"
          },
          "chunk_range": {
            "type": "object",
            "properties": {
              "start": { "type": "integer", "minimum": 0 },
              "end": { "type": "integer", "minimum": 0 }
            },
            "description": "Filter by chunk number range within a document"
          }
        }
      },
      "max_results": {
        "type": "integer",
        "description": "Maximum number of results to return",
        "default": 10,
        "minimum": 1,
        "maximum": 50
      },
      "include_content": {
        "type": "boolean",
        "description": "Whether to include full document content in results",
        "default": true
      }
    },
    "required": ["query"]
  }
}
```

### **2. `get_document_contexts` Tool**

```json
{
  "name": "get_document_contexts",
  "description": "Discover all available document contexts (work items, projects, contracts, etc.) in the index for exploration and filtering.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "context_type": {
        "type": "string",
        "description": "Optional filter by context type based on naming patterns"
      },
      "include_counts": {
        "type": "boolean",
        "description": "Include document count for each context",
        "default": true
      },
      "category_filter": {
        "type": "string",
        "description": "Optional filter by document category"
      }
    }
  }
}
```

### **3. `get_index_summary` Tool**

```json
{
  "name": "get_index_summary",
  "description": "Get comprehensive overview of the document index including statistics, document types, categories, and system health.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "detail_level": {
        "type": "string",
        "enum": ["basic", "detailed", "comprehensive"],
        "description": "Level of detail in the summary",
        "default": "basic"
      }
    }
  }
}
```

### **4. `explore_document_structure` Tool**

```json
{
  "name": "explore_document_structure",
  "description": "Navigate and explore document hierarchies, file structures, and chunk organization for better understanding of available content.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "context_id": {
        "type": "string",
        "description": "Optional context ID to explore specific context structure"
      },
      "file_name": {
        "type": "string",
        "description": "Optional file name to explore specific file's chunk structure"
      },
      "structure_type": {
        "type": "string",
        "enum": ["contexts", "files", "chunks", "categories"],
        "description": "Type of structure to explore",
        "default": "contexts"
      },
      "max_items": {
        "type": "integer",
        "description": "Maximum number of items to return",
        "default": 50,
        "minimum": 1,
        "maximum": 200
      }
    }
  }
}
```

---

## 📊 **Use Case Adaptation Examples**

### **Work Items Documentation**

```python
# Current approach (work item specific)
search_work_items(query="authentication", work_item_id="WI-123")

# New approach (use case agnostic)
search_documents(
    query="authentication",
    filters={"context_id": "WI-123"}
)
```

### **API Documentation**

```python
# API endpoint documentation
search_documents(
    query="user authentication endpoints",
    filters={
        "category": "api",
        "context_id": "UserService-v2"
    }
)

# Get all API services
get_document_contexts(context_type="API", category_filter="endpoint")
```

### **Legal Documents**

```python
# Contract clauses
search_documents(
    query="liability and indemnification",
    filters={
        "category": "legal",
        "context_id": "CONTRACT-2024-001"
    }
)

# Privacy policy sections
search_documents(
    query="data retention policies",
    filters={
        "category": "policy",
        "tags": ["privacy", "gdpr"]
    }
)
```

### **Project Documentation**

```python
# Project setup instructions
search_documents(
    query="installation and configuration",
    filters={
        "context_id": "ProjectAlpha",
        "file_type": "md",
        "tags": "setup"
    }
)

# Architecture documents
search_documents(
    query="system architecture diagrams",
    filters={
        "category": "architecture",
        "file_name": "architecture.md"
    }
)
```

---

## 🔧 **Implementation Strategy**

### **Phase 1: Enhanced Filter Builder (Week 1)**

```python
class UniversalFilterBuilder:
    """Use case agnostic filter builder for Azure Search"""

    @staticmethod
    def build_search_filter(filters: dict) -> str:
        """Build OData filter expressions for any document type"""

        expressions = []

        # Context filtering (work items, projects, contracts, etc.)
        if filters.get("context_id"):
            context_ids = filters["context_id"]
            if isinstance(context_ids, list):
                context_exprs = [f"context_id eq '{cid}'" for cid in context_ids]
                expressions.append(f"({' or '.join(context_exprs)})")
            else:
                expressions.append(f"context_id eq '{context_ids}'")

        # Context name filtering
        if filters.get("context_name"):
            expressions.append(f"context_name eq '{filters['context_name']}'")

        # Category filtering (supports arrays)
        if filters.get("category"):
            categories = filters["category"]
            if isinstance(categories, list):
                cat_exprs = [f"category eq '{cat}'" for cat in categories]
                expressions.append(f"({' or '.join(cat_exprs)})")
            else:
                expressions.append(f"category eq '{categories}'")

        # File-based filtering
        if filters.get("file_name"):
            expressions.append(f"file_name eq '{filters['file_name']}'")

        if filters.get("file_type"):
            expressions.append(f"file_type eq '{filters['file_type']}'")

        # Tag filtering (collection field)
        if filters.get("tags"):
            tags = filters["tags"] if isinstance(filters["tags"], list) else [filters["tags"]]
            tag_exprs = [f"tags/any(t: t eq '{tag}')" for tag in tags]
            expressions.append(f"({' or '.join(tag_exprs)})")

        # Chunk-specific filtering
        if filters.get("chunk_pattern"):
            expressions.append(f"chunk_index eq '{filters['chunk_pattern']}'")

        return " and ".join(expressions) if expressions else None
```

### **Phase 2: Universal Search Handler (Week 1)**

```python
async def handle_search_documents(searcher, arguments: dict) -> list[types.TextContent]:
    """Universal document search handler - use case agnostic"""

    query = arguments.get("query", "")
    search_type = arguments.get("search_type", "hybrid")
    filters = arguments.get("filters", {})
    max_results = arguments.get("max_results", 10)
    include_content = arguments.get("include_content", True)

    # Build universal filter
    azure_filter = UniversalFilterBuilder.build_search_filter(filters)

    # Handle special chunk range logic
    if filters.get("chunk_range") and filters.get("file_name"):
        return await handle_chunk_range_search(searcher, query, filters, max_results)

    # Execute search using existing Azure Search methods
    try:
        if search_type == "text":
            results = searcher.text_search(query, azure_filter, max_results)
        elif search_type == "vector":
            results = await searcher.vector_search(query, azure_filter, max_results)
        elif search_type == "semantic":
            results = searcher.semantic_search(query, azure_filter, max_results)
        else:  # hybrid (default)
            results = await searcher.hybrid_search(query, azure_filter, max_results)

        return format_universal_search_results(
            results,
            search_type,
            query,
            include_content=include_content
        )

    except Exception as e:
        return [types.TextContent(
            type="text",
            text=f"[ERROR] Document search failed: {str(e)}"
        )]
```

### **Phase 3: Context Discovery Tools (Week 2)**

```python
async def handle_get_document_contexts(searcher, arguments: dict):
    """Get all available contexts - use case agnostic"""

    context_type = arguments.get("context_type")
    include_counts = arguments.get("include_counts", True)
    category_filter = arguments.get("category_filter")

    # Build faceted search for context discovery
    facets = ["context_id,count:1000"]
    if category_filter:
        facets.append("category,count:100")

    # Add category filter if specified
    search_filter = None
    if category_filter:
        search_filter = f"category eq '{category_filter}'"

    results = searcher.search_client.search(
        search_text="*",
        filter=search_filter,
        facets=facets,
        top=0  # Only need facet data
    )

    facet_data = results.get_facets()
    contexts = facet_data.get("context_id", [])

    # Apply context type filtering if specified
    if context_type:
        contexts = filter_contexts_by_type(contexts, context_type)

    return format_context_list(contexts, include_counts=include_counts)

def filter_contexts_by_type(contexts: list, context_type: str) -> list:
    """Filter contexts by naming patterns to identify types"""

    type_patterns = {
        "work_item": ["WI-", "WORK-", "BUG-", "FEATURE-"],
        "project": ["PROJ-", "PROJECT-"],
        "contract": ["CONTRACT-", "LEGAL-"],
        "api": ["API-", "SERVICE-", "ENDPOINT-"],
        "policy": ["POLICY-", "PROC-", "PROCEDURE-"]
    }

    patterns = type_patterns.get(context_type.lower(), [context_type])

    filtered = []
    for context in contexts:
        context_id = context.get("value", "")
        if any(pattern in context_id.upper() for pattern in patterns):
            filtered.append(context)

    return filtered
```

### **Phase 4: Structure Explorer (Week 2)**

```python
async def handle_explore_document_structure(searcher, arguments: dict):
    """Explore document structure - works for any document type"""

    context_id = arguments.get("context_id")
    file_name = arguments.get("file_name")
    structure_type = arguments.get("structure_type", "contexts")
    max_items = arguments.get("max_items", 50)

    if structure_type == "contexts":
        return await explore_contexts_structure(searcher, max_items)
    elif structure_type == "files":
        return await explore_files_structure(searcher, context_id, max_items)
    elif structure_type == "chunks":
        return await explore_chunks_structure(searcher, context_id, file_name, max_items)
    elif structure_type == "categories":
        return await explore_categories_structure(searcher, max_items)
    else:
        return [types.TextContent(
            type="text",
            text="[ERROR] Invalid structure_type. Use: contexts, files, chunks, or categories"
        )]

async def explore_contexts_structure(searcher, max_items: int):
    """Get hierarchical view of all contexts"""

    results = searcher.search_client.search(
        search_text="*",
        facets=["context_id,count:1000", "category,count:100"],
        top=0
    )

    facets = results.get_facets()
    contexts = facets.get("context_id", [])[:max_items]
    categories = facets.get("category", [])

    # Organize by inferred type
    organized_contexts = organize_contexts_by_type(contexts)

    structure_data = {
        "total_contexts": len(contexts),
        "contexts_by_type": organized_contexts,
        "available_categories": [cat["value"] for cat in categories],
        "structure_type": "contexts"
    }

    return format_structure_exploration(structure_data)
```

---

## 📈 **Benefits of Use Case Agnostic Design**

### **For Different Document Types**

**Work Items Documentation:**

- Same tools work seamlessly
- No terminology confusion
- Consistent interface

**API Documentation:**

- `context_id` = Service/API name
- `category` = endpoint, authentication, etc.
- Same search and navigation tools

**Legal Documents:**

- `context_id` = Contract/Policy ID
- `category` = clause type, jurisdiction, etc.
- Same powerful search capabilities

**Project Documentation:**

- `context_id` = Project name
- `category` = setup, architecture, deployment
- Universal exploration tools

### **For AI Agents (LLMs)**

1. **Simplified Decision Making**: 4 clear tools vs 8 overlapping tools
2. **Consistent Patterns**: Same parameter structure across document types
3. **Intuitive Tool Names**: Generic names that make sense for any content
4. **Flexible Filtering**: Rich filter options for precise queries
5. **Predictable Responses**: Consistent result formatting

### **For Developers**

1. **Single Learning Curve**: Learn once, use everywhere
2. **Consistent API**: Same tools for different projects/domains
3. **Easy Integration**: Drop-in solution for any documentation system
4. **Future Proof**: Works with new document types without changes

---

## 🎯 **Migration Strategy**

### **Backward Compatibility Layer**

```python
# Optional compatibility wrapper for existing integrations
class LegacyToolWrapper:
    """Provides backward compatibility for existing work item specific tools"""

    @staticmethod
    async def search_work_items(searcher, arguments: dict):
        """Legacy wrapper - maps to new search_documents"""

        # Transform legacy parameters to new format
        new_args = {
            "query": arguments.get("query"),
            "search_type": arguments.get("search_type", "hybrid"),
            "max_results": arguments.get("max_results", 5)
        }

        if arguments.get("work_item_id"):
            new_args["filters"] = {"context_id": arguments["work_item_id"]}

        return await handle_search_documents(searcher, new_args)

    @staticmethod
    async def search_by_work_item(searcher, arguments: dict):
        """Legacy wrapper - maps to new search_documents with context filter"""

        new_args = {
            "query": arguments.get("query"),
            "filters": {"context_id": arguments.get("work_item_id")},
            "max_results": arguments.get("max_results", 5)
        }

        return await handle_search_documents(searcher, new_args)
```

### **Gradual Migration Timeline**

**Week 1-2: Implementation**

- Implement 4 new universal tools
- Create comprehensive test suite
- Document usage examples

**Week 3: Parallel Deployment**

- Deploy new tools alongside existing tools
- Update documentation with migration guide
- Begin using new tools in development

**Week 4: Migration Support**

- Provide migration examples for common use cases
- Update VS Code integration examples
- Create tool comparison documentation

**Week 5+: Full Migration**

- Deprecate old work item specific tools
- Update all documentation to use new tools
- Monitor performance and usage patterns

---

## 🧪 **Testing Strategy**

### **Cross-Domain Testing**

```python
# Test same tools work across different document types
async def test_universal_search_multiple_domains():
    """Test search works for work items, API docs, and legal documents"""

    # Work item search
    wi_results = await handle_search_documents(searcher, {
        "query": "authentication implementation",
        "filters": {"context_id": "WI-123", "category": "technical"}
    })

    # API documentation search
    api_results = await handle_search_documents(searcher, {
        "query": "authentication endpoints",
        "filters": {"context_id": "UserAPI-v2", "category": "api"}
    })

    # Legal document search
    legal_results = await handle_search_documents(searcher, {
        "query": "authentication requirements",
        "filters": {"context_id": "POLICY-AUTH-001", "category": "policy"}
    })

    # All should return relevant results
    assert len(wi_results) > 0
    assert len(api_results) > 0
    assert len(legal_results) > 0

# Test context discovery across domains
async def test_context_discovery_multiple_types():
    """Test context discovery identifies different document types"""

    all_contexts = await handle_get_document_contexts(searcher, {})
    work_items = await handle_get_document_contexts(searcher, {"context_type": "work_item"})
    api_docs = await handle_get_document_contexts(searcher, {"context_type": "api"})

    assert len(all_contexts) >= len(work_items) + len(api_docs)
```

---

## 🚀 **Future Extensibility**

### **Support for New Document Types**

The use case agnostic design automatically supports new document types without code changes:

**Academic Papers:**

- `context_id` = Paper DOI/ID
- `category` = research area, methodology
- `tags` = keywords, authors

**Customer Support:**

- `context_id` = Ticket/Case ID
- `category` = issue type, priority
- `tags` = product, feature

**Compliance Documents:**

- `context_id` = Regulation/Standard ID
- `category` = requirement type
- `tags` = jurisdiction, industry

### **Enhanced Filtering Capabilities**

Future enhancements can add new filter types without breaking existing tools:

```python
# Enhanced filters for specialized use cases
"filters": {
    "custom_metadata": {
        "author": "John Doe",
        "department": "Engineering",
        "security_level": "internal"
    },
    "content_analysis": {
        "sentiment": "positive",
        "complexity": "beginner",
        "completeness": "comprehensive"
    }
}
```

---

## 🎉 **Conclusion**

This refined MCP tools plan transforms the system from a work item-specific solution to a **universal documentation querying platform**. By leveraging the existing generic index structure and implementing use case agnostic tools, we achieve:

**✅ Use Case Independence**: Works seamlessly across any document type
**✅ Simplified Architecture**: 4 intuitive tools instead of 8 overlapping ones  
**✅ Enhanced AI Compatibility**: Clear tool purpose and consistent parameters
**✅ Future Extensibility**: Automatic support for new document types
**✅ Backward Compatibility**: Migration path for existing integrations
**✅ Rich Functionality**: All current capabilities maintained and enhanced

The result is a powerful, flexible, and maintainable system that truly fulfills the vision of a generic documentation assistant that can adapt to any use case while providing excellent developer and AI agent experience.
