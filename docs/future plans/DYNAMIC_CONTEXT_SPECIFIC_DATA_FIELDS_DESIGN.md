# Dynamic Context Fields for Azure Search Index

## The Insight: Schema-Free Contextual Data

**Problem**: Current Azure Search index has **rigid, predefined fields** that limit the contextual data we can store and query.

**Solution**: Add **dictionary-type fields** that can store **unstructured, context-specific data** while remaining **fully queryable**.

## Current Schema Limitations

### Fixed Schema Approach

```python
# Current rigid schema
AZURE_SEARCH_INDEX_FIELDS = {
    'id', 'content', 'content_vector', 'file_path', 'file_name', 'file_type',
    'title', 'tags', 'category', 'context_name', 'last_modified',
    'chunk_index', 'metadata_json'  # ← Only metadata_json for extra data
}
```

### Problems with Current Approach:

1. **Schema Rigidity**: Adding new context types requires index schema changes
2. **Limited Queryability**: `metadata_json` is just a string blob - not efficiently searchable
3. **Context Mixing**: All contexts forced into same field structure
4. **Query Complexity**: Can't efficiently filter on context-specific attributes

## Proposed Solution: Dynamic Context Fields

### Schema Design with Dictionary Fields

```python
# Enhanced schema with dynamic context fields
ENHANCED_AZURE_SEARCH_INDEX_FIELDS = {
    # Core fields (unchanged)
    'id', 'content', 'content_vector', 'file_path', 'file_name', 'file_type',
    'title', 'tags', 'category', 'context_name', 'last_modified', 'chunk_index',

    # NEW: Dynamic context fields (schema-free, queryable)
    'personal_documentation_assistant_context',    # Primary focus: Complex object for personal documentation assistant data
}
```

### Azure Search Complex Type Support

Azure Cognitive Search supports **Complex Types** which are perfect for this use case. Here's the primary implementation for personal documentation assistant context:

```python
from azure.search.documents.indexes.models import ComplexField, SearchableField, SearchField, SearchFieldDataType

# Personal Documentation Assistant Context Field
personal_documentation_assistant_context_field = ComplexField(
    name="personal_documentation_assistant_context",
    fields=[
        SearchableField(name="document_id", type=SearchFieldDataType.String),
        SearchableField(name="document_type", type=SearchFieldDataType.String),
        SearchableField(name="priority", type=SearchFieldDataType.String),
        SearchableField(name="status", type=SearchFieldDataType.String),
        SearchableField(name="author", type=SearchFieldDataType.String),
        SearchableField(name="labels", type=SearchFieldDataType.String),  # Simple string, not collection
        SearchField(name="created_date", type=SearchFieldDataType.DateTimeOffset),
        SearchField(name="due_date", type=SearchFieldDataType.DateTimeOffset),
        SearchField(name="estimated_hours", type=SearchFieldDataType.Int32),
        SearchField(name="actual_hours", type=SearchFieldDataType.Int32),
    ]
)
```

## Benefits

- **Context-Specific Querying**: Filter on personal documentation assistant priority, status, author, etc.
- **Schema Flexibility**: Add new context types without breaking existing data
- **Efficient Filtering**: Direct field-level filtering (not JSON string parsing)
- **Type Safety**: Proper data types with validation at index level

## Implementation

```python
# Add personal_documentation_assistant_context field to existing index schema
def add_context_fields_to_schema(index_definition):
    index_definition.fields.append(personal_documentation_assistant_context_field)
    return index_definition
```

## Query Examples

```python
# Personal documentation assistant context filtering
filters = {
    "personal_documentation_assistant_context/document_type": "tutorial",
    "personal_documentation_assistant_context/priority": "high",
    "personal_documentation_assistant_context/author": "john.doe@company.com"
}

# Labels as comma-separated string
filters = {"personal_documentation_assistant_context/labels": "authentication,api"}
```

## Example Document Structure

```python
# Enhanced approach - rich, queryable context data
{
    "context_name": "Tutorial 12345",
    "personal_documentation_assistant_context": {
        "document_id": "Tutorial 12345",
        "document_type": "tutorial",
        "priority": "high",
        "status": "in-progress",
        "author": "john.doe@company.com",
        "labels": "api,authentication,security",  # Simple comma-separated string
        "created_date": "2024-08-10T10:00:00Z",
        "due_date": "2024-08-20T18:00:00Z",
        "estimated_hours": 16,
        "actual_hours": 8
    }
}
```

