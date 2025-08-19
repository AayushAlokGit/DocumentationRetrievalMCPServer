"""
Universal Document Search Tool Handlers
=======================================

Implementation of the new universal MCP tools that work across all document types.
These replace the old work-item specific tools with universal capabilities.
"""

import logging
from typing import Dict, Any, Optional, List
import mcp.types as types

from common.azure_cognitive_search import FilterBuilder

logger = logging.getLogger("work-items-mcp")


async def handle_search_documents(search_service, arguments: dict) -> list[types.TextContent]:
    """Handle universal document search with comprehensive filtering"""
    try:
        query = arguments.get("query", "")
        search_type = arguments.get("search_type", "hybrid")
        filters = arguments.get("filters", {})
        max_results = arguments.get("max_results", 5)
        include_content = arguments.get("include_content", True)
        
        logger.info(f"[SEARCH] Universal search: query='{query}', type={search_type}, filters={filters}")
        
        # Handle special chunk_pattern filter by mapping to chunk_index
        processed_filters = {}
        for key, value in filters.items():
            if key == "chunk_pattern":
                # Map chunk_pattern to chunk_index field
                processed_filters["chunk_index"] = value
            else:
                processed_filters[key] = value
        
        # Execute search based on type - pass processed filters dict directly to search methods
        if search_type == "text":
            results = search_service.text_search(query, processed_filters, max_results)
        elif search_type == "vector":
            results = await search_service.vector_search(query, processed_filters, max_results)
        elif search_type == "semantic":
            results = search_service.semantic_search(query, processed_filters, max_results)
        else:  # hybrid (default)
            results = await search_service.hybrid_search(query, processed_filters, max_results)
        
        # Format results
        if not results:
            filter_desc = f" (with filters: {filters})" if filters else ""
            return [types.TextContent(
                type="text",
                text=f"[SEARCH] No documents found for query: '{query}'{filter_desc}"
            )]
        
        formatted_results = []
        for i, result in enumerate(results[:max_results], 1):
            result_text = f"## Result {i}\n"
            
            # Core document identification
            result_text += f"**Context:** {result.get('context_name', 'Unknown')}\n"
            result_text += f"**File:** {result.get('file_name', 'Unknown')}\n"
            result_text += f"**Title:** {result.get('title', 'No title')}\n"
            result_text += f"**Chunk:** {result.get('chunk_index', 'N/A')}\n"
            
            # Additional valuable metadata for LLM
            file_type = result.get('file_type', '').lstrip('.')  # Remove leading dot if present
            if file_type:
                result_text += f"**File Type:** {file_type.upper()}\n"
            
            file_path = result.get('file_path', '')
            if file_path:
                result_text += f"**Path:** {file_path}\n"
            
            category = result.get('category', '')
            if category:
                result_text += f"**Category:** {category}\n"
            
            tags = result.get('tags', '')
            if tags:
                # Tags are stored as comma-separated string, format them nicely
                tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
                if tag_list:
                    result_text += f"**Tags:** {', '.join(tag_list)}\n"
            
            last_modified = result.get('last_modified', '')
            if last_modified:
                # Format the timestamp more readably
                try:
                    from datetime import datetime
                    if isinstance(last_modified, str):
                        # Parse ISO format timestamp
                        dt = datetime.fromisoformat(last_modified.replace('Z', '+00:00'))
                        formatted_date = dt.strftime('%Y-%m-%d %H:%M UTC')
                        result_text += f"**Last Modified:** {formatted_date}\n"
                    else:
                        result_text += f"**Last Modified:** {last_modified}\n"
                except (ValueError, ImportError):
                    result_text += f"**Last Modified:** {last_modified}\n"
            
            # Document ID for reference (useful for debugging/tracking)
            doc_id = result.get('id', '')
            if doc_id:
                result_text += f"**Document ID:** {doc_id}\n"
            
            # Additional metadata if available
            metadata_json = result.get('metadata_json', '')
            if metadata_json:
                try:
                    import json
                    metadata = json.loads(metadata_json)
                    if metadata:
                        result_text += f"**Additional Metadata:** {len(metadata)} fields available\n"
                        # Show a few key metadata fields if they exist
                        interesting_keys = ['work_item_id', 'project', 'author', 'version', 'status']
                        shown_metadata = []
                        for key in interesting_keys:
                            if key in metadata and metadata[key]:
                                shown_metadata.append(f"{key}: {metadata[key]}")
                        if shown_metadata:
                            result_text += f"**Key Metadata:** {', '.join(shown_metadata)}\n"
                except (json.JSONDecodeError, ImportError):
                    pass
            
            if include_content and 'content' in result:
                content = result['content'].strip()
                if len(content) > 400:
                    content = content[:400] + "..."
                result_text += f"\n**Content:**\n```\n{content}\n```\n"
            
            # Relevance score (keeping this at the end as it's technical)
            score = result.get('@search.score', 'N/A')
            if isinstance(score, (int, float)):
                result_text += f"**Relevance Score:** {score:.4f}\n"
            else:
                result_text += f"**Relevance Score:** {score}\n"
            result_text += "\n---\n"
            formatted_results.append(result_text)
        
        response = f"# Search Results\n\n**Query:** \"{query}\"\n**Search Type:** {search_type.upper()}\n**Results Found:** {len(results)}\n\n" + "\n".join(formatted_results)
        
        return [types.TextContent(type="text", text=response)]
        
    except Exception as e:
        logger.error(f"Error in search_documents: {e}")
        return [types.TextContent(
            type="text", 
            text=f"[ERROR] Search failed: {str(e)}"
        )]


