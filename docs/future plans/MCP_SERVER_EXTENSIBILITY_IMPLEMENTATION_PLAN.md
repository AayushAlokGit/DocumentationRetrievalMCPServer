# MCP Server Tool Schema Extensibility Implementation Plan

## Problem Statement

The current MCP server implementation is tightly coupled to work-item specific tools and schemas. While universal tools exist, there's no mechanism to:

1. **Extract use case context** from the client configuration
2. **Dynamically register** context-specific tool schemas
3. **Provide context-aware descriptions** that improve LLM understanding
4. **Clean separation** between universal engine and use-case specific tooling

## Research Findings

### MCP Client Configuration Patterns

Based on MCP documentation and examples, clients configure servers through JSON configuration files:

**Claude Desktop Configuration Example:**

```json
{
  "mcpServers": {
    "server-name": {
      "command": "python",
      "args": ["path/to/server.py"],
      "env": {
        "USE_CASE": "work-items",
        "CONTEXT_TYPE": "development",
        "DOMAIN": "software-engineering"
      }
    }
  }
}
```

**VS Code MCP Configuration (mcp.json or similar):**

```json
{
  "servers": {
    "documentation-assistant": {
      "command": ["python", "src/workitem_mcp/server.py"],
      "args": [],
      "cwd": "/path/to/project",
      "env": {
        "MCP_USE_CASE": "work-items",
        "MCP_DOMAIN": "software-development",
        "MCP_CONTEXT_SCOPE": "project-documentation"
      }
    }
  }
}
```

### Key Configuration Mechanisms

1. **Environment Variables**: Primary mechanism for passing use case context
2. **Simplified Approach**: Focus on use case only for initial implementation

## Proposed Architecture (Simplified)

### 1. Use Case Detection Layer

Create a simplified `UseCaseDetector` class to extract use case information:

```python
class UseCaseDetector:
    """Detects MCP server use case from environment configuration"""

    def __init__(self):
        self.use_case = self._detect_use_case()

    def _detect_use_case(self) -> str:
        """Extract use case from environment or fallback to default"""
        # Check multiple possible environment variable names
        use_case = (
            os.getenv('MCP_USE_CASE') or
            os.getenv('USE_CASE') or
            os.getenv('USECASE') or
            'work-items'  # Default to work-items for backward compatibility
        )
        return use_case.lower().replace('_', '-')

    def is_work_items(self) -> bool:
        """Check if this is work items use case"""
        return self.use_case in ['work-items', 'workitems', 'work_items']

    def is_legal_contracts(self) -> bool:
        """Check if this is legal contracts use case"""
        return self.use_case in ['legal-contracts', 'legal', 'contracts']

    def is_research_papers(self) -> bool:
        """Check if this is research papers use case"""
        return self.use_case in ['research-papers', 'research', 'papers', 'academic']

    def is_generic_documents(self) -> bool:
        """Check if this is generic documents use case"""
        return self.use_case in ['generic-documents', 'generic', 'documents', 'general']
```

### 2. Simplified Tool Schema Factory

Create a `ToolSchemaFactory` that generates use-case specific tool schemas:

```python
class ToolSchemaFactory:
    """Generates use-case specific tool schemas based on detected use case"""

    def __init__(self, use_case_detector: UseCaseDetector):
        self.use_case_detector = use_case_detector
        self.schema_generators = {
            'work-items': WorkItemSchemaGenerator()
            # Additional generators can be added as needed:
            # 'legal': LegalContractSchemaGenerator(),
            # 'research': ResearchPaperSchemaGenerator(),
            # 'generic': GenericDocumentSchemaGenerator()
        }

    def get_tools(self) -> list[types.Tool]:
        """Generate use-case specific tool schemas"""
        use_case = self.use_case_detector.use_case

        # Currently only work-items is implemented
        if self.use_case_detector.is_work_items():
            generator = self.schema_generators['work-items']
        else:
            # Fallback to work-items for unsupported use cases
            generator = self.schema_generators['work-items']

        return generator.generate_tools()

    def get_legacy_tools(self) -> list[types.Tool]:
        """Generate legacy tools for backward compatibility"""
        # Only include legacy tools for work-items use case
        if self.use_case_detector.is_work_items():
            return get_legacy_tool_schemas()
        return []  # No legacy tools for other use cases
```

            'work-items': WorkItemSchemaGenerator(),
            'legal-contracts': LegalContractSchemaGenerator(),
            'research-papers': ResearchPaperSchemaGenerator(),
            'project-docs': ProjectDocumentationSchemaGenerator(),
            'generic-documents': GenericDocumentSchemaGenerator()
        }

    def get_tools(self) -> list[types.Tool]:
        """Generate context-specific tool schemas"""
        generator = self.schema_generators.get(
            self.context.use_case,
            self.schema_generators['generic-documents']
        )