## FilterBuilder Extension: Subclass Approach

Since each use case has a different parent complex field name (`personal_documentation_assistant_context`, `project_context`, `academic_context`), a subclass approach is cleaner and more maintainable.

### Base Complex FilterBuilder

```python
from typing import Dict, Any, Optional

class ComplexFieldFilterBuilder(FilterBuilder):
    """Base class for complex field filtering with context-specific subclasses"""

    # Subclasses should override this
    COMPLEX_FIELD_NAME = None

    def __init__(self):
        if self.COMPLEX_FIELD_NAME is None:
            raise NotImplementedError("Subclasses must define COMPLEX_FIELD_NAME")

    def build_context_filter(self, context_filters: Dict[str, Any]) -> Optional[str]:
        """Build filter for context-specific fields"""
        if not context_filters:
            return None

        # Convert context fields to full paths
        full_path_filters = {}
        for field_name, field_value in context_filters.items():
            full_path = f"{self.COMPLEX_FIELD_NAME}/{field_name}"
            full_path_filters[full_path] = field_value

        return self.build_complex_field_filter(full_path_filters)

    def build_complex_field_filter(self, filters: Dict[str, Any]) -> Optional[str]:
        """Build filter for complex field paths"""
        if not filters:
            return None

        expressions = []
        for field_path, field_value in filters.items():
            if field_value is None:
                continue

            expr = self._build_single_complex_filter(field_path, field_value)
            if expr:
                expressions.append(expr)

        return f"({' and '.join(expressions)})" if expressions else None

    def _build_single_complex_filter(self, field_path: str, field_value: Any) -> str:
        """Build filter for a single complex field"""
        if isinstance(field_value, str):
            escaped_value = field_value.replace("'", "''")
            return f"{field_path} eq '{escaped_value}'"
        elif isinstance(field_value, (int, float)):
            return f"{field_path} eq {field_value}"
        elif isinstance(field_value, bool):
            return f"{field_path} eq {str(field_value).lower()}"
        elif field_value is None:
            return f"{field_path} eq null"
        elif isinstance(field_value, dict):
            # Handle range operations: {"ge": 8, "le": 40}
            field_exprs = []
            for op, val in field_value.items():
                if op in ['eq', 'ne', 'gt', 'lt', 'ge', 'le']:
                    if isinstance(val, str):
                        escaped_val = val.replace("'", "''")
                        field_exprs.append(f"{field_path} {op} '{escaped_val}'")
                    else:
                        field_exprs.append(f"{field_path} {op} {val}")
            return f"({' and '.join(field_exprs)})" if field_exprs else ""
        else:
            escaped_value = str(field_value).replace("'", "''")
            return f"{field_path} eq '{escaped_value}'"
```

### Personal Documentation Assistant Context FilterBuilder

```python
class PersonalDocumentationAssistantFilterBuilder(ComplexFieldFilterBuilder):
    """FilterBuilder for personal documentation assistant context filtering"""

    COMPLEX_FIELD_NAME = "personal_documentation_assistant_context"

    def build_personal_documentation_assistant_filter(self, personal_documentation_assistant_filters: Dict[str, Any]) -> Optional[str]:
        """Build filter specifically for personal documentation assistant context fields"""
        return self.build_context_filter(personal_documentation_assistant_filters)

    def build_mixed_filter(self, simple_filters: Dict[str, Any],
                          personal_documentation_assistant_filters: Dict[str, Any]) -> Optional[str]:
        """Build filter combining simple fields and personal documentation assistant context fields"""
        expressions = []

        # Add simple field filters using parent class FilterBuilder methods
        if simple_filters:
            simple_expr = FilterBuilder.build_filter(simple_filters)
            if simple_expr:
                expressions.append(simple_expr)

        # Add personal documentation assistant context filters
        if personal_documentation_assistant_filters:
            context_expr = self.build_personal_documentation_assistant_filter(personal_documentation_assistant_filters)
            if context_expr:
                expressions.append(context_expr)

        return f"{' and '.join(expressions)}" if expressions else None
```

### Future Context FilterBuilders

```python
class ProjectFilterBuilder(ComplexFieldFilterBuilder):
    """FilterBuilder for project context filtering"""
    COMPLEX_FIELD_NAME = "project_context"

class AcademicFilterBuilder(ComplexFieldFilterBuilder):
    """FilterBuilder for academic context filtering"""
    COMPLEX_FIELD_NAME = "academic_context"
```