async def handle_get_document_contexts(search_service, arguments: dict) -> list[types.TextContent]:
    """Handle document context discovery with statistics"""
    try:
        include_stats = arguments.get("include_stats", True)
        max_contexts = arguments.get("max_contexts", 100)
        
        logger.info(f"[CONTEXTS] Getting contexts: stats={include_stats}")
        
        # Use Azure Search facets to get context distribution
        facets = [f"context_name,count:{max_contexts}"]
        
        results = search_service.search_client.search(
            search_text="*",
            facets=facets,
            top=0  # Only need facet data
        )
        
        facet_data = results.get_facets()
        contexts = facet_data.get("context_name", [])
        
        if not contexts:
            return [types.TextContent(
                type="text",
                text="# Document Contexts\n\n**No contexts found in the index**\n\nThis might indicate:\n- Empty search index\n- Connection issues\n- No documents uploaded yet"
            )]
        
        # Format response
        response = f"# Document Contexts\n\n**Total Contexts Found:** {len(contexts)}\n\n"
        
        for i, context in enumerate(contexts[:max_contexts], 1):
            context_name = context["value"]
            doc_count = context["count"] if include_stats else "N/A"
            
            response += f"**{i}. {context_name}**"
            if include_stats:
                response += f" - *{doc_count} documents*"
            response += "\n"
        
        if len(contexts) > max_contexts:
            response += f"\n*... and {len(contexts) - max_contexts} more contexts available*"
        
        return [types.TextContent(type="text", text=response)]
        
    except Exception as e:
        logger.error(f"Error in get_document_contexts: {e}")
        return [types.TextContent(
            type="text", 
            text=f"[ERROR] Context discovery failed: {str(e)}"
        )]


