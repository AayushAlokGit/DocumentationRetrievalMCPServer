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
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "common"))

from common.openai_service import get_openai_service
from file_tracker import DocumentProcessingTracker
from document_utils import discover_markdown_files, read_markdown_file, process_document_chunks
from common.embedding_service import get_embedding_generator
from common.azure_cognitive_search import get_azure_search_service

# Load environment variables
load_dotenv()


def upload_document_to_search(document, service_name, admin_key, index_name):
    """Upload a single processed document to Azure Cognitive Search"""
    
    # Use our centralized AzureCognitiveSearch class
    search_service = get_azure_search_service(service_name, admin_key, index_name)
    return search_service.upload_document(document)
    try:
        if search_documents:
            # Use merge_or_upload instead of upload_documents
            result = search_client.merge_or_upload_documents(documents=search_documents)
            
            # Check for any failed uploads
            failed_uploads = [r for r in result if not r.succeeded]
            successful_uploads = [r for r in result if r.succeeded]
            
            if failed_uploads:
                print(f"[WARNING]  Partial upload - {len(successful_uploads)} succeeded, {len(failed_uploads)} failed")
                for failed in failed_uploads[:3]:  # Show first 3 failures
                    print(f"   Failed: {failed.key} - {failed.error_message}")
                return len(successful_uploads) > 0  # Return True if at least some succeeded
            else:
                print(f"[SUCCESS] Uploaded {len(search_documents)} chunks for: {document['metadata'].get('title', 'Unknown')}")
                return True
                
    except Exception as e:
        print(f"[ERROR] Upload failed for {document['file_path']}: {e}")
        print(f"   First document structure: {search_documents[0] if search_documents else 'No documents'}")
        return False

    return False


def delete_document_from_search(document_id, service_name, admin_key, index_name):
    """Delete a document from Azure Cognitive Search by ID"""
    
    # Use our centralized AzureCognitiveSearch class
    search_service = get_azure_search_service(service_name, admin_key, index_name)
    return search_service.delete_document(document_id)