### Usage Examples

```python
# Personal Documentation Assistant Context Usage
personal_documentation_assistant_builder = PersonalDocumentationAssistantFilterBuilder()

# Simple personal documentation assistant filtering
personal_documentation_assistant_filters = {
    "priority": "high",
    "status": "in-progress",
    "author": "john.doe@company.com"
}
filter_expr = personal_documentation_assistant_builder.build_personal_documentation_assistant_filter(personal_documentation_assistant_filters)
# → "(personal_documentation_assistant_context/priority eq 'high' and personal_documentation_assistant_context/status eq 'in-progress' and personal_documentation_assistant_context/author eq 'john.doe@company.com')"

# Mixed simple + personal documentation assistant filtering
simple_filters = {"file_type": "md"}
personal_documentation_assistant_filters = {"priority": "high"}
filter_expr = personal_documentation_assistant_builder.build_mixed_filter(simple_filters, personal_documentation_assistant_filters)
# → "file_type eq 'md' and (personal_documentation_assistant_context/priority eq 'high')"

# Future usage for other contexts
project_builder = ProjectFilterBuilder()
project_filters = {"tech_stack": "python", "team": "backend"}
filter_expr = project_builder.build_context_filter(project_filters)
# → "(project_context/tech_stack eq 'python' and project_context/team eq 'backend')"
```

### Integration with MCP Tools

````python
from typing import Dict, Any

class PersonalDocumentationAssistantSearchTool:
    def __init__(self):
        self.filter_builder = PersonalDocumentationAssistantFilterBuilder()
        self.search_service = get_azure_search_service()

    def search_personal_documentation_assistant_items(self, query: str, personal_documentation_assistant_filters: Dict[str, Any] = None,
                         file_filters: Dict[str, Any] = None):
        """Search with personal documentation assistant context filtering"""

        # Build combined filter
        filter_expr = self.filter_builder.build_mixed_filter(
            simple_filters=file_filters or {},
            personal_documentation_assistant_filters=personal_documentation_assistant_filters or {}
        )

        # Execute search
        return self.search_service.search_documents(
            query=query,
            filters=filter_expr,
            # ... other search parameters
        )
## Implementation Impact Analysis

Based on comprehensive codebase analysis, implementing dynamic context fields will require changes across multiple components. Here are the key areas where modifications are needed:

### 1. Azure Search Index Schema (HIGH IMPACT)

**Files to Modify:**
- `src/common/azure_cognitive_search.py` (lines 405-503)
- `src/document_upload/common_scripts/create_index.py`

**Required Changes:**

```python
# In src/common/azure_cognitive_search.py - create_index() method
def create_index(self, vector_dimensions: int = 1536) -> bool:
    # Add to existing fields array around line 503
    fields.append(
        ComplexField(
            name="personal_documentation_assistant_context",
            fields=[
                SearchableField(name="document_id", type=SearchFieldDataType.String, filterable=True),
                SearchableField(name="document_type", type=SearchFieldDataType.String, filterable=True),
                SearchableField(name="priority", type=SearchFieldDataType.String, filterable=True),
                SearchableField(name="status", type=SearchFieldDataType.String, filterable=True),
                SearchableField(name="author", type=SearchFieldDataType.String, filterable=True),
                SearchableField(name="labels", type=SearchFieldDataType.String, filterable=True),
                SearchField(name="created_date", type=SearchFieldDataType.DateTimeOffset, filterable=True),
                SearchField(name="due_date", type=SearchFieldDataType.DateTimeOffset, filterable=True),
                SearchField(name="estimated_hours", type=SearchFieldDataType.Int32, filterable=True),
                SearchField(name="actual_hours", type=SearchFieldDataType.Int32, filterable=True),
            ]
        )
    )
````

**Impact Level**: 🔴 **Critical** - Index recreation required, backward compatibility considerations needed

### 2. FilterBuilder Extension (HIGH IMPACT)

**Files to Modify:**

- `src/common/azure_cognitive_search.py` (extend FilterBuilder class around line 45-140)

**Required Changes:**

```python
# Add new subclass after existing FilterBuilder class
class ComplexFieldFilterBuilder(FilterBuilder):
    """Base class for complex field filtering with context-specific subclasses"""
    COMPLEX_FIELD_NAME = None

    def __init__(self):
        if self.COMPLEX_FIELD_NAME is None:
            raise NotImplementedError("Subclasses must define COMPLEX_FIELD_NAME")
    # ... (implementation as documented above)

