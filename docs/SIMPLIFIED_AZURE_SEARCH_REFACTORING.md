# Azure Search Refactoring Plan

## Summary

Decouple `AzureCognitiveSearch` class from work item-specific terminology by:

1. **Field Mapping**: `work_item_id` → `context_id`
2. **Generic Methods**: Replace specific parameters with filter dictionaries
3. **Direct Updates**: Update all callers to use new generic methods immediately

## Key Changes

### Schema Update ✅ COMPLETED

- `work_item_id` → `context_id` field
- Schema alignment between create_index.py and azure_cognitive_search.py

### Method Transformations 🚧 IN PROGRESS

**Old API:**

```python
results = searcher.text_search(query, work_item_id, max_results)
work_items = searcher.get_work_items()
deleted = searcher.delete_documents_by_work_item(work_item_id)
```

**New API:**

```python
filters = {"context_id": work_item_id} if work_item_id else None
results = searcher.text_search(query, filters, max_results)
work_items = searcher.get_unique_field_values("context_id")
deleted = searcher.delete_documents_by_filter({"context_id": work_item_id})
```

## Implementation

### FilterBuilder Class

```python
class FilterBuilder:
    @staticmethod
    def build_filter(filters: Dict[str, Any]) -> Optional[str]:
        if not filters:
            return None

        expressions = []
        for field_name, field_value in filters.items():
            if isinstance(field_value, str):
                expressions.append(f"{field_name} eq '{field_value}'")
            elif isinstance(field_value, (int, float)):
                expressions.append(f"{field_name} eq {field_value}")
            elif isinstance(field_value, list):
                value_exprs = [f"{field_name} eq '{v}'" for v in field_value]
                expressions.append(f"({' or '.join(value_exprs)})")

        return " and ".join(expressions) if expressions else None
```

### Updated Method Signatures

```python
def text_search(self, query: str, filters: Optional[Dict[str, Any]] = None, top: int = 5)
async def vector_search(self, query: str, filters: Optional[Dict[str, Any]] = None, top: int = 5)
async def hybrid_search(self, query: str, filters: Optional[Dict[str, Any]] = None, top: int = 5)
def semantic_search(self, query: str, filters: Optional[Dict[str, Any]] = None, top: int = 5)
def get_unique_field_values(self, field_name: str) -> List[str]
def delete_documents_by_filter(self, filters: Dict[str, Any]) -> int
```

## Files to Update (22 method calls across 8 files)

1. **search_tools.py** - 4 calls → use `filters={"context_id": work_item_id}`
2. **info_tools.py** - 2 calls → use `get_unique_field_values("context_id")`
3. **search_documents.py** - 4 calls → use filter-based methods
4. **server.py** - 1 call → update to new API
5. **test_end_to_end.py** - 6 calls → update test cases
6. **test_simple_e2e.py** - 2 calls → update test cases
7. **delete_by_work_item.py** - 1 call → use `delete_documents_by_filter()`
8. **azure_cognitive_search.py** - 2 internal calls → update internal usage

## Migration Patterns

```python
# Search methods
# OLD: results = searcher.text_search(query, work_item_id, max_results)
# NEW:
filters = {"context_id": work_item_id} if work_item_id else None
results = searcher.text_search(query, filters, max_results)

# Get work items
# OLD: work_items = searcher.get_work_items()
# NEW: work_items = searcher.get_unique_field_values("context_id")

# Delete by work item
# OLD: deleted = searcher.delete_documents_by_work_item(work_item_id)
# NEW: deleted = searcher.delete_documents_by_filter({"context_id": work_item_id})
```

## Example Updates

**search_tools.py:**

```python
# Update search handler
filters = {"context_id": work_item_id} if work_item_id else None
results = searcher.text_search(query, filters, max_results)
```

**info_tools.py:**

```python
# Update work item list handler
work_items = searcher.get_unique_field_values("context_id")
```

## Benefits

- **Generic Design**: Filter any field, not just work items
- **No Legacy Code**: Direct updates eliminate deprecated methods
- **Extensible**: Easy to add new filter combinations
- **Type Safe**: Dictionary approach allows validation

## Usage Examples - **UPDATED FOR NEW APPROACH**

### Before (Work Item Specific) - **OLD API**

```python
# Old work item specific usage - LEGACY
results = search_service.text_search("query", work_item_id="WORK-123")
work_items = search_service.get_work_items()
deleted = search_service.delete_documents_by_work_item("WORK-123")
```

### After (Generic with Legacy Bridging) - **NEW API**

```python
# New generic usage with legacy bridging - CURRENT IMPLEMENTATION
results = search_service.text_search("query", filters={"context_id": "WORK-123"})
contexts = search_service.get_unique_field_values("context_id")
deleted = search_service.delete_documents_by_filter({"context_id": "WORK-123"})

# Advantage: Can also filter on other fields now
results = search_service.text_search("query", filters={"category": "documentation"})
categories = search_service.get_unique_field_values("category")
deleted = search_service.delete_documents_by_filter({"file_type": "md"})

# Complex filtering becomes possible
results = search_service.text_search("query", filters={
    "context_id": "WORK-123",
    "category": "documentation"
})
```

## Next Steps

1. **Add FilterBuilder** to azure_cognitive_search.py
2. **Update method signatures** to use filters parameter
3. **Update all 22 method calls** across 8 files
4. **Remove legacy methods** from service class
5. **Test and validate** all functionality
