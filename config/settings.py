"""
Configuration management for Work Item Documentation Retriever
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)

class Config:
    """Configuration settings for the application"""
    
    # Azure OpenAI Configuration
    AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
    AZURE_OPENAI_KEY = os.getenv('AZURE_OPENAI_KEY')
    EMBEDDING_DEPLOYMENT = os.getenv('EMBEDDING_DEPLOYMENT', 'text-embedding-ada-002')
    
    # Azure Cognitive Search Configuration
    AZURE_SEARCH_SERVICE = os.getenv('AZURE_SEARCH_SERVICE')
    AZURE_SEARCH_KEY = os.getenv('AZURE_SEARCH_KEY')
    AZURE_SEARCH_INDEX = os.getenv('AZURE_SEARCH_INDEX', 'work-items-index')
    
    # Local Paths
    WORK_ITEMS_PATH = os.getenv('WORK_ITEMS_PATH', r"C:\Users\aayushalok\Desktop\Work Items")
    
    # Application Settings
    CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', '1000'))
    CHUNK_OVERLAP = int(os.getenv('CHUNK_OVERLAP', '200'))
    VECTOR_DIMENSIONS = int(os.getenv('VECTOR_DIMENSIONS', '1536'))
    
    @classmethod
    def validate(cls):
        """Validate that required configuration is present"""
        required_fields = [
            'AZURE_OPENAI_ENDPOINT',
            'AZURE_OPENAI_KEY',
            'AZURE_SEARCH_SERVICE',
            'AZURE_SEARCH_KEY'
        ]
        
        missing_fields = []
        for field in required_fields:
            if not getattr(cls, field):
                missing_fields.append(field)
        
        if missing_fields:
            raise ValueError(f"Missing required configuration: {', '.join(missing_fields)}")
        
        return True
    
    @classmethod
    def get_search_endpoint(cls):
        """Get the full Azure Search endpoint URL"""
        return f"https://{cls.AZURE_SEARCH_SERVICE}.search.windows.net"