async def main(specific_work_item_dir: str = None):
    """Main processing function for Work Items directory structure - Individual file processing with idempotency
    
    Args:
        specific_work_item_dir: If provided, use this directory path instead of PERSONAL_DOCUMENTATION_ROOT_DIRECTORY
    """

    # Configuration from environment
    base_PERSONAL_DOCUMENTATION_ROOT_DIRECTORY = os.getenv('PERSONAL_DOCUMENTATION_ROOT_DIRECTORY', r"C:\Users\aayushalok\Desktop\Work Items")
    
    # Use specific work item directory if provided, otherwise use base path
    if specific_work_item_dir:
        PERSONAL_DOCUMENTATION_ROOT_DIRECTORY = specific_work_item_dir
        print(f"[SPECIFIC_DIR] Using specific work item directory: {PERSONAL_DOCUMENTATION_ROOT_DIRECTORY}")
    else:
        PERSONAL_DOCUMENTATION_ROOT_DIRECTORY = base_PERSONAL_DOCUMENTATION_ROOT_DIRECTORY
        print(f"[BASE_DIR] Using base work items directory: {PERSONAL_DOCUMENTATION_ROOT_DIRECTORY}")
    
    azure_openai_endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
    search_service_name = os.getenv('AZURE_SEARCH_SERVICE')
    search_admin_key = os.getenv('AZURE_SEARCH_KEY')
    search_index_name = os.getenv('AZURE_SEARCH_INDEX', 'work-items-index')

    # Initialize processing tracker - always use base path for tracking file location
    tracker = DocumentProcessingTracker("processed_files.json")
    
    print("Starting document processing...")
    print(f"Work Items Path: {PERSONAL_DOCUMENTATION_ROOT_DIRECTORY}")
    if specific_work_item_dir:
        print(f"[WORK_ITEM] Processing specific work item directory: {specific_work_item_dir}")
    else:
        print(f"[ALL_WORK_ITEMS] Processing all work items from base directory")
    print(f"Azure OpenAI Endpoint: {azure_openai_endpoint}")
    print(f"Search Service: {search_service_name}")
    print(f"Search Index: {search_index_name}")
    print(f"Tracking file: {tracker.tracking_file.absolute()}")

    # Initialize OpenAI service
    openai_service = get_openai_service()
    
    # Test the connection
    if not openai_service.test_connection():
        print("[ERROR] Failed to connect to Azure OpenAI. Please check your credentials.")
        return

    # Get tracker stats
    stats = tracker.get_stats()
    print(f"[LIST] Found {stats['total_processed']} previously processed files in tracking")

    # Discover all markdown files
    markdown_files = discover_markdown_files(PERSONAL_DOCUMENTATION_ROOT_DIRECTORY)
    if specific_work_item_dir:
        print(f"[SEARCH] Found {len(markdown_files)} markdown files in specific work item directory")
    else:
        print(f"[SEARCH] Found {len(markdown_files)} total markdown files across work item directories")

    # Filter out already processed files
    files_to_process = []
    skipped_count = 0
    
    for file_path in markdown_files:
        if tracker.is_processed(file_path):
            skipped_count += 1
            print(f"⏭️  Skipping (already processed): {file_path}")
        else:
            files_to_process.append(file_path)
    
    print(f"[SUMMARY] Processing Summary:")
    print(f"   - Total files found: {len(markdown_files)}")
    print(f"   - Already processed: {skipped_count}")
    print(f"   - To process: {len(files_to_process)}")
    
    if not files_to_process:
        if specific_work_item_dir:
            print(f"[SUCCESS] All files in specific work item directory are already processed!")
        else:
            print("[SUCCESS] All files are already processed!")
        return

    # Process files individually
    work_items_summary = {}
    processed_count = 0
    failed_count = 0

    for i, file_path in enumerate(files_to_process, 1):
        try:
            print(f"\n[{i}/{len(files_to_process)}] Processing: {file_path.name}")
            if specific_work_item_dir:
                print(f"   [WORK_ITEM] Processing file from specific work item directory")
                print(f"   [FILE_PATH] Full path: {file_path}")
            
            # Read and parse file
            file_data = read_markdown_file(file_path)
            if not file_data:
                print(f"[WARNING]  Skipping empty file: {file_path.name}")
                continue

            work_item_id = file_data['metadata']['work_item_id']
            print(f"   [METADATA] Extracted work item ID: {work_item_id}")
            
            # Track work items for summary
            if work_item_id not in work_items_summary:
                work_items_summary[work_item_id] = 0
            work_items_summary[work_item_id] += 1

            # Create chunks
            chunks = process_document_chunks(file_data)
            print(f"   Title: Created {len(chunks)} chunks")

            # Generate embeddings
            embedding_generator = get_embedding_generator()
            embeddings = await embedding_generator.generate_embeddings_batch(chunks)
            
            # Validate embeddings
            valid_embeddings = []
            for j, emb in enumerate(embeddings):
                if embedding_generator.validate_embedding(emb):
                    valid_embeddings.append(emb)
                else:
                    print(f"   [WARNING]  Invalid embedding for chunk {j}, using zero vector")
                    valid_embeddings.append(embedding_generator.get_empty_embedding())
            
            print(f"   🧠 Generated {len(valid_embeddings)} embeddings ({len([e for e in embeddings if embedding_generator.validate_embedding(e)])} valid)")

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
                print(f"   [SUCCESS] Successfully processed: {file_data['metadata']['title']} (Work Item: {work_item_id})")
            else:
                failed_count += 1
                print(f"   [ERROR] Failed to upload: {file_path.name} (Work Item: {work_item_id})")

            # Add a small delay to respect rate limits
            if i < len(files_to_process):  # Don't delay after the last file
                await asyncio.sleep(2)

        except Exception as e:
            failed_count += 1
            print(f"   [ERROR] Error processing {file_path.name}: {e}")

    # Final summary
    final_stats = tracker.get_stats()
    if specific_work_item_dir:
        print(f"\n🎉 Processing Complete for specific work item directory!")
    else:
        print(f"\n🎉 Processing Complete!")
    print(f"   - Files processed successfully: {processed_count}")
    print(f"   - Files failed: {failed_count}")
    print(f"   - Total files in tracking: {final_stats['total_processed']}")
    
    if work_items_summary:
        if specific_work_item_dir:
            print(f"   - Work items processed:")
        else:
            print(f"   - Work items affected:")
        for work_item_id, file_count in work_items_summary.items():
            print(f"     • {work_item_id}: {file_count} files")

    if processed_count > 0:
        print(f"   - Documents are now searchable by work item ID and content")
        print(f"   - Run the script again to resume from where it left off")


if __name__ == "__main__":
    asyncio.run(main())
