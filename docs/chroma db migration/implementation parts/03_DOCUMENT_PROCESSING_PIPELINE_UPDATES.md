# Part 3: Document Processing Pipeline Updates 📄

## Overview

This document covers updating the **Document Processing Pipeline** to work with ChromaDB. This includes modifying document processing strategies to create ChromaDB-compatible objects and updating the upload pipeline to use ChromaDB's batch operations instead of Azure Cognitive Search.

## Why This Component is Critical 🎯

The Document Processing Pipeline serves as the **data ingestion layer**:

- **Document Ingestion**: Processes raw documents (MD, PDF, DOCX) into searchable chunks
- **Embedding Generation**: Creates vector embeddings for semantic search
- **Object Creation**: Formats processed documents for storage in search service
- **Batch Upload**: Efficiently uploads large volumes of documents to the search backend
- **Data Foundation**: All search functionality depends on properly processed and uploaded documents

## Document Processing Architecture 🏗️

### Current Processing Structure

```
src/document_upload/
├── document_processing_pipeline.py    # Main pipeline orchestration
├── processing_strategies.py           # Document-to-search-object conversion
├── discovery_strategies.py            # File discovery logic (no changes needed)
├── file_tracker.py                   # File tracking logic (no changes needed)
└── personal_documentation_assistant_scripts/  # Upload scripts
```

### Key Components Requiring Updates

| Component                           | Current Azure Dependencies                            | ChromaDB Changes Required               |
| ----------------------------------- | ----------------------------------------------------- | --------------------------------------- |
| **processing_strategies.py**        | `create_chunk_search_objects()` creates Azure objects | Add `create_chromadb_objects()` method  |
| **document_processing_pipeline.py** | `UploadPhase` uses Azure batch upload                 | Update to use ChromaDB collection.add() |
| **Upload Scripts**                  | Call Azure search service methods                     | Update to use ChromaDB service          |

## Part 3 Implementation Details 📝

### 3.1 Processing Strategies Updates

**File: `src/document_upload/processing_strategies.py`**

The main change is adding ChromaDB object creation alongside (or replacing) Azure object creation:

```python
"""
Document Processing Strategies - ChromaDB Version
===============================================

Updated processing strategies for ChromaDB backend
"""

from typing import List, Dict, Any, Tuple
from datetime import datetime

from .base_types import ProcessedDocument  # Assuming this exists
from common.embedding_service import get_embedding_generator

class PersonalDocumentationAssistantProcessingStrategy:
    """
    Processing strategy for personal documentation with ChromaDB support
    """

    def __init__(self):
        """Initialize processing strategy"""
        self.embedding_generator = get_embedding_generator()

    async def generate_chunk_embeddings(self, content_chunks: List[str]) -> List[List[float]]:
        """
        Generate embeddings for document chunks

        Args:
            content_chunks: List of text chunks to embed

        Returns:
            List of embedding vectors for each chunk
        """
        embeddings = []

        for chunk in content_chunks:
            try:
                embedding = await self.embedding_generator.generate_embedding(chunk)
                embeddings.append(embedding)
            except Exception as e:
                print(f"[ERROR] Failed to generate embedding for chunk: {e}")
                # Use zero vector as fallback
                embeddings.append([0.0] * 1536)  # Assuming 1536-dimensional embeddings

        return embeddings

    def create_chromadb_objects(self, processed_doc: ProcessedDocument,
                               chunk_embeddings: List[List[float]]) -> Tuple[List[str], List[str], List[List[float]], List[Dict]]:
        """
        Create ChromaDB-compatible objects (ids, documents, embeddings, metadatas)

        Args:
            processed_doc: Processed document with metadata and chunks
            chunk_embeddings: List of embedding vectors for each chunk

        Returns:
            Tuple of (ids, documents, embeddings, metadatas) for ChromaDB
        """
        ids = []
        documents = []  # Text content
        embeddings = []  # Vector embeddings
        metadatas = []  # Metadata dicts

        for chunk_index, (chunk_content, embedding) in enumerate(zip(processed_doc.content_chunks, chunk_embeddings)):
            # Create unique chunk ID
            chunk_id = f"{processed_doc.document_id}_chunk_{chunk_index}"
            ids.append(chunk_id)

            # Store text content directly (no field wrapper needed for ChromaDB)
            documents.append(chunk_content)

            # Store embedding vector
            embeddings.append(embedding)

            # Create metadata dict (simplified structure for ChromaDB)
            metadata = {
                "file_path": processed_doc.file_path,
                "file_name": processed_doc.file_name,
                "file_type": processed_doc.file_type,
                "title": processed_doc.title,
                "tags": self._format_tags_for_chromadb(processed_doc.tags),
                "category": processed_doc.category,
                "context_name": processed_doc.context_name,
                "last_modified": processed_doc.last_modified.isoformat() if processed_doc.last_modified else None,
                "chunk_index": f"{processed_doc.file_name}_chunk_{chunk_index}",
                # Add any additional metadata as JSON string if needed
                "metadata_json": processed_doc.metadata_json if processed_doc.metadata_json else "{}"
            }

            # Remove None values to keep metadata clean
            metadata = {k: v for k, v in metadata.items() if v is not None}
            metadatas.append(metadata)

        return ids, documents, embeddings, metadatas

    def _format_tags_for_chromadb(self, tags: Any) -> str:
        """
        Format tags for ChromaDB storage (as comma-separated string)

        Args:
            tags: Tags in various formats (list, string, etc.)

        Returns:
            Comma-separated tag string
        """
        if not tags:
            return ""

        if isinstance(tags, list):
            return ', '.join(str(tag) for tag in tags if tag)
        elif isinstance(tags, str):
            return tags
        else:
            return str(tags) if tags else ""

    # Optional: Keep for backward compatibility or transition period
    def create_azure_search_objects(self, processed_doc: ProcessedDocument,
                                   chunk_embeddings: List[List[float]]) -> List[Dict[str, Any]]:
        """
        Create Azure Cognitive Search index objects

        NOTE: This method can be removed once migration to ChromaDB is complete
        """
        search_objects = []

        for chunk_index, (chunk_content, embedding) in enumerate(zip(processed_doc.content_chunks, chunk_embeddings)):
            # Convert tags to comma-separated string for Azure
            tags_str = self._format_tags_for_chromadb(processed_doc.tags)

            # Enhanced chunk index for better searchability
            enhanced_chunk_index = f"{processed_doc.file_name}_chunk_{chunk_index}"

            # Create Azure search index object
            search_object = {
                "id": f"{processed_doc.document_id}_chunk_{chunk_index}",
                "content": chunk_content,
                "content_vector": embedding,
                "file_path": processed_doc.file_path,
                "file_name": processed_doc.file_name,
                "file_type": processed_doc.file_type,
                "title": processed_doc.title,
                "tags": tags_str,
                "category": processed_doc.category,
                "context_name": processed_doc.context_name,
                "last_modified": processed_doc.last_modified,
                "chunk_index": enhanced_chunk_index,
                "metadata_json": processed_doc.metadata_json
            }
            search_objects.append(search_object)

        return search_objects


class DocumentProcessingStrategy:
    """Base class for document processing strategies"""

    async def generate_chunk_embeddings(self, content_chunks: List[str]) -> List[List[float]]:
        """Generate embeddings for document chunks - must be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement generate_chunk_embeddings")

    def create_chromadb_objects(self, processed_doc: ProcessedDocument,
                               chunk_embeddings: List[List[float]]) -> Tuple[List[str], List[str], List[List[float]], List[Dict]]:
        """Create ChromaDB objects - must be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement create_chromadb_objects")


# Strategy factory for easy instantiation
def get_processing_strategy(strategy_type: str = "personal_documentation_assistant") -> DocumentProcessingStrategy:
    """
    Get processing strategy instance

    Args:
        strategy_type: Type of processing strategy to create

    Returns:
        Processing strategy instance
    """
    strategies = {
        "personal_documentation_assistant": PersonalDocumentationAssistantProcessingStrategy
    }

    strategy_class = strategies.get(strategy_type)
    if not strategy_class:
        raise ValueError(f"Unknown processing strategy: {strategy_type}")

    return strategy_class()
```

