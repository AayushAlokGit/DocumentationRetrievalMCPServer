For us to be able to effectively search for the documents , using Azure COgntiive Search it is highly important that the metadata values that we populate for the index entry for each document corresponding to a particular chunk of a file which is to be uploaded to the Azure Cognitive search index.

The use case of this project is to be able to query any of the documentation files.
Now for the usecase of this project figuring out the metadata for the files is not too complex.
There are certain general trends that will be present in the personal documentation files and the folder structure.

The Personal Documentation Folder (respresented by the work item path env variable) will consists of the following ->

1. MarkDown and/or text files at root
2. Markdown and/or Text files at any child directory level of root.

In case of there are child directories , present under the root. The name of the directory provides valuable information. This information maybe about the context of the files contained in this directory.
For example if directory name -> "Task 12" , it means that the files under this are related to "Task 12" and "Task 12" becomes a keyword of interest for all the files present under this directory even those present in its child directories.

Similarly from the markdown files and text files we can clearly extract keywords from all the text formatted as headings.

This is the strategy for obtaining the relevant metadata for this project.
