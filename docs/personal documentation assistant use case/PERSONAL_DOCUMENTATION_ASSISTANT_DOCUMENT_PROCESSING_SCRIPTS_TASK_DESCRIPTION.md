Document processing scripts for the personal documentation retrieval mcp server ->

A highly customized document upload script for a single file or files nested under the same directory.

1. An upload script which accepts a file path or a folder path. And a dictionary consisting of relevant metadata which will be used to directly populate the contents of the search index.
   This script will upload all the file(s) present at the file path or under the folder path to the search index.
   This script will internally handle the chunking and embedding of the files.
   For this script care must be taken to pass the correct metadata dict, such that it matched the search index field schema.
   This script will use the document processing tracker.

2. An upload script which will take in a file path or a folder path and run the document processing pipeline class on the input(i.e discovery phase + processing phase). This script will also have the force reset option to delete the index and all documents in the search index, and then proceed to run the document processing pipeline class on the provided path.
   This will also use the document processing tracker.

3. A delete script which will use a combination of context name + file name to fetch the accurate chunks (if any) and then proceed to delete the chunks. This will also use the document processing tracker.
