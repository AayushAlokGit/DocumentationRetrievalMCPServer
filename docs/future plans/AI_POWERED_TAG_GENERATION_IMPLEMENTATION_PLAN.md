# AI-Powered Tag Generation Implementation Plan

## 🎯 Overview

This plan outlines the implementation of AI-powered intelligent tag generation for documents processed through the Personal Documentation Assistant pipeline. The goal is to replace basic rule-based tag extraction with sophisticated AI analysis that generates contextually relevant, searchable tags.

## 📋 Current State Analysis

### Current Tag Generation Approach

- **Location**: `src/document_upload/processing_strategies.py`
- **Method**: `_extract_tags()` in both Azure Cognitive Search and ChromaDB strategies
- **Current Logic**: Work item ID + File type + Filename (sanitized)

### Limitations

- ❌ No semantic understanding of content
- ❌ Limited contextual relevance
- ❌ Misses technical terms and key concepts

## 🚀 Implementation Strategy

### Phase 1: Setup (Week 1)

#### Directory Structure

```bash
src/document_upload/ai_tag_generation/
├── ai_tag_generator.py          # Main AI service
├── tag_strategies.py            # PersonalDocumentationTaggingStrategy
├── tag_validator.py             # Quality validation
└── prompt_templates.py          # LLM prompts
```

#### Environment Variables

```env
OPENAI_API_KEY=your_openai_key
AI_TAG_GENERATION_MODEL=gpt-4o-mini
ENABLE_AI_TAG_GENERATION=true
AI_TAG_MAX_TAGS_PER_DOCUMENT=15
```

#### Dependencies

```txt
openai>=1.0.0
tiktoken>=0.5.0
tenacity>=8.0.0
```

### Phase 2: Core AI Tag Generator (Week 2)

#### 2.1 Main AI Tag Generator Implementation

**Key Features**:

- **Content Analysis**: Extract key concepts, technical terms, and domain-specific language
- **Context Awareness**: Use file path, work item context, and existing metadata
- **Multi-Strategy Support**: Different approaches for different document types
- **Caching**: Cache results to avoid redundant API calls
- **Fallback Logic**: Graceful degradation when AI service unavailable

**Concrete Implementation**:

```python
class AITagGenerator:
    def __init__(self):
        self.client = openai.AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.model = os.getenv('AI_TAG_GENERATION_MODEL', 'gpt-4o-mini')
        self.max_tags = int(os.getenv('AI_TAG_MAX_TAGS_PER_DOCUMENT', '15'))

    async def generate_tags(self, content: str, file_path: Path, metadata: Dict) -> List[str]:
        """Generate tags using OpenAI API with structured prompt"""

        # Step 1: Prepare content for analysis (limit to first 3000 chars)
        content_preview = content[:3000] + "..." if len(content) > 3000 else content

        # Step 2: Build prompt with context
        prompt = self._build_prompt(content_preview, file_path, metadata)

        # Step 3: Call OpenAI API
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=500
            )

            # Step 4: Parse JSON response and extract tags
            response_text = response.choices[0].message.content
            tag_data = json.loads(response_text)

            # Step 5: Flatten all tag categories into single list
            all_tags = []
            for category, tags in tag_data.items():
                if isinstance(tags, list):
                    all_tags.extend(tags)

            # Step 6: Clean and validate tags
            cleaned_tags = self._clean_tags(all_tags)

            return cleaned_tags[:self.max_tags]

        except Exception as e:
            print(f"AI tag generation failed: {e}")
            return []

    def _build_prompt(self, content: str, file_path: Path, metadata: Dict) -> str:
        """Build structured prompt for tag generation"""
        return f"""
Analyze this personal documentation and generate relevant tags for search indexing.

Document Context:
- File: {file_path.name}
- Work Item: {metadata.get('work_item_id', 'unknown')}
- Category: {metadata.get('category', 'unknown')}

Content Preview:
{content}

Generate tags across these focus areas and return as JSON:
1. Technical Terms (languages, frameworks, tools, technologies, APIs)
2. Concepts (methodologies, patterns, principles, ideas)
3. Functional Tags (what users can accomplish with this document)
4. Domain Tags (subject matter areas, business domains)
5. Learning Topics (for educational/workshop content)
6. Process Steps (for workflow/procedure content)
7. Resource Types (for reference materials and collections)

Example Return format:
{{
    "technical_terms": ["python", "api", "framework"],
    "concepts": ["authentication", "security", "best-practices"],
    "functional_tags": ["setup", "configuration", "troubleshooting"],
    "domain_tags": ["web-development", "backend", "database"],
    "learning_topics": ["workshop", "training", "tutorial"],
    "process_steps": ["deployment", "testing", "monitoring"],
    "resource_types": ["reference", "documentation", "links"]
}}

Max {self.max_tags} total tags. Focus on searchability and discoverability.
"""

    def _clean_tags(self, tags: List[str]) -> List[str]:
        """Clean and standardize tags"""
        cleaned = []
        for tag in tags:
            if isinstance(tag, str) and tag.strip():
                # Convert to lowercase, replace spaces with hyphens
                clean_tag = tag.strip().lower().replace(' ', '-').replace('_', '-')
                # Remove special characters except hyphens
                clean_tag = re.sub(r'[^a-z0-9-]', '', clean_tag)
                if clean_tag and len(clean_tag) > 1:
                    cleaned.append(clean_tag)

        # Remove duplicates while preserving order
        return list(dict.fromkeys(cleaned))
```