### 3.2 Document Processing Pipeline Updates

**File: `src/document_upload/document_processing_pipeline.py`**

Update the pipeline to work with ChromaDB service:

```python
"""
Document Processing Pipeline - ChromaDB Version
=============================================

Updated document processing pipeline for ChromaDB backend
"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass

from .processing_strategies import DocumentProcessingStrategy, get_processing_strategy
from .base_types import ProcessedDocument  # Assuming this exists
from common.chromadb_service import ChromaDBService

@dataclass
class DocumentUploadResult:
    """Results from document upload process"""
    total_search_objects: int
    successfully_uploaded: int
    failed_uploads: int
    upload_time: float
    errors: List[str]

class DocumentProcessingPipeline:
    """
    Complete document processing pipeline for ChromaDB

    Handles:
    1. Document discovery and parsing
    2. Content chunking and embedding generation
    3. ChromaDB object creation
    4. Batch upload to ChromaDB collection
    """

    def __init__(self, search_service: ChromaDBService, processing_strategy: Optional[DocumentProcessingStrategy] = None):
        """
        Initialize processing pipeline

        Args:
            search_service: ChromaDB service instance
            processing_strategy: Document processing strategy (defaults to personal docs strategy)
        """
        self.search_service = search_service
        self.processing_strategy = processing_strategy or get_processing_strategy("personal_documentation_assistant")

        # Initialize pipeline phases
        self.upload_phase = UploadPhase(self.search_service)

    async def process_documents_batch(self, processed_documents: List[ProcessedDocument]) -> DocumentUploadResult:
        """
        Process a batch of documents through the complete pipeline

        Args:
            processed_documents: List of processed documents ready for upload

        Returns:
            DocumentUploadResult with upload statistics
        """
        print(f"🚀 Starting document batch processing ({len(processed_documents)} documents)")

        try:
            # Upload phase - convert to ChromaDB objects and upload
            upload_result = self.upload_phase.upload_documents(processed_documents, self.processing_strategy)

            print(f"✅ Batch processing complete:")
            print(f"   📄 Total objects: {upload_result.total_search_objects}")
            print(f"   ✅ Successful: {upload_result.successfully_uploaded}")
            print(f"   ❌ Failed: {upload_result.failed_uploads}")
            print(f"   ⏱️ Time: {upload_result.upload_time:.2f}s")

            return upload_result

        except Exception as e:
            print(f"❌ Batch processing failed: {e}")
            return DocumentUploadResult(
                total_search_objects=0,
                successfully_uploaded=0,
                failed_uploads=len(processed_documents),
                upload_time=0,
                errors=[f"Pipeline failed: {str(e)}"]
            )


class UploadPhase:
    """
    Phase 3: ChromaDB Upload

    Handles uploading processed documents to ChromaDB collection
    """

    def __init__(self, search_service: ChromaDBService):
        """
        Initialize upload phase with ChromaDB service

        Args:
            search_service: ChromaDB service instance
        """
        self.search_service = search_service

    def upload_documents(self, processed_documents: List[ProcessedDocument],
                        processing_strategy: DocumentProcessingStrategy) -> DocumentUploadResult:
        """
        Upload processed documents to ChromaDB

        Args:
            processed_documents: List of processed documents
            processing_strategy: Strategy used for processing (contains object creation logic)

        Returns:
            DocumentUploadResult: Upload statistics and results
        """
        start_time = datetime.now()
        total_objects = 0
        successful_uploads = 0
        failed_uploads = 0
        errors = []

        print(f"      📤 Starting upload to ChromaDB service...")

        try:
            # Upload to ChromaDB
            successful_uploads, failed_uploads = self._upload_to_chromadb(
                processed_documents, processing_strategy, errors
            )

            upload_time = (datetime.now() - start_time).total_seconds()
            total_objects = successful_uploads + failed_uploads

            print(f"      ✅ Upload completed: {successful_uploads}/{total_objects} successful")
            if failed_uploads > 0:
                print(f"      ❌ Failed uploads: {failed_uploads}")

        except Exception as e:
            upload_time = (datetime.now() - start_time).total_seconds()
            error_msg = f"Upload phase failed: {str(e)}"
            errors.append(error_msg)
            print(f"      ❌ {error_msg}")

        return DocumentUploadResult(
            total_search_objects=total_objects,
            successfully_uploaded=successful_uploads,
            failed_uploads=failed_uploads,
            upload_time=upload_time,
            errors=errors
        )

    def _upload_to_chromadb(self, processed_documents: List[ProcessedDocument],
                           processing_strategy: DocumentProcessingStrategy,
                           errors: List[str]) -> tuple[int, int]:
        """Upload documents to ChromaDB"""
        successful = 0
        failed = 0

        for doc in processed_documents:
            try:
                # Generate embeddings for this document
                chunk_embeddings = asyncio.run(processing_strategy.generate_chunk_embeddings(doc.content_chunks))

                # Create ChromaDB objects
                ids, documents, embeddings, metadatas = processing_strategy.create_chromadb_objects(doc, chunk_embeddings)

                # Upload to ChromaDB
                self.search_service.collection.add(
                    ids=ids,
                    documents=documents,
                    embeddings=embeddings,
                    metadatas=metadatas
                )

                successful += len(ids)
                print(f"         ✅ Uploaded {doc.file_name}: {len(ids)} chunks")

            except Exception as e:
                failed += len(doc.content_chunks) if hasattr(doc, 'content_chunks') else 1
                error_msg = f"Failed to upload {doc.file_name}: {str(e)}"
                errors.append(error_msg)
                print(f"         ❌ {error_msg}")

        return successful, failed


class DocumentProcessor:
    """
    High-level document processor that handles the complete workflow
    """

    def __init__(self, search_service: ChromaDBService):
        """Initialize document processor with ChromaDB service"""
        self.search_service = search_service
        self.pipeline = DocumentProcessingPipeline(search_service)

    async def process_file(self, file_path: str, context_name: str, **metadata) -> DocumentUploadResult:
        """
        Process a single file and upload to ChromaDB

        Args:
            file_path: Path to file to process
            context_name: Context/category for the document
            **metadata: Additional metadata for the document

        Returns:
            DocumentUploadResult with processing results
        """
        try:
            # This would typically involve:
            # 1. File parsing (MD, PDF, DOCX)
            # 2. Content chunking
            # 3. Metadata extraction
            # 4. ProcessedDocument creation

            # For now, assume we have a method to create ProcessedDocument
            processed_doc = self._parse_file_to_processed_document(file_path, context_name, metadata)

            # Process through pipeline
            return await self.pipeline.process_documents_batch([processed_doc])

        except Exception as e:
            print(f"❌ Failed to process file {file_path}: {e}")
            return DocumentUploadResult(
                total_search_objects=0,
                successfully_uploaded=0,
                failed_uploads=1,
                upload_time=0,
                errors=[f"File processing failed: {str(e)}"]
            )

    async def process_directory(self, directory_path: str, context_name: str,
                              file_patterns: List[str] = None) -> DocumentUploadResult:
        """
        Process all files in a directory and upload to ChromaDB

        Args:
            directory_path: Path to directory to process
            context_name: Context/category for documents
            file_patterns: List of file patterns to match (e.g., ['*.md', '*.pdf'])

        Returns:
            DocumentUploadResult with processing results
        """
        try:
            # Discover files (this would use existing discovery strategies)
            file_paths = self._discover_files(directory_path, file_patterns or ['*.md', '*.pdf', '*.docx'])

            # Process files in batches
            batch_size = 10  # Process 10 files at a time
            all_results = []

            for i in range(0, len(file_paths), batch_size):
                batch_files = file_paths[i:i + batch_size]
                print(f"🔄 Processing batch {i//batch_size + 1}/{(len(file_paths) + batch_size - 1)//batch_size}")

                # Parse files to ProcessedDocuments
                processed_docs = []
                for file_path in batch_files:
                    try:
                        processed_doc = self._parse_file_to_processed_document(file_path, context_name, {})
                        processed_docs.append(processed_doc)
                    except Exception as e:
                        print(f"⚠️ Skipping {file_path}: {e}")

                # Process batch if we have documents
                if processed_docs:
                    batch_result = await self.pipeline.process_documents_batch(processed_docs)
                    all_results.append(batch_result)

            # Combine results
            return self._combine_upload_results(all_results)

        except Exception as e:
            print(f"❌ Failed to process directory {directory_path}: {e}")
            return DocumentUploadResult(
                total_search_objects=0,
                successfully_uploaded=0,
                failed_uploads=1,
                upload_time=0,
                errors=[f"Directory processing failed: {str(e)}"]
            )

    def _parse_file_to_processed_document(self, file_path: str, context_name: str, metadata: dict) -> ProcessedDocument:
        """
        Parse a file into a ProcessedDocument

        This is a placeholder - actual implementation would handle:
        - Different file types (MD, PDF, DOCX)
        - Content extraction
        - Text chunking
        - Metadata extraction
        """
        # This is a simplified placeholder implementation
        import os
        from pathlib import Path

        # Read file content (simplified)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception:
            # Fallback for binary files or encoding issues
            content = f"Content from {os.path.basename(file_path)}"

        # Simple chunking (split by paragraphs)
        chunks = [chunk.strip() for chunk in content.split('\n\n') if chunk.strip()]
        if not chunks:
            chunks = [content]  # Fallback to entire content

        # Create ProcessedDocument
        return ProcessedDocument(
            document_id=f"doc_{hash(file_path)}",
            file_path=file_path,
            file_name=os.path.basename(file_path),
            file_type=Path(file_path).suffix.lstrip('.'),
            title=metadata.get('title', os.path.basename(file_path)),
            content_chunks=chunks,
            tags=metadata.get('tags', []),
            category=metadata.get('category', 'document'),
            context_name=context_name,
            last_modified=datetime.fromtimestamp(os.path.getmtime(file_path)),
            metadata_json=str(metadata) if metadata else "{}"
        )

    def _discover_files(self, directory_path: str, patterns: List[str]) -> List[str]:
        """Discover files matching patterns in directory"""
        import glob
        import os

        all_files = []
        for pattern in patterns:
            full_pattern = os.path.join(directory_path, "**", pattern)
            files = glob.glob(full_pattern, recursive=True)
            all_files.extend(files)

        return list(set(all_files))  # Remove duplicates

    def _combine_upload_results(self, results: List[DocumentUploadResult]) -> DocumentUploadResult:
        """Combine multiple upload results into single result"""
        if not results:
            return DocumentUploadResult(0, 0, 0, 0, [])

        total_objects = sum(r.total_search_objects for r in results)
        successful = sum(r.successfully_uploaded for r in results)
        failed = sum(r.failed_uploads for r in results)
        total_time = sum(r.upload_time for r in results)
        all_errors = []
        for r in results:
            all_errors.extend(r.errors)

        return DocumentUploadResult(
            total_search_objects=total_objects,
            successfully_uploaded=successful,
            failed_uploads=failed,
            upload_time=total_time,
            errors=all_errors
        )
```