async def handle_explore_document_structure(search_service, arguments: dict) -> list[types.TextContent]:
    """Handle document structure exploration"""
    try:
        structure_type = arguments.get("structure_type", "contexts")
        context_name = arguments.get("context_name")
        file_name = arguments.get("file_name") 
        max_items = arguments.get("max_items", 50)
        
        logger.info(f"[STRUCTURE] Exploring: type={structure_type}, context={context_name}")
        
        if structure_type == "contexts":
            return await _explore_contexts(search_service, arguments)
        elif structure_type == "files":
            return await _explore_files(search_service, arguments)
        elif structure_type == "chunks":
            return await _explore_chunks(search_service, arguments)
        elif structure_type == "categories":
            return await _explore_categories(search_service, arguments)
        else:
            return [types.TextContent(
                type="text",
                text=f"[ERROR] Unknown structure type: {structure_type}"
            )]
            
    except Exception as e:
        logger.error(f"Error in explore_document_structure: {e}")
        return [types.TextContent(
            type="text", 
            text=f"[ERROR] Structure exploration failed: {str(e)}"
        )]


async def handle_get_index_summary(search_service, arguments: dict) -> list[types.TextContent]:
    """Handle index summary and statistics"""
    try:
        include_facets = arguments.get("include_facets", True)
        facet_limit = arguments.get("facet_limit", 50)
        
        logger.info(f"[SUMMARY] Getting index summary: facets={include_facets}")
        
        # Prepare facets for detailed statistics
        facets = []
        if include_facets:
            facets = [
                f"context_name,count:{facet_limit}",
                f"file_type,count:{facet_limit}",
                f"category,count:{facet_limit}",
                f"tags,count:{facet_limit * 2}"  # More tags expected
            ]
        
        # Get comprehensive statistics
        results = search_service.search_client.search(
            search_text="*",
            facets=facets,
            top=0,
            include_total_count=True
        )
        
        total_count = results.get_count()
        facet_data = results.get_facets() if include_facets else {}
        
        # Build response
        response = f"# Search Index Summary\n\n"
        response += f"**Total Documents:** {total_count:,}\n\n"
        
        if include_facets:
            # Context distribution
            contexts = facet_data.get("context_name", [])
            response += f"## Contexts Distribution\n"
            response += f"**Found {len(contexts)} contexts:**\n"
            context_names = [c["value"] for c in contexts[:5]]
            for i, ctx in enumerate(contexts[:5], 1):
                response += f"  {i}. **{ctx['value']}** - *{ctx['count']:,} documents*\n"
            if len(contexts) > 5:
                response += f"  ... *and {len(contexts) - 5} more contexts*\n"
            response += "\n"
            
            # File type distribution
            file_types = facet_data.get("file_type", [])
            response += f"## File Types Distribution\n"
            for ft in file_types[:10]:
                response += f"- **{ft['value']}**: {ft['count']:,} files\n"
            response += "\n"
            
            # Category distribution
            categories = facet_data.get("category", [])
            if categories:
                response += f"## Categories\n"
                for cat in categories[:10]:
                    response += f"- **{cat['value']}**: {cat['count']:,} documents\n"
                response += "\n"
            
            # Popular tags
            tags = facet_data.get("tags", [])
            if tags:
                response += f"## Popular Tags\n"
                for tag in tags[:15]:
                    response += f"- `{tag['value']}` ({tag['count']:,}) "
                response += "\n"
        
        return [types.TextContent(type="text", text=response)]
        
    except Exception as e:
        logger.error(f"Error in get_index_summary: {e}")
        return [types.TextContent(
            type="text", 
            text=f"[ERROR] Index summary failed: {str(e)}"
        )]


# Helper functions for structure exploration

async def _explore_contexts(search_service, arguments: dict) -> list[types.TextContent]:
    """Explore context hierarchy"""
    # Implementation using facets similar to get_document_contexts
    return await handle_get_document_contexts(search_service, arguments)


