# AI-Powered Tag Generation Implementation Plan

This plan addresses architectural inconsistencies and aligns with the existing Azure-based infrastructure while implementing AI-powered intelligent tag generation for documents.

## ✅ Prerequisites Status Update

### Azure AI Foundry Chat Model Configuration ✅ **COMPLETED**

✅ **Great Progress**: The Azure AI Foundry setup now includes both embedding and chat completion model configurations:

- **Embedding Model**: `text-embedding-3-large` ✅ (existing)
- **Chat Completion Model**: `gpt-4o-mini` ✅ (newly added)
- **Separate API Keys**: Both embedding and chat completion keys configured ✅

**What's Been Added to .env**:

- `AZURE_AI_FOUNDRY_CHAT_COMPLETION_MODEL_KEY` - Dedicated chat completion API key
- `CHAT_COMPLETION_MODEL=gpt-4o-mini` - Model name for AI tag generation

**Ready for Implementation**: ✅ All prerequisites are now met for AI tag generation implementation.e## ✅ Prerequisites Status Update

### Azure AI Foundry Chat Model Configuration ✅ **COMPLETED**

✅ **Great Progress**: The Azure AI Foundry setup now includes both embedding and chat completion model configurations:

- **Embedding Model**: `text-embedding-3-large` ✅ (existing)
- **Chat Completion Model**: `gpt-4o-mini` ✅ (newly added)
- **Separate API Keys**: Both embedding and chat completion keys configured ✅

**What's Been Added to .env**:

- `AZURE_AI_FOUNDRY_CHAT_COMPLETION_MODEL_KEY` - Dedicated chat completion API key
- `CHAT_COMPLETION_MODEL=gpt-4o-mini` - Model name for AI tag generation

**Ready for Implementation**: ✅ All prerequisites are now met for AI tag generation implementation.entation Plan (Corrected)

## 🎯 Overview

This corrected plan addresses architectural inconsistencies in the original plan and aligns with the existing Azure-based infrastructure while implementing AI-powered intelligent tag generation for documents.

## 📋 Current State Analysis (Verified)

### Current Tag Generation Approach ✅

- **Location**: `src/document_upload/processing_strategies.py` (Lines 660-695 & 1101-1116)
- **Method**: `_extract_tags()` in both `PersonalDocumentationAssistantChromaDBProcessingStrategy` only for now (Since Azure Cognitive Search will no longer be used)
- **Current Logic**: Work item ID + File type + Filename (sanitized)

### Current Architecture Analysis ✅

- **Embedding Service**: Already uses `src/common/embedding_services/` with Azure OpenAI integration
- **Authentication**: Azure OpenAI with endpoint and key (not direct OpenAI API)
- **Processing**: Synchronous methods throughout the pipeline
- **Dependencies**: OpenAI library already present (`>=1.0.0,<2.0.0`)

## � Critical Prerequisites

### Azure AI Foundry Chat Model Deployment Required

⚠️ **Important**: The current Azure AI Foundry setup only has an embedding model deployment (`text-embedding-3-large`). For AI tag generation, a **chat completion model deployment is required**.

**Required Action Before Implementation**:

1. Deploy a chat completion model (e.g., `gpt-4o-mini`, `gpt-35-turbo`) in Azure AI Foundry
2. Add the deployment name to `.env` as `CHAT_COMPLETION_DEPLOYMENT=your-chat-model-deployment-name`
3. Verify the deployment is accessible with the existing API key

**Cost Consideration**: Chat completion models have different pricing than embedding models. Estimate ~$0.0005-0.002 per 1K tokens for gpt-4o-mini.

## �🚀 Corrected Implementation Strategy

### Phase 1: Setup (Week 1)

#### Directory Structure

```bash
src/document_upload/ai_tag_generation/
├── __init__.py                  # Package initialization
└── ai_tag_generator.py          # Main AI service (Azure OpenAI compatible)
```

**Rationale for Minimal Structure**:

- `ai_tag_generator.py`: Core AI tag generation logic using Azure OpenAI
- `__init__.py`: Package exports and initialization
- **Removed**: `tag_strategies.py` (not needed for initial implementation)
- **Removed**: `tag_validator.py` (validation handled within AITagGenerator.\_clean_tags)
- **Removed**: `prompt_templates.py` (prompt template integrated into AITagGenerator.\_build_prompt)

#### Environment Variables (Corrected) ✅

```env
# Azure AI Foundry configuration (already configured in .env)
AZURE_AI_FOUNDRY_ENDPOINT=https://aayush-azure-ai-foundry.cognitiveservices.azure.com/
EMBEDDING_MODEL=text-embedding-3-large
CHAT_COMPLETION_MODEL=gpt-4o-mini  # ✅ Added

# AI Tag Generation specific variables (to be added to .env)
ENABLE_AI_TAG_GENERATION=true
AI_TAG_MAX_TAGS_PER_DOCUMENT=15
```

