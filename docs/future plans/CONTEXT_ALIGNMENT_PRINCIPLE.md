# Context Alignment Principle: Document Processing ↔ MCP Server

## Core Learning

**The context in which the document processing pipeline processes documents MUST be the same context in which the MCP server will be used for search.**

This creates a **perfect symmetry** in the system:

```
Document Processing Context = MCP Server Usage Context
```

## Why This Matters

### 1. **Metadata Consistency**

- Documents processed with **Work Item context** → MCP server searches with **Work Item context**
- Documents processed with **Project context** → MCP server searches with **Project context**
- Documents processed with **Academic context** → MCP server searches with **Academic context**

### 2. **Search Relevance**

- The metadata extracted during processing is **optimized for the specific search patterns** the MCP server will encounter
- Tags, categories, and context_name fields are **aligned with user search intent**

### 3. **User Experience Alignment**

- Users searching for work items will find metadata structured for work item workflows
- Users searching for project documentation will find metadata structured for project workflows
- The search results match the **mental model** of the context

## Architectural Implication

```
┌─────────────────────────────────────────────────────────────────┐
│                    CONTEXT ALIGNMENT                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Document Processing Pipeline    ←→    MCP Server Usage         │
│                                                                 │
│  ┌─────────────────────────────┐       ┌─────────────────────┐ │
│  │ WorkItemProcessingStrategy  │  ←→   │ Work Item MCP Tools │ │
│  │ - Extract work_item_id      │       │ - Search by work_id │ │
│  │ - Tag with bug/task/feature │       │ - Filter by type    │ │
│  │ - Category: bug-technical   │       │ - Context: work_id  │ │
│  └─────────────────────────────┘       └─────────────────────┘ │
│                                                                 │
│  ┌─────────────────────────────┐       ┌─────────────────────┐ │
│  │ ProjectProcessingStrategy   │  ←→   │ Project MCP Tools   │ │
│  │ - Extract project_name      │       │ - Search by project │ │
│  │ - Tag with tech stack       │       │ - Filter by module  │ │
│  │ - Category: project-api     │       │ - Context: project  │ │
│  └─────────────────────────────┘       └─────────────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Implementation Strategy

### Current State

- **Document Processing**: Uses `PersonalDocumentationAssistantProcessingStrategy` (Work Item focused)
- **MCP Server**: Named `work-items-documentation` and provides work item search tools

✅ **Already Aligned!** The current system follows this principle correctly.

### Future Extensions

When adding new contexts, both sides must be updated together:

#### Adding Academic Context

1. **Processing Side**: Create `AcademicProcessingStrategy`

   - Extract: `author`, `publication_date`, `citation_info`
   - Tags: `research-topic`, `methodology`, `peer-reviewed`
   - Category: `paper-theoretical`, `paper-empirical`

2. **MCP Server Side**: Create Academic MCP Server
   - Tools: `search_by_author`, `search_by_topic`, `find_citations`
   - Context filters: `author`, `publication`, `research_area`

#### Adding Project Context

1. **Processing Side**: Create `ProjectProcessingStrategy`

   - Extract: `project_name`, `module`, `tech_stack`
   - Tags: `programming-language`, `framework`, `component`
   - Category: `project-api`, `project-documentation`

2. **MCP Server Side**: Create Project MCP Server
   - Tools: `search_by_project`, `search_by_technology`, `find_api_docs`
   - Context filters: `project_name`, `module`, `technology`

## Benefits of Context Alignment

### 1. **Optimized Search Results**

- Search queries get results with metadata that **matches their context expectations**
- Relevance scoring is optimized for the specific use case

### 2. **Consistent User Experience**

- Users working in "work item mode" get work item-focused metadata
- Users working in "project mode" get project-focused metadata

### 3. **Efficient Development**

- One context strategy per use case
- Clear separation of concerns
- Easier to test and validate

### 4. **Scalable Architecture**

- Easy to add new contexts without affecting existing ones
- Each context can evolve independently
- Clear extension points for new use cases

## Key Design Rule

> **"Process as you search, search as you process"**

The metadata extraction strategy during document processing should **mirror** the search patterns and filtering needs of the MCP server tools that will query that same data.

## Validation Checklist

When implementing any new context:

- [ ] Document processing strategy extracts metadata relevant to search use cases
- [ ] MCP server tools can effectively filter and search using that metadata
- [ ] Field mappings to Azure Search schema support both processing and querying
- [ ] Tags and categories enable the search patterns users will actually use
- [ ] Context_name field provides meaningful grouping for the specific use case

This principle ensures that the **entire pipeline from document ingestion to user search is optimized for the specific context** in which the system will be used.