async def _explore_files(search_service, arguments: dict) -> list[types.TextContent]:
    """Explore file structure"""
    context_name = arguments.get("context_name")
    max_items = arguments.get("max_items", 50)
    
    filters = {}
    if context_name:
        filters["context_name"] = context_name
    
    # Use search client directly with facets for file exploration
    results = search_service.search_client.search(
        search_text="*",
        filter=FilterBuilder.build_filter(filters) if filters else None,
        facets=["file_name,count:1000"],
        select="file_name,file_type,file_path,category,tags,last_modified",
        top=0
    )
    
    facet_data = results.get_facets()
    files = facet_data.get("file_name", [])

    # Get additional metadata for each file by querying one search index chunk per file
    # NOTE: In the document processing pipeline, each file is split into chunks,
    # but the metadata for each file chunk is the same
    file_metadata = {}
    for file_info in files[:max_items]:
        file_name = file_info['value']
        # Get one document for this file to extract metadata
        file_query_filters = dict(filters)  # Copy existing filters
        file_query_filters["file_name"] = file_name
        
        file_results = search_service.search_client.search(
            search_text="*",
            filter=FilterBuilder.build_filter(file_query_filters),
            select="file_name,file_type,file_path,category,tags,last_modified",
            top=1
        )
        
        file_docs = list(file_results)
        if file_docs:
            file_metadata[file_name] = file_docs[0]
    
    context_desc = f" in **{context_name}**" if context_name else ""
    response = f"# File Structure\n\n**Files Found:** {len(files)}{context_desc}\n\n"
    
    for i, file_info in enumerate(files[:max_items], 1):
        file_name = file_info['value']
        chunk_count = file_info['count']
        metadata = file_metadata.get(file_name, {})
        
        response += f"**{i}. {file_name}**\n"
        response += f"   - *{chunk_count} chunks*\n"
        
        # Add file type if available
        file_type = metadata.get('file_type', '')
        if file_type:
            response += f"   - *Type: {file_type}*\n"
        
        # Add file path if available
        file_path = metadata.get('file_path', '')
        if file_path:
            response += f"   - *Path: {file_path}*\n"
        
        # Add category if available
        category = metadata.get('category', '')
        if category:
            response += f"   - *Category: {category}*\n"
        
        # Add tags if available
        tags = metadata.get('tags', '')
        if tags and tags.strip():
            if isinstance(tags, list):
                tags_str = ', '.join(tags)
            else:
                tags_str = str(tags).replace(';', ', ').replace('|', ', ')
            response += f"   - *Tags: {tags_str}*\n"
        
        # Add last modified date
        last_modified = metadata.get('last_modified', '')
        if last_modified:
            try:
                from datetime import datetime
                if isinstance(last_modified, str):
                    dt = datetime.fromisoformat(last_modified.replace('Z', '+00:00'))
                    response += f"   - *Modified: {dt.strftime('%Y-%m-%d %H:%M:%S UTC')}*\n"
                else:
                    response += f"   - *Modified: {last_modified}*\n"
            except:
                response += f"   - *Modified: {last_modified}*\n"
        
        response += "\n"
    
    if len(files) > max_items:
        response += f"*... and {len(files) - max_items} more files available*\n"
    
    return [types.TextContent(type="text", text=response)]


