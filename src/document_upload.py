"""
Document Upload to Azure Cognitive Search
========================================

Main module for processing and uploading Work Items documentation to Azure Cognitive Search.
This module coordinates the document processing pipeline including file discovery, 
chunking, embedding generation, and search index upload.
"""

import os
import asyncio
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict
from dotenv import load_dotenv
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential

# Import our helper modules
from openai_service import get_openai_service
from file_tracker import ProcessingTracker
from document_utils import discover_markdown_files, read_markdown_file, process_document_chunks

# Load environment variables
load_dotenv()


class EmbeddingGenerator:
    def __init__(self):
        self.openai_service = get_openai_service()

    async def generate_embeddings_batch(self, texts: List[str], batch_size: int = 16) -> List[List[float]]:
        """Generate embeddings for text chunks in batches with rate limiting"""
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]

            try:
                # Add delay to respect rate limits
                if i > 0:
                    await asyncio.sleep(1)  # 1 second between batches

                batch_embeddings = await self.openai_service.generate_embeddings_batch(batch)
                
                # Handle None values from failed embeddings
                processed_embeddings = []
                for embedding in batch_embeddings:
                    if embedding is not None:
                        processed_embeddings.append(embedding)
                    else:
                        # Add empty embedding for failed generation
                        empty_embedding = [0.0] * 1536  # Dimension for text-embedding-ada-002
                        processed_embeddings.append(empty_embedding)
                
                all_embeddings.extend(processed_embeddings)

                print(f"Generated embeddings for batch {i//batch_size + 1}/{(len(texts) + batch_size - 1)//batch_size}")

            except Exception as e:
                print(f"Error generating embeddings for batch {i//batch_size + 1}: {e}")
                # Add empty embeddings for failed batch to maintain alignment
                empty_embedding = [0.0] * 1536  # Dimension for text-embedding-ada-002
                all_embeddings.extend([empty_embedding] * len(batch))

        return all_embeddings


def upload_document_to_search(document, service_name, admin_key, index_name):
    """Upload a single processed document to Azure Cognitive Search"""
    
    # Initialize search client
    search_client = SearchClient(
        endpoint=f"https://{service_name}.search.windows.net",
        index_name=index_name,
        credential=AzureKeyCredential(admin_key)
    )

    # Prepare document chunks for upload
    search_documents = []
    
    for i, (chunk, embedding) in enumerate(zip(document['chunks'], document['embeddings'])):
        file_name = Path(document['file_path']).stem
        # Create a more unique document ID using file path hash
        file_hash = hashlib.md5(document['file_path'].encode()).hexdigest()[:8]
        doc_id = f"{file_hash}_{i}"

        # Convert timestamp to ISO format for Azure Search
        last_modified_timestamp = document['metadata'].get('last_modified')
        if last_modified_timestamp:
            last_modified_iso = datetime.fromtimestamp(last_modified_timestamp).isoformat() + 'Z'
        else:
            last_modified_iso = datetime.now().isoformat() + 'Z'

        # First, try uploading without vector to isolate the issue
        search_doc = {
            '@search.action': 'upload',
            'id': doc_id,
            'content': str(chunk),
            'file_path': str(document['file_path']),
            'title': str(document['metadata'].get('title', '')),
            'work_item_id': str(document['metadata'].get('work_item_id', '')),
            'tags': ','.join(document['metadata'].get('tags', [])) if document['metadata'].get('tags') else '',
            'last_modified': last_modified_iso,
            'chunk_index': i
        }
        
        # Only add vector if embedding is valid
        if embedding and isinstance(embedding, list) and len(embedding) == 1536:
            # Ensure all values are floats and not None
            clean_embedding = [float(x) if x is not None else 0.0 for x in embedding]
            search_doc['content_vector'] = clean_embedding
        
        search_documents.append(search_doc)

    # Upload document chunks
    try:
        if search_documents:
            # Use merge_or_upload instead of upload_documents
            result = search_client.merge_or_upload_documents(documents=search_documents)
            
            # Check for any failed uploads
            failed_uploads = [r for r in result if not r.succeeded]
            successful_uploads = [r for r in result if r.succeeded]
            
            if failed_uploads:
                print(f"⚠️  Partial upload - {len(successful_uploads)} succeeded, {len(failed_uploads)} failed")
                for failed in failed_uploads[:3]:  # Show first 3 failures
                    print(f"   Failed: {failed.key} - {failed.error_message}")
                return len(successful_uploads) > 0  # Return True if at least some succeeded
            else:
                print(f"✅ Uploaded {len(search_documents)} chunks for: {document['metadata'].get('title', 'Unknown')}")
                return True
                
    except Exception as e:
        print(f"❌ Upload failed for {document['file_path']}: {e}")
        print(f"   First document structure: {search_documents[0] if search_documents else 'No documents'}")
        return False

    return False


