# Work Item Documentation Retriever

## Project Overview

I want to create a Model Context Protocol (MCP) server that leverages an LLM to answer queries related to work items I have worked upon. This MCP server will be integrated into VS Code agent mode to provide intelligent assistance for work item documentation queries.

## Data Structure

The knowledge base will be derived from a local folder structure containing work item documentation:

- **Root Directory**: `"Work Items"` folder on local desktop
- **Organization**: Each work item has its own subdirectory
- **Directory Names**: The subdirectory name serves as the **work item identifier**
- **Contents**: Each subdirectory contains:
  - Documentation markdown files (primary content)
  - Other files (will be ignored for now)

**Example Structure:**
```
Work Items/
├── WI-12345/
│   ├── requirements.md
│   ├── implementation-notes.md
│   └── other-files.txt (ignored)
├── BUG-67890/
│   ├── analysis.md
│   ├── fix-documentation.md
│   └── screenshots/ (ignored)
└── FEATURE-11111/
    ├── design.md
    ├── implementation.md
    └── testing.md
```

## Technical Architecture

The solution uses:
- **Azure OpenAI** for LLM capabilities and text embeddings
- **Azure Cognitive Search** as the vector database for efficient information retrieval
- **Model Context Protocol (MCP)** server architecture for VS Code integration
- **Python** implementation for processing and indexing

## Key Features

1. **Automatic Discovery**: Recursively scan the "Work Items" directory structure
2. **Work Item Identification**: Extract work item IDs from directory names
3. **Document Processing**: Parse markdown files and extract metadata
4. **Vector Indexing**: Generate embeddings and store in Azure Cognitive Search
5. **Intelligent Querying**: Provide context-aware answers about work items through VS Code
6. **Incremental Updates**: Support for updating documentation as work items evolve