### 3.3 Upload Scripts Updates

**File: `src/document_upload/personal_documentation_assistant_scripts/upload_with_custom_metadata.py`**

Update upload scripts to use ChromaDB:

```python
"""
Upload Documents with Custom Metadata - ChromaDB Version
=======================================================

Upload script updated for ChromaDB backend
"""

import asyncio
import sys
from pathlib import Path
from typing import Dict, Any, List

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from common.chromadb_service import ChromaDBService
from document_upload.document_processing_pipeline import DocumentProcessor

async def upload_documents_with_metadata(
    file_paths: List[str],
    context_name: str,
    metadata: Dict[str, Any] = None
) -> None:
    """
    Upload documents with custom metadata to ChromaDB

    Args:
        file_paths: List of file paths to upload
        context_name: Context/category for documents
        metadata: Additional metadata to attach to documents
    """
    # Initialize ChromaDB service
    print("🔄 Initializing ChromaDB service...")
    search_service = ChromaDBService()

    # Test connection
    if not search_service.test_connection():
        print("❌ Failed to connect to ChromaDB")
        return

    print(f"✅ Connected to ChromaDB collection: {search_service.collection_name}")

    # Initialize document processor
    processor = DocumentProcessor(search_service)

    # Process each file
    total_successful = 0
    total_failed = 0

    for file_path in file_paths:
        print(f"\n📄 Processing: {file_path}")

        try:
            # Process single file
            result = await processor.process_file(
                file_path=file_path,
                context_name=context_name,
                **(metadata or {})
            )

            total_successful += result.successfully_uploaded
            total_failed += result.failed_uploads

            if result.errors:
                print("⚠️ Errors encountered:")
                for error in result.errors:
                    print(f"   - {error}")

        except Exception as e:
            print(f"❌ Failed to process {file_path}: {e}")
            total_failed += 1

    # Final summary
    print(f"\n📊 Upload Summary:")
    print(f"   ✅ Successful uploads: {total_successful}")
    print(f"   ❌ Failed uploads: {total_failed}")
    print(f"   📁 Context: {context_name}")

    # Display collection stats
    stats = search_service.get_index_stats()
    print(f"   📈 Total documents in collection: {stats.get('document_count', 0)}")

async def upload_directory_with_metadata(
    directory_path: str,
    context_name: str,
    file_patterns: List[str] = None,
    metadata: Dict[str, Any] = None
) -> None:
    """
    Upload all files in directory with custom metadata to ChromaDB

    Args:
        directory_path: Directory containing files to upload
        context_name: Context/category for documents
        file_patterns: File patterns to match (e.g., ['*.md', '*.pdf'])
        metadata: Additional metadata to attach to documents
    """
    # Initialize ChromaDB service
    print("🔄 Initializing ChromaDB service...")
    search_service = ChromaDBService()

    # Test connection
    if not search_service.test_connection():
        print("❌ Failed to connect to ChromaDB")
        return

    print(f"✅ Connected to ChromaDB collection: {search_service.collection_name}")

    # Initialize document processor
    processor = DocumentProcessor(search_service)

    # Process directory
    print(f"\n📁 Processing directory: {directory_path}")
    print(f"🎯 Context: {context_name}")
    print(f"🔍 File patterns: {file_patterns or ['*.md', '*.pdf', '*.docx']}")

    if metadata:
        print(f"🏷️ Additional metadata: {metadata}")

    try:
        result = await processor.process_directory(
            directory_path=directory_path,
            context_name=context_name,
            file_patterns=file_patterns,
            **{k: v for k, v in (metadata or {}).items()}
        )

        # Final summary
        print(f"\n📊 Upload Summary:")
        print(f"   ✅ Successful uploads: {result.successfully_uploaded}")
        print(f"   ❌ Failed uploads: {result.failed_uploads}")
        print(f"   ⏱️ Total time: {result.upload_time:.2f}s")
        print(f"   📁 Context: {context_name}")

        if result.errors:
            print("⚠️ Errors encountered:")
            for error in result.errors:
                print(f"   - {error}")

        # Display collection stats
        stats = search_service.get_index_stats()
        print(f"   📈 Total documents in collection: {stats.get('document_count', 0)}")

    except Exception as e:
        print(f"❌ Directory processing failed: {e}")

# Example usage functions
async def main_example():
    """Example usage of the upload functions"""

    # Example 1: Upload specific files
    print("=== Example 1: Upload Specific Files ===")
    await upload_documents_with_metadata(
        file_paths=[
            "docs/README.md",
            "docs/setup_guide.md"
        ],
        context_name="project_documentation",
        metadata={
            "category": "guide",
            "tags": ["setup", "documentation"],
            "priority": "high"
        }
    )

    # Example 2: Upload entire directory
    print("\n=== Example 2: Upload Directory ===")
    await upload_directory_with_metadata(
        directory_path="docs/",
        context_name="project_documentation",
        file_patterns=["*.md", "*.pdf"],
        metadata={
            "category": "documentation",
            "project": "mcp_server"
        }
    )

if __name__ == "__main__":
    # Run example
    asyncio.run(main_example())
```