def upload_to_search(documents, service_name, admin_key, index_name):
    """Upload processed documents to Azure Cognitive Search"""

    # Initialize search client
    search_client = SearchClient(
        endpoint=f"https://{service_name}.search.windows.net",
        index_name=index_name,
        credential=AzureKeyCredential(admin_key)
    )

    # Prepare documents for upload
    search_documents = []

    for doc in documents:
        for i, (chunk, embedding) in enumerate(zip(doc['chunks'], doc['embeddings'])):
            file_name = Path(doc['file_path']).stem
            doc_id = f"{file_name}_chunk_{i}".replace(" ", "_")

            search_doc = {
                'id': doc_id,
                'content': chunk,
                'content_vector': embedding,
                'file_path': doc['file_path'],
                'title': doc['metadata'].get('title', ''),
                'work_item_id': doc['metadata'].get('work_item_id', ''),
                'tags': doc['metadata'].get('tags', []),
                'last_modified': doc['metadata'].get('last_modified'),
                'chunk_index': i
            }
            search_documents.append(search_doc)

    # Upload documents in batches
    try:
        batch_size = 100  # Azure Cognitive Search batch limit
        for i in range(0, len(search_documents), batch_size):
            batch = search_documents[i:i + batch_size]
            result = search_client.upload_documents(documents=batch)
            print(f"Uploaded batch {i//batch_size + 1}/{(len(search_documents) + batch_size - 1)//batch_size}: {len(batch)} documents")
        
        print(f"Successfully uploaded {len(search_documents)} total documents")
        return True
    except Exception as e:
        print(f"Upload failed: {e}")
        return False