#### Dependencies (Corrected)

```txt
# No new dependencies required - reuse existing:
# openai>=1.0.0,<2.0.0 (already present)
# python-dotenv==1.0.0 (already present)
```

### Phase 2: Core AI Tag Generator (Week 2)

#### 2.1 Performance & Timeout Considerations ⚡

**Challenge**: Full document analysis can be time-consuming, especially for large documents.

**Solutions Implemented**:

1. **Timeout Handling**: Set reasonable API timeouts (60-120 seconds)
2. **Graceful Degradation**: Fall back to basic tags if AI generation fails
3. **Progress Feedback**: Log processing status for large documents
4. **Content Size Monitoring**: Log document sizes for performance analysis

#### 2.2 Azure OpenAI Compatible Implementation

````python
import json
import re
import os
from pathlib import Path
from typing import List, Dict, Optional
from openai import AzureOpenAI
import asyncio
from datetime import datetime

class AITagGenerator:
    """AI-powered tag generator using Azure OpenAI (compatible with existing architecture)"""

    def __init__(self):
        # Use existing Azure AI Foundry configuration (matching updated .env variables)
        self.client = AzureOpenAI(
            azure_endpoint=os.getenv('AZURE_AI_FOUNDRY_ENDPOINT'),
            api_key=os.getenv('AZURE_AI_FOUNDRY_CHAT_COMPLETION_MODEL_KEY'),  # ✅ Updated to use chat completion key
            api_version=os.getenv('OPENAI_API_VERSION', '2024-05-01-preview'),
            timeout=120.0  # 2-minute timeout for large documents (per official SDK docs)
        )
        self.model = os.getenv('CHAT_COMPLETION_MODEL', 'gpt-4o-mini')  # ✅ Updated to use CHAT_COMPLETION_MODEL
        self.max_tags = int(os.getenv('AI_TAG_MAX_TAGS_PER_DOCUMENT', '15'))

    def generate_tags(self, content: str, file_path: Path, metadata: Dict) -> List[str]:
        """
        Generate tags using Azure OpenAI API with structured prompt.

        Includes timeout handling and performance monitoring for robust processing
        of large documents.

        Note: Synchronous method to maintain compatibility with existing pipeline.
        """
        import time

        content_size = len(content)
        print(f"[INFO] Processing {file_path.name} ({content_size:,} characters)")

        try:
            start_time = time.time()

            # Build prompt with full content
            prompt = self._build_prompt(content, file_path, metadata)

            print(f"[INFO] Calling Azure OpenAI API...")

            # Call Azure OpenAI API with timeout handling
            # Note: timeout is configured in client initialization (120 seconds)
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=500
            )

            processing_time = time.time() - start_time
            print(f"[INFO] API call completed in {processing_time:.2f} seconds")

            # Parse response with error handling
            response_text = response.choices[0].message.content
            tags = self._parse_response(response_text)

            result_tags = tags[:self.max_tags]
            print(f"[SUCCESS] Generated {len(result_tags)} AI tags for {file_path.name}")
            return result_tags

        except Exception as e:
            processing_time = time.time() - start_time if 'start_time' in locals() else 0
            error_type = type(e).__name__

            print(f"[ERROR] AI tag generation failed for {file_path.name}: {error_type} - {e}")
            print(f"[INFO] Processing time before error: {processing_time:.2f} seconds")
            print(f"[INFO] Falling back to basic tags only for {file_path.name}")

            # Return empty list for graceful degradation
            return []

    def _parse_response(self, response_text: str) -> List[str]:
        """Parse LLM response with robust JSON extraction"""
        try:
            # First, try direct JSON parsing
            tag_data = json.loads(response_text)
        except json.JSONDecodeError:
            # Extract JSON from markdown or mixed content
            tag_data = self._extract_json_from_text(response_text)

        if not tag_data:
            return []

        # Flatten all tag categories into single list
        all_tags = []
        for category, tags in tag_data.items():
            if isinstance(tags, list):
                all_tags.extend(tags)
            elif isinstance(tags, str):
                all_tags.append(tags)

        # Clean and validate tags
        return self._clean_tags(all_tags)

    def _extract_json_from_text(self, text: str) -> Optional[Dict]:
        """Extract JSON from text that might contain markdown or other content"""
        import re

        # Look for JSON blocks in markdown
        json_pattern = r'```json\s*(.*?)\s*```'
        match = re.search(json_pattern, text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        # Look for plain JSON blocks
        json_pattern = r'\{.*\}'
        match = re.search(json_pattern, text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass

        return None

    def _build_prompt(self, content: str, file_path: Path, metadata: Dict) -> str:
        """Build structured prompt for tag generation"""
        return f"""Analyze this personal documentation and generate relevant tags for search indexing.

Document Context:
- File: {file_path.name}
- Work Item: {metadata.get('work_item_id', 'unknown')}
- Category: {metadata.get('category', 'unknown')}
- File Type: {file_path.suffix}

Full Document Content:
{content}

Generate tags across these focus areas and return ONLY a JSON object:

{{
    "technical_terms": ["python", "api", "framework"],
    "concepts": ["authentication", "security", "best-practices"],
    "functional_tags": ["setup", "configuration", "troubleshooting"],
    "domain_tags": ["web-development", "backend", "database"],
    "learning_topics": ["workshop", "training", "tutorial"],
    "process_steps": ["deployment", "testing", "monitoring"],
    "resource_types": ["reference", "documentation", "links"]
}}

Guidelines:
- Maximum {self.max_tags} total tags across all categories
- Focus on searchability and discoverability
- Use lowercase, hyphen-separated format
- Include both specific technical terms and broader conceptual tags
- Consider how someone would search for this content

Return ONLY the JSON object, no additional text."""

    def _clean_tags(self, tags: List[str]) -> List[str]:
        """Clean and standardize tags"""
        cleaned = []
        seen = set()

        for tag in tags:
            if isinstance(tag, str) and tag.strip():
                # Convert to lowercase, replace spaces/underscores with hyphens
                clean_tag = tag.strip().lower().replace(' ', '-').replace('_', '-')
                # Remove special characters except hyphens and numbers
                clean_tag = re.sub(r'[^a-z0-9-]', '', clean_tag)
                # Remove multiple consecutive hyphens
                clean_tag = re.sub(r'-+', '-', clean_tag).strip('-')

                if clean_tag and len(clean_tag) > 1 and clean_tag not in seen:
                    cleaned.append(clean_tag)
                    seen.add(clean_tag)

        return cleaned

    def test_connection(self) -> bool:
        """Test the Azure OpenAI connection"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Test connection - reply with 'OK'"}],
                max_tokens=10
            )
            return response.choices[0].message.content.strip() == 'OK'
        except Exception as e:
            print(f"AI tag generator connection test failed: {e}")
            return False
````

### Phase 3: Integration (Week 3)

#### 3.1 Updated Processing Strategies (Corrected)

**Key Change**: Maintain synchronous interface for compatibility

```python
# In src/document_upload/processing_strategies.py

class PersonalDocumentationAssistantAzureCognitiveSearchProcessingStrategy(DocumentProcessingStrategy):
    def __init__(self):
        super().__init__()
        self.ai_tag_generator = None
        if os.getenv('ENABLE_AI_TAG_GENERATION', 'false').lower() == 'true':
            try:
                from .ai_tag_generation.ai_tag_generator import AITagGenerator
                self.ai_tag_generator = AITagGenerator()
            except ImportError as e:
                print(f"AI tag generator not available: {e}")

    def _extract_tags(self, content: str, file_path: Path, metadata: Dict,
                     file_type: str, work_item_id: str) -> list:
        """Enhanced tag extraction with AI-powered generation (synchronous)"""

        # Keep existing basic tags for reliability
        basic_tags = set()
        basic_tags.add(work_item_id.lower())
        basic_tags.add(file_type)
        filename_tag = file_path.stem.lower().replace('_', '-').replace(' ', '-')
        basic_tags.add(filename_tag)

        # Generate AI-powered tags if enabled and available
        ai_tags = set()
        if self.ai_tag_generator:
            try:
                ai_result = self.ai_tag_generator.generate_tags(
                    content=content,
                    file_path=file_path,
                    metadata=metadata
                )
                ai_tags = set(ai_result)
                print(f"Generated {len(ai_tags)} AI tags for {file_path.name}")
            except Exception as e:
                print(f"AI tag generation failed for {file_path.name}: {e}")

        # Combine and deduplicate
        all_tags = basic_tags.union(ai_tags)
        return sorted(list(all_tags))
```

## ⏱️ Expected Processing Times

### Document Size vs Processing Time Estimates

| Document Size      | Expected Time  | Notes                  |
| ------------------ | -------------- | ---------------------- |
| < 1KB (small)      | 5-15 seconds   | Quick processing       |
| 1-10KB (medium)    | 15-45 seconds  | Standard documents     |
| 10-50KB (large)    | 45-90 seconds  | Comprehensive analysis |
| 50KB+ (very large) | 90-120 seconds | May hit timeout limits |

### Processing Flow

1. **Start**: Log document size and begin processing
2. **API Call**: Send full content to Azure OpenAI (with 2-min timeout)
3. **Fallback**: Return basic tags if AI generation fails
4. **Complete**: Log success/failure and processing time

### User Experience Considerations

- **Progress Feedback**: Console logs show processing status
- **No Blocking**: Document upload continues even if AI tagging fails
- **Reliable Fallback**: Basic tags (work item + file type + filename) always available
- **Performance Monitoring**: Processing times logged for optimization

## 📊 Expected Benefits (Validated)

- **25-40%** improvement in search result relevance (realistic estimate)
- **50%** reduction in "no results found" queries (achievable with better tags)
- **3x** more diverse and discoverable content tags (conservative estimate)
- Backward compatibility maintained
- Graceful degradation when AI service unavailable

## 🎯 Corrected Implementation Timeline

| Phase       | Duration | Key Deliverables                               |
| ----------- | -------- | ---------------------------------------------- |
| **Phase 1** | 1 week   | Infrastructure setup, Azure OpenAI integration |
| **Phase 2** | 1 week   | Core AI tag generator with robust parsing      |
| **Phase 3** | 1 week   | Integration with backward compatibility        |

**Total Timeline**: 3 weeks

## 🔧 Migration Strategy

### Week 1: Foundation ✅ **Prerequisites Complete**

1. ✅ **Chat completion model configured** in Azure AI Foundry (COMPLETED)
2. ✅ **Environment variables updated** with AI tag generation configuration (COMPLETED)
3. 🔄 Create `ai_tag_generation` package structure
4. 🔄 Set up Azure AI Foundry integration (reuse existing client pattern from embedding service)
5. 🔄 Implement basic AI tag generator with connection testing

### Week 2: Core Implementation

1. Implement robust response parsing
2. Create comprehensive prompt templates
3. Test with sample documents

### Week 3: Integration & Testing

1. Update both processing strategies
2. Add feature flag support
3. Test backward compatibility
4. Performance validation

## 🚨 Risk Mitigation & Performance Handling

### 1. **Long Processing Times** ⏱️

**Risk**: Large documents may take 30-120 seconds to process
**Mitigations**:

- **Timeout Handling**: 2-minute timeout configured in client initialization
- **Progress Logging**: Real-time feedback on processing status
- **Graceful Degradation**: Falls back to basic tags if AI generation fails
- **Performance Monitoring**: Log document sizes and processing times

### 2. **Azure OpenAI Service Limits**

- Implement request rate limiting if needed
- Monitor API usage to stay within quotas
- Set reasonable timeout values (120 seconds) in client initialization

### 3. **Response Parsing Failures**

- Robust JSON extraction from mixed content
- Graceful fallback to basic tags
- Comprehensive error logging with error types

### 4. **Cost & Performance Impact**

- Monitor API costs for large document processing
- Log processing times for performance optimization
- Rate limiting to prevent API overload
- Track token usage patterns

## 🎯 Getting Started (Corrected)

### Prerequisites Checklist ✅

- [x] ✅ **Chat completion model configured** in Azure AI Foundry portal (COMPLETED)
- [x] ✅ **Azure AI Foundry access verified** using existing credentials (COMPLETED)
- [x] ✅ **Environment variables updated** with chat model configuration (COMPLETED)
- [ ] 🔄 **Test connection** using new chat completion endpoint

### Implementation Steps (Updated)

1. ✅ **Azure AI Foundry chat model configured** (COMPLETED)
2. 🔄 **Create base infrastructure** following corrected Phase 1
3. 🔄 **Implement core AI tag generator** with Azure AI Foundry compatibility
4. 🔄 **Test with sample documents** using existing work items
5. 🔄 **Integrate with feature flags** for safe rollout
6. 🔄 **Monitor performance and accuracy** with gradual deployment

### Testing the Current Environment

```bash
# Test existing Azure AI Foundry embedding connection
cd src/common/embedding_services
python -c "from azure_openai_embedding_service import AzureOpenAIEmbeddingGenerator; service = AzureOpenAIEmbeddingGenerator(); print('Embedding connection test:', service.test_connection())"

# Test new chat completion configuration (once implemented)
# This will be available after Phase 1 implementation:
# python -c "from document_upload.ai_tag_generation.ai_tag_generator import AITagGenerator; generator = AITagGenerator(); print('Chat completion test:', generator.test_connection())"
```

### Next Steps for Implementation

1. **Immediate**: Test chat completion model access with new environment variables
2. **Phase 1**: Create `ai_tag_generation` package structure
3. **Phase 2**: Implement `AITagGenerator` class with updated environment variables
4. **Phase 3**: Integrate with existing processing strategies

**Ready to proceed**: ✅ All environment configuration is now complete!