**Core Methods**:

#### 2.2 Tag Generation Process Flow

**Step-by-Step Process**:

1. **Content Preparation**: Truncate content to manageable size (3000 chars) for API call
2. **Context Building**: Extract file name, work item, category from metadata
3. **Prompt Construction**: Build structured prompt with focus areas and JSON format
4. **API Call**: Send to OpenAI with temperature=0.3 for consistency
5. **Response Parsing**: Parse JSON response containing categorized tags
6. **Tag Cleaning**: Standardize format (lowercase, hyphens, no special chars)
7. **Deduplication**: Remove duplicates while preserving order
8. **Limit Enforcement**: Return max 15 tags as configured
   PERSONAL_DOCUMENTATION_PROMPT = """
   Analyze this personal documentation and generate relevant tags for search indexing.

Document Context:

- File: {file_name}
- Work Item: {work_item_id}
- Category: {category}

Content Preview:
{content_preview}

Generate tags across these comprehensive focus areas:

1. Technical Terms (languages, frameworks, tools, technologies, APIs)
2. Concepts (methodologies, patterns, principles, ideas)
3. Functional Tags (what users can accomplish with this document)
4. Domain Tags (subject matter areas, business domains)
5. Learning Topics (for educational/workshop content)
6. Process Steps (for workflow/procedure content)
7. Resource Types (for reference materials and collections)

Guidelines:

- Prioritize searchability and discoverability
- Include both specific technical terms and broader conceptual tags
- Consider how someone would search for this content

### Phase 3: Integration (Week 3)

#### Update Processing Strategies

```python
async def _extract_tags(self, content: str, file_path: Path, metadata: Dict,
                       file_type: str, work_item_id: str, post) -> List[str]:
    """Enhanced tag extraction with AI-powered generation"""

    # Keep existing basic tags
    basic_tags = {work_item_id.lower(), file_type, filename_tag}

    # Generate AI-powered tags if enabled
    ai_tags = set()
    if self.ai_tag_generator and os.getenv('ENABLE_AI_TAG_GENERATION', 'false').lower() == 'true':
        try:
            ai_result = await self.ai_tag_generator.generate_tags(
                content=content, file_path=file_path, metadata=metadata
            )
            ai_tags = set(ai_result.all_tags)
        except Exception as e:
            print(f"AI tag generation failed: {e}")

    # Combine and deduplicate
    all_tags = basic_tags.union(ai_tags)
    return sorted(list(all_tags))
```

## 📊 Expected Benefits

- **25-40%** improvement in search result relevance
- **50%** reduction in "no results found" queries
- **3x** more diverse and discoverable content tags
- Automated metadata enrichment
- Consistent tagging across document types

## 🎯 Implementation Timeline

| Phase       | Duration | Key Deliverables                                |
| ----------- | -------- | ----------------------------------------------- |
| **Phase 1** | 1 week   | Infrastructure setup, environment configuration |
| **Phase 2** | 1 week   | Core AI tag generator implementation            |
| **Phase 3** | 1 week   | Integration with existing processing strategies |

**Total Timeline**: 3 weeks

## 🚀 Getting Started

1. **Set up development environment** with required dependencies
2. **Configure AI service credentials** in environment variables
3. **Create base infrastructure** following Phase 1 guidelines
4. **Implement core AI tag generator** with unified prompt
5. **Integrate with existing processing pipeline** using feature flags
6. **Test with sample documents** and validate tag quality

```

```
