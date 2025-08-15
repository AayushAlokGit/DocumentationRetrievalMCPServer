# Tool Result Formatting: Importance and Best Practices

## Executive Summary

Proper formatting of tool results is crucial for creating effective Model Context Protocol (MCP) servers that provide valuable, actionable information to Language Learning Models (LLMs) and end users. This document outlines the critical importance of result formatting and establishes best practices for optimal user experience.

## Why Tool Result Formatting Matters

### 1. **Enhanced LLM Comprehension**

- **Structured Data Processing**: Well-formatted results enable LLMs to parse and understand complex information more effectively
- **Context Preservation**: Proper formatting maintains semantic relationships between data elements
- **Reduced Hallucination**: Clear structure reduces the likelihood of LLMs misinterpreting or fabricating information
- **Improved Reasoning**: Structured formats support better analytical reasoning and decision-making

### 2. **Superior User Experience**

- **Readability**: Professional formatting makes results immediately comprehensible to human users
- **Scanability**: Well-structured content allows users to quickly locate relevant information
- **Professional Presentation**: Clean formatting creates trust and confidence in the system
- **Reduced Cognitive Load**: Organized information reduces mental effort required to process results

### 3. **Operational Efficiency**

- **Faster Decision Making**: Quick identification of key information accelerates workflows
- **Reduced Follow-up Queries**: Comprehensive formatting minimizes need for clarification
- **Improved Tool Adoption**: Better formatted tools are more likely to be used consistently
- **Enhanced Productivity**: Users can act on information without additional processing steps

## Formatting Principles

### 1. **Hierarchical Structure**

```markdown
# Primary Header (Tool Purpose)

## Secondary Headers (Data Categories)

### Tertiary Headers (Subcategories)
```

### 2. **Visual Hierarchy**

- **Bold Text**: For emphasis and key terms
- **Code Blocks**: For technical data, IDs, and structured information
- **Tables**: For comparative data and structured listings
- **Lists**: For enumerated items and step-by-step information

### 3. **Information Density Balance**

- Provide comprehensive information without overwhelming the user
- Use white space effectively to separate logical sections
- Prioritize most important information at the top
- Include summary statistics where relevant

## Best Practices by Tool Type

### Search Results Tools

```markdown
# Search Results

**Query**: [search term]
**Results Found**: [count with comma formatting]
**Search Type**: [hybrid/vector/semantic/text]

## Document Matches

**[Document Title]**

- **Context**: [context_name]
- **File**: `[filename]`
- **Relevance Score**: [score]

[Content preview...]
```

### Information Discovery Tools

```markdown
# Document Contexts

**Total Contexts**: [count]
**Document Distribution**: [statistics]

## Available Contexts

1. **[Context Name]** ([document_count] documents)
   - **Primary Focus**: [description]
   - **File Types**: [types]
   - **Last Updated**: [date]
```

### Statistical Summary Tools

```markdown
# Search Index Summary

**Total Documents**: [count with commas]
**Active Contexts**: [count]
**Storage Utilization**: [statistics]

## Document Distribution

| Context | Document Count | Percentage |
| ------- | -------------- | ---------- |
| [name]  | [count]        | [percent]% |
```

## Formatting Anti-Patterns to Avoid

### 1. **Excessive Emoji Usage**

❌ **Avoid**: `🔍 Search Results 📄 Found 514 documents! 🎉`
✅ **Prefer**: `# Search Results\n**Documents Found**: 514`

**Rationale**:

- Emojis can interfere with LLM parsing
- Professional contexts require formal presentation
- Accessibility tools may struggle with emoji interpretation
- International users may have different emoji interpretations

### 2. **Inconsistent Formatting**

❌ **Avoid**: Mixed header styles, inconsistent bolding, varying list formats
✅ **Prefer**: Consistent markdown structure throughout all tools

### 3. **Information Overload**

❌ **Avoid**: Dumping raw data without structure
✅ **Prefer**: Organized, hierarchical presentation with clear sections

### 4. **Insufficient Context**

❌ **Avoid**: Bare results without explanatory headers or metadata
✅ **Prefer**: Clear headers, counts, and contextual information

## Implementation Guidelines

### 1. **Result Headers**

Always start with a clear header indicating the tool's purpose and scope:

```python
def format_search_results(results, query, search_type):
    output = f"# Search Results\n"
    output += f"**Query**: {query}\n"
    output += f"**Results Found**: {len(results):,}\n"
    output += f"**Search Type**: {search_type}\n\n"
    return output
```

### 2. **Statistical Information**

Include relevant counts and statistics with proper formatting:

```python
def format_count(count):
    return f"{count:,}"  # Adds comma separators for readability

def format_percentage(value, total):
    percentage = (value / total) * 100
    return f"{percentage:.1f}%"
```

### 3. **Content Structuring**

Organize information logically with clear sections:

```python
def format_document_contexts(contexts):
    output = "# Document Contexts\n"
    output += f"**Total Contexts**: {len(contexts):,}\n\n"

    output += "## Available Contexts\n"
    for i, context in enumerate(contexts, 1):
        output += f"{i}. **{context.name}** ({context.doc_count:,} documents)\n"
        output += f"   - **Description**: {context.description}\n"
        output += f"   - **File Types**: {', '.join(context.file_types)}\n\n"

    return output
```

## Quality Metrics

### 1. **Readability Indicators**

- Clear hierarchical structure (headers, subheaders)
- Consistent formatting patterns
- Appropriate use of emphasis (bold, code blocks)
- Logical information flow

### 2. **LLM Compatibility Metrics**

- Structured markdown that parses cleanly
- No ambiguous formatting elements
- Clear semantic boundaries between information sections
- Consistent data presentation patterns

### 3. **User Experience Indicators**

- Quick information location (within 3 seconds)
- No need for additional clarification questions
- Professional, business-appropriate presentation
- Accessibility-friendly formatting

## Case Study: Before and After

### Before (Poor Formatting)

```
Found some documents: doc1.md, doc2.pdf, doc3.docx in contexts work-item-1, project-alpha, documentation
```

### After (Professional Formatting)

```markdown
# Search Results

**Query**: architecture documentation
**Results Found**: 3
**Search Type**: hybrid

## Document Matches

1. **Architecture Overview**

   - **Context**: work-item-1
   - **File**: `doc1.md`
   - **Type**: Markdown

2. **Technical Specifications**

   - **Context**: project-alpha
   - **File**: `doc2.pdf`
   - **Type**: PDF

3. **Implementation Guide**
   - **Context**: documentation
   - **File**: `doc3.docx`
   - **Type**: Word Document
```

## Conclusion

Effective tool result formatting is not merely aesthetic—it's a fundamental component of system usability and reliability. By implementing consistent, professional formatting standards:

- **LLMs** receive structured, parseable information that enhances their reasoning capabilities
- **Users** experience faster, more confident decision-making through clear presentation
- **Systems** achieve higher adoption rates and user satisfaction

The investment in proper formatting pays dividends in user experience, system reliability, and operational efficiency. As MCP servers become integral to AI-assisted workflows, formatting quality becomes a competitive differentiator and a marker of professional software development.

## References

- [Markdown Formatting Guide](https://guides.github.com/features/mastering-markdown/)
- [Accessibility in Technical Documentation](https://www.w3.org/WAI/WCAG21/Understanding/)
- [Model Context Protocol Specification](https://github.com/modelcontextprotocol/specification)
- [LLM Information Processing Best Practices](https://platform.openai.com/docs/guides/prompt-engineering)