async def main():
    """Main processing function for Work Items directory structure - Individual file processing with idempotency"""

    # Configuration from environment
    work_items_path = os.getenv('WORK_ITEMS_PATH', r"C:\Users\aayushalok\Desktop\Work Items")
    azure_openai_endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
    azure_openai_key = os.getenv('AZURE_OPENAI_KEY')
    embedding_deployment = os.getenv('EMBEDDING_DEPLOYMENT', 'text-embedding-ada-002')
    search_service_name = os.getenv('AZURE_SEARCH_SERVICE')
    search_admin_key = os.getenv('AZURE_SEARCH_KEY')
    search_index_name = os.getenv('AZURE_SEARCH_INDEX', 'work-items-index')

    # Initialize processing tracker
    tracker = ProcessingTracker("processed_files.json")
    
    print("Starting document processing...")
    print(f"Work Items Path: {work_items_path}")
    print(f"Azure OpenAI Endpoint: {azure_openai_endpoint}")
    print(f"Search Service: {search_service_name}")
    print(f"Search Index: {search_index_name}")
    print(f"Tracking file: {tracker.tracking_file.absolute()}")

    # Initialize OpenAI service
    openai_service = get_openai_service()
    
    # Test the connection
    if not openai_service.test_connection():
        print("❌ Failed to connect to Azure OpenAI. Please check your credentials.")
        return

    # Get tracker stats
    stats = tracker.get_stats()
    print(f"📋 Found {stats['total_processed']} previously processed files in tracking")

    # Discover all markdown files
    markdown_files = discover_markdown_files(work_items_path)
    print(f"🔍 Found {len(markdown_files)} total markdown files across work item directories")

    # Filter out already processed files
    files_to_process = []
    skipped_count = 0
    
    for file_path in markdown_files:
        if tracker.is_processed(file_path):
            skipped_count += 1
            print(f"⏭️  Skipping (already processed): {file_path.name}")
        else:
            files_to_process.append(file_path)
    
    print(f"📊 Processing Summary:")
    print(f"   - Total files found: {len(markdown_files)}")
    print(f"   - Already processed: {skipped_count}")
    print(f"   - To process: {len(files_to_process)}")
    
    if not files_to_process:
        print("✅ All files are already processed!")
        return

    # Process files individually
    work_items_summary = {}
    processed_count = 0
    failed_count = 0

    for i, file_path in enumerate(files_to_process, 1):
        try:
            print(f"\n[{i}/{len(files_to_process)}] Processing: {file_path.name}")
            
            # Read and parse file
            file_data = read_markdown_file(file_path)
            if not file_data:
                print(f"⚠️  Skipping empty file: {file_path.name}")
                continue

            work_item_id = file_data['metadata']['work_item_id']
            
            # Track work items for summary
            if work_item_id not in work_items_summary:
                work_items_summary[work_item_id] = 0
            work_items_summary[work_item_id] += 1

            # Create chunks
            chunks = process_document_chunks(file_data)
            print(f"   📝 Created {len(chunks)} chunks")

            # Generate embeddings
            embedding_generator = EmbeddingGenerator()
            embeddings = await embedding_generator.generate_embeddings_batch(chunks)
            
            # Validate embeddings
            valid_embeddings = []
            for j, emb in enumerate(embeddings):
                if emb and isinstance(emb, list) and len(emb) == 1536:
                    valid_embeddings.append(emb)
                else:
                    print(f"   ⚠️  Invalid embedding for chunk {j}, using zero vector")
                    valid_embeddings.append([0.0] * 1536)
            
            print(f"   🧠 Generated {len(valid_embeddings)} embeddings ({len([e for e in embeddings if e and len(e) == 1536])} valid)")

            # Prepare document
            document = {
                'file_path': str(file_path),
                'metadata': file_data['metadata'],
                'chunks': chunks,
                'embeddings': valid_embeddings
            }

            # Upload to search
            upload_success = upload_document_to_search(
                document, search_service_name, search_admin_key, search_index_name
            )

            if upload_success:
                # Mark as processed only after successful upload
                tracker.mark_processed(file_path)
                tracker.save()
                processed_count += 1
                print(f"   ✅ Successfully processed: {file_data['metadata']['title']}")
            else:
                failed_count += 1
                print(f"   ❌ Failed to upload: {file_path.name}")

            # Add a small delay to respect rate limits
            if i < len(files_to_process):  # Don't delay after the last file
                await asyncio.sleep(2)

        except Exception as e:
            failed_count += 1
            print(f"   ❌ Error processing {file_path.name}: {e}")

    # Final summary
    final_stats = tracker.get_stats()
    print(f"\n🎉 Processing Complete!")
    print(f"   - Files processed successfully: {processed_count}")
    print(f"   - Files failed: {failed_count}")
    print(f"   - Total files in tracking: {final_stats['total_processed']}")
    
    if work_items_summary:
        print(f"   - Work items affected:")
        for work_item_id, file_count in work_items_summary.items():
            print(f"     • {work_item_id}: {file_count} files")

    if processed_count > 0:
        print(f"   - Documents are now searchable by work item ID and content")
        print(f"   - Run the script again to resume from where it left off")


if __name__ == "__main__":
    asyncio.run(main())