### 3.4 Delete Documents Script

**File: `src/document_upload/personal_documentation_assistant_scripts/delete_by_context_and_filename.py`**

```python
"""
Delete Documents by Context and Filename - ChromaDB Version
==========================================================

Delete script updated for ChromaDB backend
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from common.chromadb_service import ChromaDBService

async def delete_documents_by_context_and_filename(
    context_name: Optional[str] = None,
    file_name: Optional[str] = None,
    confirm: bool = False
) -> None:
    """
    Delete documents by context and/or filename from ChromaDB

    Args:
        context_name: Context name to filter by (optional)
        file_name: File name to filter by (optional)
        confirm: Whether to skip confirmation prompt
    """
    if not context_name and not file_name:
        print("❌ Must provide at least context_name or file_name")
        return

    # Initialize ChromaDB service
    print("🔄 Initializing ChromaDB service...")
    search_service = ChromaDBService()

    # Test connection
    if not search_service.test_connection():
        print("❌ Failed to connect to ChromaDB")
        return

    print(f"✅ Connected to ChromaDB collection: {search_service.collection_name}")

    # Build filter criteria
    filters = {}
    if context_name:
        filters["context_name"] = context_name
    if file_name:
        filters["file_name"] = file_name

    print(f"🔍 Searching for documents matching: {filters}")

    try:
        # Find matching documents first
        results = await search_service.vector_search("", filters, 1000)  # Large limit to find all

        if not results:
            print("📭 No documents found matching criteria")
            return

        # Show what will be deleted
        print(f"📋 Found {len(results)} documents to delete:")
        for i, doc in enumerate(results[:10]):  # Show first 10
            print(f"   {i+1}. {doc.get('file_name', 'unknown')} (context: {doc.get('context_name', 'unknown')})")

        if len(results) > 10:
            print(f"   ... and {len(results) - 10} more documents")

        # Confirmation
        if not confirm:
            response = input(f"\n❓ Delete {len(results)} documents? (yes/no): ")
            if response.lower() not in ['yes', 'y']:
                print("❌ Deletion cancelled")
                return

        # Extract document IDs
        doc_ids = [doc['id'] for doc in results if 'id' in doc]

        if not doc_ids:
            print("❌ No document IDs found")
            return

        # Delete documents
        print(f"🗑️ Deleting {len(doc_ids)} documents...")

        try:
            search_service.collection.delete(ids=doc_ids)
            print(f"✅ Successfully deleted {len(doc_ids)} documents")

        except Exception as e:
            print(f"❌ Delete operation failed: {e}")
            return

        # Verify deletion
        verify_results = await search_service.vector_search("", filters, 10)
        remaining_count = len(verify_results)

        if remaining_count == 0:
            print("✅ All matching documents deleted successfully")
        else:
            print(f"⚠️ {remaining_count} documents still remain (may not have matched filter exactly)")

        # Show updated collection stats
        stats = search_service.get_index_stats()
        print(f"📈 Total documents in collection: {stats.get('document_count', 0)}")

    except Exception as e:
        print(f"❌ Delete operation failed: {e}")

async def delete_all_documents_in_context(context_name: str, confirm: bool = False) -> None:
    """Delete all documents in a specific context"""
    await delete_documents_by_context_and_filename(
        context_name=context_name,
        file_name=None,
        confirm=confirm
    )

async def delete_specific_file_across_contexts(file_name: str, confirm: bool = False) -> None:
    """Delete a specific file across all contexts"""
    await delete_documents_by_context_and_filename(
        context_name=None,
        file_name=file_name,
        confirm=confirm
    )

async def main_example():
    """Example usage of delete functions"""

    # Example 1: Delete all documents in a context
    print("=== Example 1: Delete Context ===")
    await delete_all_documents_in_context("test_context", confirm=False)

    # Example 2: Delete specific file
    print("\n=== Example 2: Delete Specific File ===")
    await delete_specific_file_across_contexts("old_readme.md", confirm=False)

    # Example 3: Delete by both context and filename
    print("\n=== Example 3: Delete Context + Filename ===")
    await delete_documents_by_context_and_filename(
        context_name="project_docs",
        file_name="deprecated.md",
        confirm=False
    )

if __name__ == "__main__":
    # Run example
    asyncio.run(main_example())
```