async def _explore_chunks(search_service, arguments: dict) -> list[types.TextContent]:
    """Explore chunk structure with simple retrieval"""
    context_name = arguments.get("context_name")
    file_name = arguments.get("file_name")
    max_items = arguments.get("max_items", 50)
    
    filters = {}
    if context_name:
        filters["context_name"] = context_name
    if file_name:
        filters["file_name"] = file_name
    
    # Use Azure Search with proper sorting and additional metadata fields
    results = search_service.search_client.search(
        search_text="*",
        filter=FilterBuilder.build_filter(filters) if filters else None,
        select="id,file_name,file_path,file_type,chunk_index,context_name,title,content,category,tags,last_modified,metadata_json",
        top=max_items
    )
    
    chunks = list(results)
    
    # Sort chunks by file name and chunk index for consistent ordering
    chunks = sorted(chunks, key=lambda x: (x.get('file_name', ''), x.get('chunk_index', '')))
    
    file_desc = f" from **{file_name}**" if file_name else ""
    context_desc = f" in **{context_name}**" if context_name else ""
    
    response = f"# Document Chunks\n\n**Chunks Found:** {len(chunks)}{file_desc}{context_desc}\n\n"
    
    for i, chunk in enumerate(chunks, 1):
        response += f"## Chunk {i}\n"
        response += f"**File:** {chunk.get('file_name', 'Unknown')}\n"
        response += f"**File Type:** {chunk.get('file_type', 'N/A')}\n"
        response += f"**File Path:** {chunk.get('file_path', 'N/A')}\n"
        response += f"**Context:** {chunk.get('context_name', 'N/A')}\n"
        response += f"**Chunk ID:** {chunk.get('chunk_index', 'N/A')}\n"
        response += f"**Document ID:** {chunk.get('id', 'N/A')}\n"
        response += f"**Title:** {chunk.get('title', 'No title')}\n"
        
        # Display category if available
        category = chunk.get('category', '')
        if category:
            response += f"**Category:** {category}\n"
        
        # Display tags if available
        tags = chunk.get('tags', '')
        if tags and tags.strip():
            if isinstance(tags, list):
                tags_str = ', '.join(tags)
            else:
                tags_str = str(tags).replace(';', ', ').replace('|', ', ')
            response += f"**Tags:** {tags_str}\n"
        
        # Display last modified date
        last_modified = chunk.get('last_modified', '')
        if last_modified:
            try:
                from datetime import datetime
                if isinstance(last_modified, str):
                    # Parse ISO format datetime
                    dt = datetime.fromisoformat(last_modified.replace('Z', '+00:00'))
                    response += f"**Last Modified:** {dt.strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
                else:
                    response += f"**Last Modified:** {last_modified}\n"
            except:
                response += f"**Last Modified:** {last_modified}\n"
        
        # Display parsed metadata if available
        metadata_json = chunk.get('metadata_json', '')
        if metadata_json and metadata_json.strip():
            try:
                import json
                metadata = json.loads(metadata_json)
                if isinstance(metadata, dict) and metadata:
                    key_fields = ['author', 'subject', 'keywords', 'description', 'created_date', 'word_count', 'page_count']
                    metadata_info = []
                    for field in key_fields:
                        if field in metadata and metadata[field]:
                            metadata_info.append(f"{field.replace('_', ' ').title()}: {metadata[field]}")
                    if metadata_info:
                        response += f"**Metadata:** {', '.join(metadata_info)}\n"
            except:
                pass
        
        content = chunk.get('content', '').strip()
        if len(content) > 150:
            content = content[:150] + "..."
        response += f"**Preview:**\n```\n{content}\n```\n\n"
        
        if i >= max_items:
            break
    
    return [types.TextContent(type="text", text=response)]


async def _explore_categories(search_service, arguments: dict) -> list[types.TextContent]:
    """Explore category structure"""
    context_name = arguments.get("context_name")
    max_items = arguments.get("max_items", 50)
    
    filters = {}
    if context_name:
        filters["context_name"] = context_name
    
    # Use search client with facets for category exploration
    results = search_service.search_client.search(
        search_text="*",
        filter=FilterBuilder.build_filter(filters) if filters else None,
        facets=["category,count:1000"],
        top=0
    )
    
    facet_data = results.get_facets()
    categories = facet_data.get("category", [])
    
    context_desc = f" in **{context_name}**" if context_name else ""
    response = f"# Document Categories\n\n**Categories Found:** {len(categories)}{context_desc}\n\n"
    
    for i, cat_info in enumerate(categories[:max_items], 1):
        category_name = cat_info['value']
        doc_count = cat_info['count']
        response += f"**{i}. {category_name}**\n"
        response += f"   - *{doc_count:,} documents*\n\n"
    
    if len(categories) > max_items:
        response += f"*... and {len(categories) - max_items} more categories available*\n"
    
    return [types.TextContent(type="text", text=response)]