### 3. Use-Case Specific Schema Generators

Each use case gets its own schema generator with use-case specific descriptions:

```python
class WorkItemSchemaGenerator:
    """Generates work-item specific tool schemas"""

    def generate_tools(self) -> list[types.Tool]:
        return [
            types.Tool(
                name="search_documents",
                description="Search across work item documentation and development artifacts. "
                           "Use this to find information about work items, user stories, bug reports, "
                           "technical specifications, and development artifacts. "
                           "Results include work item IDs (WORK-xxx format), implementation details, and cross-references.",
                inputSchema=self._get_work_item_search_schema()
            ),
            types.Tool(
                name="get_document_contexts",
                description="Discover available work items and project contexts. "
                           "Returns work item IDs (WORK-xxx format), project names, and document counts. "
                           "Use this to understand the scope of available work item documentation.",
                inputSchema=self._get_work_item_context_schema()
            ),
            types.Tool(
                name="explore_document_structure",
                description="Navigate through work item documentation structure. "
                           "Explore work item contexts, development files, code chunks, and technical categories. "
                           "Ideal for understanding project organization and finding related work items.",
                inputSchema=self._get_work_item_structure_schema()
            ),
            types.Tool(
                name="get_index_summary",
                description="Get comprehensive work item index statistics. "
                           "Provides overview of work items, development artifacts, file types, and project categories. "
                           "Use this to understand the scope of your development documentation.",
                inputSchema=self._get_work_item_summary_schema()
            )
        ]

# Additional schema generators can be implemented as needed:
# - LegalContractSchemaGenerator (for legal document use cases)
# - ResearchPaperSchemaGenerator (for academic research use cases)
# - GenericDocumentSchemaGenerator (fallback for general documents)
```

### 4. Updated Server Architecture

Modify the server to use the simplified extensible architecture:

```python
# server.py
class ExtensibleMCPServer:
    def __init__(self):
        self.use_case_detector = UseCaseDetector()
        self.schema_factory = ToolSchemaFactory(self.use_case_detector)
        self.tool_router = None

    async def initialize_services(self):
        """Initialize services with use case awareness"""
        searcher = DocumentSearcher()
        self.tool_router = UniversalToolRouter(searcher, self.use_case_detector)

    @app.list_tools()
    async def handle_list_tools(self) -> list[types.Tool]:
        """Return use-case specific tools"""
        tools = self.schema_factory.get_tools()

        # Add legacy tools for backward compatibility (work-items only)
        legacy_tools = self.schema_factory.get_legacy_tools()
        tools.extend(legacy_tools)

        return tools
```

## Implementation Changes Required (Simplified)

### 1. File Structure Changes

```
src/workitem_mcp/
├── server.py                    # Updated to use extensible architecture
├── context/
│   ├── __init__.py
│   ├── use_case_detector.py     # NEW: Use case detection logic
│   └── schema_factory.py        # NEW: Dynamic schema generation
├── schemas/
│   ├── __init__.py
│   └── work_item_schemas.py     # NEW: Work item specific schemas
│   # Future schema files can be added as needed:
│   # ├── legal_schemas.py     # FUTURE: Legal contract schemas
│   # ├── research_schemas.py  # FUTURE: Research paper schemas
│   # └── generic_schemas.py   # FUTURE: Generic document schemas
├── tools/
│   ├── universal_tools.py       # PRESERVED: Universal tools unchanged
│   ├── tool_router.py          # MODIFIED: Use case aware routing
│   ├── legacy_compatibility.py # PRESERVED: Backward compatibility
│   └── tool_schemas.py         # MODIFIED: Import from schema factory
└── search_documents.py         # PRESERVED: Universal search engine
```

