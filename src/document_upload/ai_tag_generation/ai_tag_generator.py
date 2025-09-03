"""
AI-powered tag generator using Azure OpenAI for intelligent document tagging.

This module provides AI-powered tag generation capabilities using Azure OpenAI's
chat completion API. It's designed to integrate seamlessly with the existing
document processing pipeline while providing graceful fallback handling.
"""

import json
import re
import os
import time
from pathlib import Path
from typing import List, Dict, Optional
from openai import AzureOpenAI


class AITagGenerator:
    """AI-powered tag generator using Azure OpenAI (compatible with existing architecture)"""

    def __init__(self):
        """Initialize the AI tag generator with Azure OpenAI configuration."""
        # Use existing Azure AI Foundry configuration (matching updated .env variables)
        self.client = AzureOpenAI(
            azure_endpoint=os.getenv('AZURE_AI_FOUNDRY_ENDPOINT'),
            api_key=os.getenv('AZURE_AI_FOUNDRY_CHAT_COMPLETION_MODEL_KEY'),
            api_version=os.getenv('OPENAI_API_VERSION', '2024-05-01-preview'),
            timeout=120.0  # 2-minute timeout for large documents (per official SDK docs)
        )
        self.model = os.getenv('CHAT_COMPLETION_MODEL', 'gpt-4o-mini')
        self.max_tags = int(os.getenv('AI_TAG_MAX_TAGS_PER_DOCUMENT', '15'))

    def generate_tags(self, content: str, file_path: Path, metadata: Dict) -> List[str]:
        """
        Generate tags using Azure OpenAI API with structured prompt.

        Includes timeout handling and performance monitoring for robust processing
        of large documents.

        Args:
            content: The document content to analyze
            file_path: Path to the source file
            metadata: Document metadata including work_item_id, category, etc.

        Returns:
            List of generated tags, empty list if generation fails

        Note: Synchronous method to maintain compatibility with existing pipeline.
        """
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
        """Build structured prompt for tag generation optimized for ChromaDB metadata"""
        # Determine directory context for better categorization
        directory_name = file_path.parent.name if file_path.parent.name != "." else "root"
        relative_path = str(file_path.relative_to(Path.cwd())) if Path.cwd() in file_path.parents else str(file_path)
        
        return f"""Analyze the file {file_path.name} in the {directory_name} folder. Generate complete metadata for ChromaDB upload and create a JSON configuration entry for batch processing:

1. **Content Analysis**: Document purpose and technical focus
2. **Directory Context**: Functional context from folder location
3. **Functional Tags**: 4-5 searchable tags (directory context + content themes)
4. **Category Classification**: Appropriate category assignment
5. **JSON Configuration**: Create upload config entry for PowerShell script

File: {relative_path}
Work Item ID: {metadata.get('work_item_id', 'unknown')}
Directory Context: {directory_name}
File Type: {file_path.suffix}

Full Document Content:
{content}

Generate comprehensive metadata optimized for ChromaDB search and return ONLY a JSON object:

{{
    "functional_tags": ["category-specific", "content-theme", "use-case", "technology"],
    "technical_terms": ["frameworks", "apis", "tools", "languages"],
    "content_category": ["documentation", "tutorial", "reference", "guide"],
    "process_tags": ["setup", "implementation", "troubleshooting", "configuration"],
    "domain_context": ["web-dev", "data-science", "devops", "architecture"]
}}

Guidelines:
- Maximum {self.max_tags} total tags across all categories
- Prioritize searchability and ChromaDB query optimization
- Use directory context to inform categorization
- Focus on functional tags that reflect document purpose
- Use lowercase, hyphen-separated format
- Consider semantic search patterns for personal documentation
- Balance specific technical terms with broader conceptual tags

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