async def handle_get_document_content(search_service, arguments: dict) -> list[types.TextContent]:
    """Handle full document content retrieval by document IDs or context+file"""
    try:
        document_ids = arguments.get("document_ids")
        context_and_file = arguments.get("context_and_file")
        max_content_length = arguments.get("max_content_length")
        include_metadata = arguments.get("include_metadata", True)
        
        logger.info(f"[CONTENT] Getting document content: ids={document_ids}, context_file={context_and_file}")
        
        # Ensure we have at least one identifier
        if not any([document_ids, context_and_file]):
            return [types.TextContent(
                type="text",
                text="[ERROR] At least one identifier required: document_ids or context_and_file"
            )]
        
        results = []
        
        # Handle document IDs
        if document_ids:
            id_list = document_ids if isinstance(document_ids, list) else [document_ids]
            for doc_id in id_list:
                try:
                    result = search_service.search_client.get_document(key=doc_id)
                    results.append(result)
                except Exception as e:
                    logger.warning(f"Could not retrieve document ID {doc_id}: {e}")
        
        # Handle context and file combination
        if context_and_file:
            context_name = context_and_file.get("context_name")
            file_name = context_and_file.get("file_name")
            if context_name and file_name:
                filter_expr = f"context_name eq '{context_name}' and file_name eq '{file_name}'"
                search_results = search_service.search_client.search(
                    search_text="*",
                    filter=filter_expr,
                    top=100,
                    order_by="chunk_index asc"
                )
                results.extend(list(search_results))
        
        if not results:
            return [types.TextContent(
                type="text",
                text="[CONTENT] No documents found matching the specified identifiers"
            )]
        
        # Format results with full content
        formatted_results = []
        for i, result in enumerate(results, 1):
            result_text = f"## Document {i}\n"
            
            # Core document identification
            if include_metadata:
                result_text += f"**Context:** {result.get('context_name', 'Unknown')}\n"
                result_text += f"**File:** {result.get('file_name', 'Unknown')}\n"
                result_text += f"**Title:** {result.get('title', 'No title')}\n"
                result_text += f"**Chunk:** {result.get('chunk_index', 'N/A')}\n"
                
                # Additional metadata
                file_type = result.get('file_type', '').lstrip('.')
                if file_type:
                    result_text += f"**File Type:** {file_type.upper()}\n"
                
                file_path = result.get('file_path', '')
                if file_path:
                    result_text += f"**Path:** {file_path}\n"
                
                category = result.get('category', '')
                if category:
                    result_text += f"**Category:** {category}\n"
                
                tags = result.get('tags', '')
                if tags:
                    tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
                    if tag_list:
                        result_text += f"**Tags:** {', '.join(tag_list)}\n"
                
                last_modified = result.get('last_modified', '')
                if last_modified:
                    result_text += f"**Last Modified:** {last_modified}\n"
                
                doc_id = result.get('id', '')
                if doc_id:
                    result_text += f"**Document ID:** {doc_id}\n"
                
                result_text += "\n"
            
            # Full content (with optional length limit)
            content = result.get('content', '').strip()
            if content:
                if max_content_length and len(content) > max_content_length:
                    content = content[:max_content_length] + f"... [content truncated at {max_content_length} characters]"
                
                result_text += f"**Full Content:**\n```\n{content}\n```\n"
            else:
                result_text += "**Full Content:** *No content available*\n"
            
            result_text += "\n---\n\n"
            formatted_results.append(result_text)
        
        response = f"# Document Content\n\n**Documents Retrieved:** {len(results)}\n\n" + "".join(formatted_results)
        
        return [types.TextContent(type="text", text=response)]
        
    except Exception as e:
        logger.error(f"Error in get_document_content: {e}")
        return [types.TextContent(
            type="text", 
            text=f"[ERROR] Content retrieval failed: {str(e)}"
        )]