class PersonalDocumentationAssistantFilterBuilder(ComplexFieldFilterBuilder):
    """FilterBuilder for personal documentation assistant context filtering"""
    COMPLEX_FIELD_NAME = "personal_documentation_assistant_context"
    # ... (implementation as documented above)
```

**Impact Level**: 🔴 **Critical** - Foundation for all context-based filtering

### 3. Document Processing Pipeline (HIGH IMPACT)

**Files to Modify:**

- `src/document_upload/processing_strategies.py` (lines 42, 700-800)
- `src/document_upload/document_processing_pipeline.py` (lines 276-350)

**Current Schema Constants Need Updates:**

```python
# Line 42 in processing_strategies.py - Update field set
AZURE_SEARCH_INDEX_FIELDS = {
    'id', 'content', 'content_vector', 'file_path', 'file_name', 'file_type',
    'title', 'tags', 'category', 'context_name', 'last_modified',
    'chunk_index', 'metadata_json',
    'personal_documentation_assistant_context'  # NEW: Add this field
}
```

**Processing Strategy Enhancement:**

```python
# Add to PersonalDocumentationAssistantProcessingStrategy class
def _extract_personal_documentation_assistant_context(self, content: str, file_metadata: Dict) -> Dict[str, Any]:
    """Extract personal documentation assistant-specific context from document"""
    return {
        "document_id": self._extract_document_id(content, file_metadata),
        "document_type": self._classify_document_type(content, file_metadata),
        "priority": self._extract_priority(content),
        "status": self._extract_status(content),
        "author": self._extract_author(content, file_metadata),
        "labels": self._extract_labels_string(content),
        "created_date": self._extract_created_date(content, file_metadata),
        "due_date": self._extract_due_date(content),
        "estimated_hours": self._extract_estimated_hours(content),
        "actual_hours": self._extract_actual_hours(content),
    }

# Modify create_search_object() method to include context field
def create_search_object(self, chunk_data: Dict, metadata: Dict) -> Dict:
    search_obj = {
        # ... existing fields ...
        "personal_documentation_assistant_context": self._extract_personal_documentation_assistant_context(
            chunk_data.get('content', ''), metadata
        )
    }
    return search_obj
```

**Impact Level**: 🔴 **Critical** - Core document processing logic changes

### 4. MCP Tools Integration (MEDIUM IMPACT)

**Files to Modify:**

- `src/workitem_mcp/tools/universal_tools.py` (search functions)
- `src/workitem_mcp/tools/tool_schemas.py` (tool parameter definitions)

**Search Tool Enhancement:**

```python
# In universal_tools.py - handle_search_documents function
async def handle_search_documents(search_service, arguments):
    # Extract context-specific filters
    context_filters = arguments.get('personal_documentation_assistant_context', {})

    if context_filters:
        # Use PersonalDocumentationAssistantFilterBuilder for complex filtering
        context_builder = PersonalDocumentationAssistantFilterBuilder()
        context_filter_expr = context_builder.build_personal_documentation_assistant_filter(context_filters)

        # Combine with existing simple filters
        simple_filters = {k: v for k, v in arguments.items() if k != 'personal_documentation_assistant_context'}
        if simple_filters:
            simple_filter_expr = FilterBuilder.build_filter(simple_filters)
            combined_filter = f"{simple_filter_expr} and {context_filter_expr}"
        else:
            combined_filter = context_filter_expr
    # ... rest of search logic