### 2. Core Implementation Files (Simplified)

#### A. Use Case Detector (`context/use_case_detector.py`)

- Environment variable parsing for MCP_USE_CASE
- Use case validation and normalization
- Helper methods for use case checking

#### B. Schema Factory (`context/schema_factory.py`)

- Registry of schema generators by use case
- Use case to schema generator mapping
- Legacy tool inclusion logic

#### C. Use Case Schema Generators (`schemas/`)

- Work item specific schemas with WORK-xxx context descriptions
- Framework for future schema generators (legal, research, generic)
- Extensible architecture for domain-specific tooling

#### D. Universal Tools (Unchanged)

- Keep existing universal_tools.py as-is
- No changes to FilterBuilder or search functionality
- Tools remain use-case agnostic at implementation level

### 3. Configuration Examples (Simplified)

#### Work Items Use Case (Primary Implementation)

```json
{
  "mcpServers": {
    "work-item-docs": {
      "command": "python",
      "args": ["src/workitem_mcp/server.py"],
      "env": {
        "MCP_USE_CASE": "work-items"
      }
    }
  }
}
```

#### Future Use Cases (Extensible)

Additional use cases can be supported by implementing their respective schema generators:

- `MCP_USE_CASE: "legal"` - for legal document analysis
- `MCP_USE_CASE: "research"` - for academic research papers
- `MCP_USE_CASE: "generic"` - for general document collections

### 4. Migration Strategy (Simplified)

#### Phase 1: Core Structure

1. Create use case detector with basic environment variable parsing
2. Create simplified schema factory with work items schema generator
3. Create work item specific schema generator with appropriate descriptions

#### Phase 2: Schema Generation

1. Implement work item schemas with WORK-xxx context in descriptions
2. Test schema generation and tool registration
3. Validate backward compatibility with existing work item usage

#### Phase 3: Integration

1. Update server.py to use use case detector for tool registration
2. Test tool schema generation for work items use case
3. Prepare extensibility framework for future use cases

#### Phase 4: Testing & Documentation

1. Test work items configuration thoroughly
2. Create documentation for the extensibility framework
3. Document patterns for adding new use cases in the future

## Benefits of This Simplified Architecture

### 1. **Simple Extensibility**

- Single codebase supports multiple use cases
- New use cases added via schema generators only
- No changes to universal tools or core engine
- Just environment variable configuration

### 2. **Use Case Focused**

- Clear separation between implementation and description
- Use case specific tool descriptions and context
- Appropriate terminology for each domain
- Simple configuration via MCP_USE_CASE only

### 3. **Backward Compatible**

- Existing work item setup continues working
- Legacy tools still available for work items
- No breaking changes to universal tools
- Gradual migration possible

### 4. **Performance Optimized**

- Tools load only for relevant use case
- No overhead from unused functionality
- Schema generation at startup only
- Minimal configuration complexity

## Implementation Priority (Simplified)

1. **Create use case detector** - Simple environment variable parsing for work items
2. **Create schema factory** - Work item schema generator with extensible framework
3. **Create work item schemas** - Domain specific descriptions for work item tools
4. **Update server.py** - Use new schema factory for tool registration
5. **Test configuration** - Verify work items use case works correctly

This simplified approach focuses on the work items use case while maintaining an extensible framework for future additions.

## Risk Mitigation

### 1. **Backward Compatibility**

- Preserve all existing legacy tools
- Default to work-item behavior when no context detected
- Comprehensive testing of legacy workflows

### 2. **Performance**

- Schema generation happens once at startup
- Context detection optimized for startup time
- No runtime performance impact

### 3. **Configuration Complexity**

- Provide clear configuration examples
- Sensible defaults for all settings
- Validation and error messages for invalid configs

## Success Metrics

1. ✅ **Single codebase** supports multiple use cases
2. ✅ **Context extraction** from client configuration works
3. ✅ **Dynamic tool registration** based on use case
4. ✅ **LLM interactions** show improved understanding with context-aware descriptions
5. ✅ **Backward compatibility** with zero breaking changes
6. ✅ **Performance** remains equivalent to current implementation

This architecture provides true extensibility while maintaining the robust universal tools foundation and ensuring seamless operation across diverse documentation use cases.