### 3.5 Batch Processing Script

**File: `src/document_upload/personal_documentation_assistant_scripts/batch_upload_directory.py`**

```python
"""
Batch Upload Directory - ChromaDB Version
=========================================

Batch processing script for large document collections
"""

import asyncio
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from common.chromadb_service import ChromaDBService
from document_upload.document_processing_pipeline import DocumentProcessor

async def batch_upload_directory(
    directory_path: str,
    context_name: str,
    file_extensions: List[str] = None,
    batch_size: int = 50,
    metadata: Dict[str, Any] = None,
    recursive: bool = True
) -> None:
    """
    Batch upload entire directory to ChromaDB with progress tracking

    Args:
        directory_path: Directory to process
        context_name: Context for all documents
        file_extensions: File extensions to include (default: ['.md', '.pdf', '.docx'])
        batch_size: Number of documents to process per batch
        metadata: Additional metadata for all documents
        recursive: Whether to search subdirectories
    """
    # Default file extensions
    if file_extensions is None:
        file_extensions = ['.md', '.pdf', '.docx', '.txt']

    # Initialize ChromaDB service
    print("🔄 Initializing ChromaDB service...")
    search_service = ChromaDBService()

    # Test connection
    if not search_service.test_connection():
        print("❌ Failed to connect to ChromaDB")
        return

    print(f"✅ Connected to ChromaDB collection: {search_service.collection_name}")

    # Get initial stats
    initial_stats = search_service.get_index_stats()
    initial_count = initial_stats.get('document_count', 0)
    print(f"📊 Initial document count: {initial_count}")

    # Discover all files
    print(f"🔍 Discovering files in: {directory_path}")
    print(f"   📁 Recursive: {recursive}")
    print(f"   🎯 Extensions: {file_extensions}")

    all_files = []
    directory = Path(directory_path)

    for extension in file_extensions:
        if recursive:
            pattern = f"**/*{extension}"
        else:
            pattern = f"*{extension}"

        files = list(directory.glob(pattern))
        all_files.extend(files)

    all_files = list(set(all_files))  # Remove duplicates
    all_files = [str(f) for f in all_files]  # Convert to strings

    print(f"📋 Found {len(all_files)} files to process")

    if not all_files:
        print("📭 No files found matching criteria")
        return

    # Initialize processor
    processor = DocumentProcessor(search_service)

    # Process in batches
    total_successful = 0
    total_failed = 0
    total_batches = (len(all_files) + batch_size - 1) // batch_size

    for batch_idx in range(0, len(all_files), batch_size):
        batch_files = all_files[batch_idx:batch_idx + batch_size]
        batch_num = (batch_idx // batch_size) + 1

        print(f"\n🔄 Processing batch {batch_num}/{total_batches} ({len(batch_files)} files)")

        # Process batch of files
        batch_successful = 0
        batch_failed = 0

        for file_path in batch_files:
            try:
                print(f"   📄 Processing: {Path(file_path).name}")

                result = await processor.process_file(
                    file_path=file_path,
                    context_name=context_name,
                    **(metadata or {})
                )

                batch_successful += result.successfully_uploaded
                batch_failed += result.failed_uploads

                if result.errors:
                    print(f"   ⚠️ Errors in {Path(file_path).name}:")
                    for error in result.errors:
                        print(f"     - {error}")

            except Exception as e:
                print(f"   ❌ Failed to process {Path(file_path).name}: {e}")
                batch_failed += 1

        total_successful += batch_successful
        total_failed += batch_failed

        print(f"   ✅ Batch {batch_num} complete: {batch_successful} successful, {batch_failed} failed")

        # Brief pause between batches to avoid overwhelming the system
        if batch_num < total_batches:
            await asyncio.sleep(1)

    # Final summary
    print(f"\n📊 Final Upload Summary:")
    print(f"   📄 Total files processed: {len(all_files)}")
    print(f"   ✅ Successful uploads: {total_successful}")
    print(f"   ❌ Failed uploads: {total_failed}")
    print(f"   📁 Context: {context_name}")
    print(f"   🏷️ Batch size: {batch_size}")

    if metadata:
        print(f"   📋 Metadata applied: {metadata}")

    # Final collection stats
    final_stats = search_service.get_index_stats()
    final_count = final_stats.get('document_count', 0)
    documents_added = final_count - initial_count

    print(f"   📈 Documents added to collection: {documents_added}")
    print(f"   📊 Total documents in collection: {final_count}")

def main():
    """Command line interface for batch upload"""
    parser = argparse.ArgumentParser(description="Batch upload directory to ChromaDB")

    parser.add_argument("directory", help="Directory to upload")
    parser.add_argument("context", help="Context name for documents")
    parser.add_argument("--extensions", nargs="+", default=[".md", ".pdf", ".docx"],
                       help="File extensions to include")
    parser.add_argument("--batch-size", type=int, default=50,
                       help="Number of documents per batch")
    parser.add_argument("--no-recursive", action="store_true",
                       help="Don't search subdirectories")
    parser.add_argument("--category", help="Document category")
    parser.add_argument("--tags", nargs="+", help="Document tags")

    args = parser.parse_args()

    # Build metadata
    metadata = {}
    if args.category:
        metadata["category"] = args.category
    if args.tags:
        metadata["tags"] = args.tags

    # Run batch upload
    asyncio.run(batch_upload_directory(
        directory_path=args.directory,
        context_name=args.context,
        file_extensions=args.extensions,
        batch_size=args.batch_size,
        metadata=metadata,
        recursive=not args.no_recursive
    ))

if __name__ == "__main__":
    if len(sys.argv) == 1:
        # Example usage if no arguments provided
        print("=== Batch Upload Example ===")
        asyncio.run(batch_upload_directory(
            directory_path="docs/",
            context_name="project_documentation",
            file_extensions=[".md", ".pdf"],
            batch_size=25,
            metadata={
                "category": "documentation",
                "project": "chromadb_migration"
            }
        ))
    else:
        # Use command line arguments
        main()
```