```

**Tool Schema Updates:**

```python
# In tool_schemas.py - add context filtering parameters to search tools
{
    "name": "search_documents",
    "description": "Search documents with context-specific filtering",
    "inputSchema": {
        "type": "object",
        "properties": {
            # ... existing properties ...
            "personal_documentation_assistant_context": {
                "type": "object",
                "description": "Filter by personal documentation assistant context fields",
                "properties": {
                    "document_id": {"type": "string", "description": "Filter by document ID"},
                    "document_type": {"type": "string", "description": "Filter by document type"},
                    "priority": {"type": "string", "description": "Filter by priority level"},
                    "status": {"type": "string", "description": "Filter by status"},
                    "author": {"type": "string", "description": "Filter by author"},
                    "labels": {"type": "string", "description": "Filter by comma-separated labels"},
                    "estimated_hours": {"type": "object", "description": "Filter by estimated hours range"}
                }
            }
        }
    }
}
```

**Impact Level**: 🟡 **Medium** - Extends existing functionality without breaking changes

### 5. Upload Scripts and Utilities (MEDIUM IMPACT)

**Files to Modify:**

- `src/document_upload/common_scripts/upload_work_items.py`
- `src/document_upload/common_scripts/upload_single_file.py`
- `src/document_upload/personal_documentation_assistant_scripts/upload_work_items.py`

**Required Changes:**

- Update upload scripts to handle new context fields in document objects
- Ensure consistent field population during upload process
- Add validation for context field data types

**Impact Level**: 🟡 **Medium** - Scripts will continue to work but won't populate new fields until updated

### 6. MCP Server Core (LOW IMPACT)

**Files to Modify:**

- `src/workitem_mcp/server.py` (minimal changes)
- `src/workitem_mcp/tools/tool_router.py` (no changes needed)

**Required Changes:**

- No structural changes needed to server core
- Tool router automatically supports new filtering parameters
- Existing tool routing and error handling remains intact

**Impact Level**: 🟢 **Low** - Leverages existing extensible architecture

### 7. Documentation and Configuration (LOW IMPACT)

**Files to Update:**

- Update setup documentation with new field information
- Add examples of context-based filtering to usage guides
- Update environment setup if new dependencies are needed

**Impact Level**: 🟢 **Low** - Documentation updates only

## Migration Strategy

### Phase 1: Index Schema Update (Breaking Change)

1. **Backup existing index** and test data
2. **Update create_index.py** with new ComplexField definitions
3. **Recreate Azure Search index** with new schema
4. **Re-upload existing documents** to populate new fields (initially empty)

### Phase 2: FilterBuilder Extension (Foundation)

1. **Implement ComplexFieldFilterBuilder** base class
2. **Add PersonalDocumentationAssistantFilterBuilder** subclass
3. **Unit test** filtering logic with sample OData queries
4. **Integration test** with Azure Search service

### Phase 3: Processing Pipeline Enhancement (Core Logic)

1. **Update processing strategies** to extract context metadata
2. **Modify document processing pipeline** to populate new fields
3. **Test end-to-end** document upload with context field population
4. **Validate search functionality** with new fields

### Phase 4: MCP Tools Integration (User Experience)

1. **Update universal tools** to accept context filter parameters
2. **Enhance tool schemas** with new parameter definitions
3. **Test MCP tools** with context-based filtering
4. **Validate VS Code integration** with new filtering capabilities

### Phase 5: Documentation and Testing (Completion)

1. **Update setup guides** and usage documentation
2. **Create example queries** showcasing context-based filtering
3. **Comprehensive testing** across all use cases
4. **Performance validation** with larger datasets

## Risk Assessment

### High Risks 🔴

- **Index Schema Changes**: Requires index recreation and data re-upload
- **Breaking Changes**: Existing clients may need updates for full functionality
- **Data Migration**: All existing documents need reprocessing to populate context fields

### Medium Risks 🟡

- **Performance Impact**: Complex field filtering may affect query performance
- **Type Validation**: Azure Search strict type checking for complex fields
- **Development Complexity**: Multiple file modifications required

### Low Risks 🟢

- **MCP Server Stability**: Changes leverage existing extensible architecture
- **Backward Compatibility**: Universal tools maintain existing functionality
- **Tool Router Impact**: No changes needed to routing infrastructure

## Success Metrics

1. **Functional**: Context-based filtering works across all MCP tools
2. **Performance**: Search response times remain under 2 seconds for complex queries
3. **Compatibility**: Existing MCP tools continue to work without modification
4. **Extensibility**: New context types can be added following established patterns
5. **User Experience**: VS Code Agent can effectively filter using context-specific parameters

## Implementation Recommendations

1. **Start with Phase 1-2** to establish foundation (FilterBuilder + Schema)
2. **Implement comprehensive unit tests** before proceeding to integration
3. **Use development environment** for all testing before production changes
4. **Keep backward compatibility** by maintaining existing simple field filtering
5. **Document OData query examples** for each context field combination
6. **Plan for gradual rollout** with feature flags if needed

This analysis confirms that the dynamic context fields implementation is **technically feasible** and provides a **clear roadmap** for implementation while highlighting the **critical areas** requiring careful attention during development.

```

```
