The part of the processing strategy where the document which is to be uploaded is being processed. In this part there is room for extensibility of the code.
The code can be extended by abstracting the implementation details of how the documents is actually processed. Currently in the document processing strategy processing of a document involves reading the document content and then creating relevant metadata fro the document.
For both the reading of the document and extraction of metadata the document itself is a necessary input.
So both of these functions have a common input i.e the document. And since documents can be of many types there is need for extensibility for the read document content and extract metadata functionality.
Analyse the code to truly understand the document processing pipeline and come up with a plan to achieve the extensibility discussed above.
Output your plan in a markdown file.

# Plan for Achieving Extensibility in Document Processing Pipeline

## 1. Abstract Document Reading

- Create an interface or abstract class for document reading.
- Implement specific readers for different document types (e.g., PDF, Word, Markdown).
- Each reader should have a common method signature for reading document content.

## 2. Abstract Metadata Extraction

- Create an interface or abstract class for metadata extraction.
- Implement specific extractors for different document types.
- Each extractor should have a common method signature for extracting metadata.

## 3. Common Document Input

- Ensure that both the document reader and metadata extractor accept a common document input type.
- This could be a base class or interface that all document types implement.

## 4. Extensibility Points

- Identify key points in the processing pipeline where new document types may need to be added.
- Provide clear extension points in the code (e.g., using factory methods or dependency injection).

## 5. Documentation and Examples

- Update documentation to include examples of how to add new document types.
- Provide clear guidelines for developers on how to extend the processing pipeline.

The above instructions are good enough but make sure to not overcomplicate things.