## Testing Strategy for Part 3 🧪

### Unit Tests for Document Processing

**File: `tests/test_document_processing_chromadb.py`**

```python
import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.document_upload.processing_strategies import PersonalDocumentationAssistantProcessingStrategy
from src.document_upload.document_processing_pipeline import DocumentProcessor, UploadPhase
from src.common.chromadb_service import ChromaDBService

class TestProcessingStrategies:

    @pytest.fixture
    def mock_embedding_generator(self):
        """Mock embedding generator"""
        mock_gen = Mock()
        mock_gen.generate_embedding = Mock(return_value=[0.1, 0.2, 0.3])
        return mock_gen

    @pytest.fixture
    def processing_strategy(self, mock_embedding_generator):
        """Create processing strategy with mocked dependencies"""
        with patch('src.document_upload.processing_strategies.get_embedding_generator',
                  return_value=mock_embedding_generator):
            return PersonalDocumentationAssistantProcessingStrategy()

    @pytest.fixture
    def sample_processed_document(self):
        """Create sample ProcessedDocument for testing"""
        from src.document_upload.base_types import ProcessedDocument  # Assuming this exists

        return ProcessedDocument(
            document_id="test_doc_123",
            file_path="/path/to/test.md",
            file_name="test.md",
            file_type="md",
            title="Test Document",
            content_chunks=["First chunk content", "Second chunk content", "Third chunk content"],
            tags=["test", "sample", "document"],
            category="manual",
            context_name="test_context",
            last_modified=datetime(2024, 1, 1, 12, 0, 0),
            metadata_json='{"custom": "metadata"}'
        )

    @pytest.mark.asyncio
    async def test_generate_chunk_embeddings(self, processing_strategy, mock_embedding_generator):
        """Test chunk embedding generation"""
        chunks = ["First chunk", "Second chunk", "Third chunk"]

        embeddings = await processing_strategy.generate_chunk_embeddings(chunks)

        assert len(embeddings) == 3
        assert all(len(emb) == 3 for emb in embeddings)  # Mock returns 3-dim vectors
        assert mock_embedding_generator.generate_embedding.call_count == 3

    def test_create_chromadb_objects(self, processing_strategy, sample_processed_document):
        """Test ChromaDB object creation"""
        chunk_embeddings = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6], [0.7, 0.8, 0.9]]

        ids, documents, embeddings, metadatas = processing_strategy.create_chromadb_objects(
            sample_processed_document, chunk_embeddings
        )

        # Verify structure
        assert len(ids) == 3
        assert len(documents) == 3
        assert len(embeddings) == 3
        assert len(metadatas) == 3

        # Verify IDs
        assert all(id.startswith("test_doc_123_chunk_") for id in ids)
        assert ids[0] == "test_doc_123_chunk_0"
        assert ids[2] == "test_doc_123_chunk_2"

        # Verify documents (content)
        assert documents[0] == "First chunk content"
        assert documents[1] == "Second chunk content"
        assert documents[2] == "Third chunk content"

        # Verify embeddings
        assert embeddings == chunk_embeddings

        # Verify metadata structure
        for metadata in metadatas:
            assert metadata["file_name"] == "test.md"
            assert metadata["file_type"] == "md"
            assert metadata["title"] == "Test Document"
            assert metadata["category"] == "manual"
            assert metadata["context_name"] == "test_context"
            assert metadata["tags"] == "test, sample, document"
            assert "id" not in metadata  # Should not include reserved fields
            assert "content" not in metadata
            assert "content_vector" not in metadata

    def test_format_tags_for_chromadb(self, processing_strategy):
        """Test tag formatting for ChromaDB"""
        # Test list of tags
        list_tags = ["tag1", "tag2", "tag3"]
        result = processing_strategy._format_tags_for_chromadb(list_tags)
        assert result == "tag1, tag2, tag3"

        # Test string tags
        string_tags = "existing, tags"
        result = processing_strategy._format_tags_for_chromadb(string_tags)
        assert result == "existing, tags"

        # Test empty/None tags
        assert processing_strategy._format_tags_for_chromadb(None) == ""
        assert processing_strategy._format_tags_for_chromadb([]) == ""


class TestDocumentProcessingPipeline:

    @pytest.fixture
    def mock_chromadb_service(self):
        """Create mock ChromaDB service"""
        service = Mock(spec=ChromaDBService)

        # Mock collection
        mock_collection = MagicMock()
        service.collection = mock_collection

        return service

    @pytest.fixture
    def mock_processing_strategy(self):
        """Create mock processing strategy"""
        strategy = Mock()

        # Mock embedding generation
        strategy.generate_chunk_embeddings = Mock(return_value=[
            [0.1, 0.2, 0.3], [0.4, 0.5, 0.6], [0.7, 0.8, 0.9]
        ])

        # Mock ChromaDB object creation
        strategy.create_chromadb_objects = Mock(return_value=(
            ["doc1_chunk_0", "doc1_chunk_1", "doc1_chunk_2"],  # ids
            ["content1", "content2", "content3"],  # documents
            [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6], [0.7, 0.8, 0.9]],  # embeddings
            [{"meta": "data1"}, {"meta": "data2"}, {"meta": "data3"}]  # metadatas
        ))

        return strategy

    @pytest.fixture
    def sample_processed_documents(self):
        """Create sample processed documents for testing"""
        from src.document_upload.base_types import ProcessedDocument

        return [
            ProcessedDocument(
                document_id="doc1",
                file_path="/path/doc1.md",
                file_name="doc1.md",
                file_type="md",
                title="Document 1",
                content_chunks=["chunk1", "chunk2", "chunk3"],
                tags=["tag1"],
                category="test",
                context_name="test_context",
                last_modified=datetime.now(),
                metadata_json="{}"
            ),
            ProcessedDocument(
                document_id="doc2",
                file_path="/path/doc2.md",
                file_name="doc2.md",
                file_type="md",
                title="Document 2",
                content_chunks=["chunk4", "chunk5"],
                tags=["tag2"],
                category="test",
                context_name="test_context",
                last_modified=datetime.now(),
                metadata_json="{}"
            )
        ]

    def test_upload_phase_initialization(self, mock_chromadb_service):
        """Test upload phase initialization"""
        upload_phase = UploadPhase(mock_chromadb_service)

        assert upload_phase.search_service == mock_chromadb_service

    def test_upload_documents_success(self, mock_chromadb_service, mock_processing_strategy, sample_processed_documents):
        """Test successful document upload"""
        upload_phase = UploadPhase(mock_chromadb_service)

        with patch('asyncio.run') as mock_run:
            mock_run.return_value = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6], [0.7, 0.8, 0.9]]

            result = upload_phase.upload_documents(sample_processed_documents, mock_processing_strategy)

        # Verify upload was successful
        assert result.successfully_uploaded == 6  # 3 chunks from doc1 + 3 chunks from doc2 (mocked)
        assert result.failed_uploads == 0
        assert len(result.errors) == 0

        # Verify ChromaDB collection.add was called for each document
        assert mock_chromadb_service.collection.add.call_count == 2

        # Verify processing strategy was called
        assert mock_processing_strategy.create_chromadb_objects.call_count == 2

    def test_upload_documents_with_errors(self, mock_chromadb_service, mock_processing_strategy, sample_processed_documents):
        """Test document upload with errors"""
        upload_phase = UploadPhase(mock_chromadb_service)

        # Configure collection.add to raise exception
        mock_chromadb_service.collection.add.side_effect = Exception("Upload failed")

        with patch('asyncio.run') as mock_run:
            mock_run.return_value = [[0.1, 0.2, 0.3]]

            result = upload_phase.upload_documents(sample_processed_documents, mock_processing_strategy)

        # Verify errors were captured
        assert result.successfully_uploaded == 0
        assert result.failed_uploads == 5  # Total chunks from both documents
        assert len(result.errors) == 2  # One error per document
        assert all("Upload failed" in error for error in result.errors)


class TestDocumentProcessor:

    @pytest.fixture
    def mock_chromadb_service(self):
        """Create mock ChromaDB service"""
        return Mock(spec=ChromaDBService)

    def test_processor_initialization(self, mock_chromadb_service):
        """Test document processor initialization"""
        processor = DocumentProcessor(mock_chromadb_service)

        assert processor.search_service == mock_chromadb_service
        assert processor.pipeline is not None

    @pytest.mark.asyncio
    async def test_process_file(self, mock_chromadb_service):
        """Test single file processing"""
        processor = DocumentProcessor(mock_chromadb_service)

        # Mock file parsing and pipeline processing
        with patch.object(processor, '_parse_file_to_processed_document') as mock_parse, \
             patch.object(processor.pipeline, 'process_documents_batch') as mock_process:

            # Configure mocks
            mock_doc = Mock()
            mock_parse.return_value = mock_doc

            mock_result = Mock()
            mock_result.successfully_uploaded = 5
            mock_result.failed_uploads = 0
            mock_process.return_value = mock_result

            # Test file processing
            result = await processor.process_file(
                file_path="test.md",
                context_name="test_context",
                category="manual"
            )

            # Verify calls
            mock_parse.assert_called_once_with("test.md", "test_context", {"category": "manual"})
            mock_process.assert_called_once_with([mock_doc])

            # Verify result
            assert result == mock_result

    def test_discover_files(self, mock_chromadb_service):
        """Test file discovery"""
        processor = DocumentProcessor(mock_chromadb_service)

        with patch('glob.glob') as mock_glob:
            # Mock glob to return test files
            mock_glob.return_value = ['/path/file1.md', '/path/file2.pdf', '/path/file3.docx']

            files = processor._discover_files('/path', ['*.md', '*.pdf'])

            # Verify glob was called correctly
            assert mock_glob.call_count == 2  # Once for each pattern

            # Verify files were found
            assert len(files) == 3
            assert '/path/file1.md' in files
            assert '/path/file2.pdf' in files
```

## Integration Points with Other Components 🔗

### Dependencies from Parts 1 & 2

- **ChromaDBService**: Document processing relies on ChromaDB service for uploads
- **Embedding Service**: Required for generating vector embeddings of document chunks
- **MCP Tools**: Can verify uploaded documents are searchable via MCP interface

### Provides to Complete System

- **Document Ingestion**: Enables bulk document upload to ChromaDB
- **Content Foundation**: All search functionality depends on processed documents
- **Metadata Structure**: Establishes metadata schema used throughout system

## Completion Criteria ✅

Part 3 is complete when:

1. **✅ ProcessingStrategy updated** with `create_chromadb_objects()` method
2. **✅ Upload pipeline updated** to use ChromaDB collection operations
3. **✅ Upload scripts converted** to use ChromaDB service
4. **✅ Delete scripts working** with ChromaDB filtering
5. **✅ Batch processing implemented** for large document collections
6. **✅ Error handling robust** for upload failures and retries
7. **✅ Integration tests passing** for complete upload-to-search workflow
8. **✅ Performance validated** for batch upload operations

## Known Limitations & Considerations 🚨

### ChromaDB-Specific Constraints

1. **Metadata Schema**: ChromaDB stores all metadata as key-value pairs (simpler than Azure's typed fields)
2. **Batch Size Limits**: ChromaDB may have limits on batch upload size
3. **Transaction Support**: ChromaDB doesn't support transactions like Azure Cognitive Search
4. **Schema Evolution**: Adding new metadata fields requires careful handling

### Performance Considerations

1. **Embedding Generation**: Async embedding generation is critical for performance
2. **Memory Usage**: Large document batches may require memory management
3. **Collection Size**: Very large collections may impact query performance
4. **Concurrent Uploads**: Multiple upload processes may need coordination

### Recommended Best Practices

1. **Batch Size**: Use 25-50 documents per batch for optimal performance
2. **Error Recovery**: Implement retry logic for transient failures
3. **Progress Tracking**: Provide detailed progress reporting for large uploads
4. **Metadata Consistency**: Validate metadata schema before upload
5. **Duplicate Prevention**: Check for existing documents before upload

## Performance Testing Recommendations 📊

### Load Testing Scenarios

1. **Small Batch**: 10 documents, 100 chunks total
2. **Medium Batch**: 100 documents, 1000 chunks total
3. **Large Batch**: 1000 documents, 10000 chunks total
4. **Concurrent Upload**: Multiple upload processes simultaneously

### Metrics to Monitor

- **Upload throughput**: Documents per second
- **Memory usage**: Peak memory during processing
- **ChromaDB performance**: Query response time after large uploads
- **Error rates**: Failed uploads vs total attempts

### Optimization Opportunities

- **Async processing**: Parallel embedding generation
- **Streaming uploads**: Upload documents as they're processed
- **Connection pooling**: Reuse ChromaDB connections
- **Caching**: Cache embeddings for duplicate content

## Next Steps ➡️

After completing Part 3:

1. **Integration Testing**: Test complete workflow from document upload through MCP search
2. **Performance Tuning**: Optimize batch sizes and async processing
3. **Production Deployment**: Deploy ChromaDB with proper persistence and backup
4. **Monitoring Setup**: Implement logging and metrics collection
5. **User Documentation**: Update upload guides and troubleshooting docs

---

**📄 Part 3 completes the ChromaDB implementation by providing the data ingestion layer. This enables the complete workflow: document upload → ChromaDB storage → MCP search interface → user queries.**

**🎯 Implementation Order: Complete Parts 1 & 2 first, then implement Part 3 for full end-to-end functionality.**
