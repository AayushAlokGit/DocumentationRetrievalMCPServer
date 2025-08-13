# Configuration and Dependencies

## Simplified Project File Structure

```
WorkItemDocumentationRetriever/
├── src/
│   ├── server/
│   │   ├── __init__.py
│   │   └── main.py                  # MCP server entry point
│   ├── services/
│   │   ├── __init__.py
│   │   ├── azure_openai.py          # Azure OpenAI integration
│   │   └── azure_search.py          # Azure Cognitive Search operations
│   └── utils/
│       ├── __init__.py
│       ├── config.py                # Configuration management
│       └── logger.py                # Logging utilities
├── data/
│   └── work-items/                  # Local markdown files
├── scripts/
│   ├── setup.py                     # Project setup automation
│   ├── upload_documents.py          # Document upload script
│   └── validate_config.py           # Configuration validation
├── tests/
│   ├── __init__.py
│   └── test_server.py
├── docs/
│   ├── 01-Architecture.md
│   ├── 02-AzureSetup.md
│   ├── 03-DocumentUpload.md
│   ├── 04-MCPServerImplementation.md
│   ├── 05-Configuration.md
│   └── 06-Timeline.md
├── .env.example                     # Environment variables template
├── requirements.txt                 # Python dependencies
├── .gitignore
└── README.md
```

## Python Dependencies

Create a `requirements.txt` file with the following dependencies:

```txt
# Core MCP and server dependencies
mcp>=1.0.0
fastapi>=0.104.0
uvicorn>=0.24.0
pydantic>=2.0.0

# Azure OpenAI integration
openai>=1.0.0
azure-identity>=1.15.0

# Azure Cognitive Search
azure-search-documents>=11.4.0
azure-core>=1.29.0

# Document processing
python-markdown>=3.5.0
python-frontmatter>=1.0.0
beautifulsoup4>=4.12.0
pypdf>=3.17.0
python-docx>=0.8.11

# File system monitoring
watchdog>=3.0.0

# Utilities
python-dotenv>=1.0.0
aiofiles>=23.2.1
httpx>=0.25.0
numpy>=1.24.0
pandas>=2.1.0

# Development and testing
pytest>=7.4.0
pytest-asyncio>=0.21.0
black>=23.0.0
flake8>=6.0.0
mypy>=1.5.0
```

## Environment Variables

Create a `.env.example` file:

```env
# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=https://your-openai-service.openai.azure.com/
AZURE_OPENAI_API_KEY=your-openai-api-key
AZURE_OPENAI_DEPLOYMENT_NAME=your-gpt4-deployment-name
AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME=your-embedding-deployment-name

# Azure Cognitive Search Configuration
AZURE_SEARCH_SERVICE_NAME=your-search-service-name
AZURE_SEARCH_ADMIN_KEY=your-search-admin-key
AZURE_SEARCH_INDEX_NAME=work-items-index

# Application Configuration
PERSONAL_DOCUMENTATION_ROOT_DIRECTORY=./data/work-items
MCP_SERVER_PORT=3000
LOG_LEVEL=INFO

# Optional: Azure Key Vault (for production)
AZURE_KEY_VAULT_URL=https://your-keyvault.vault.azure.net/
USE_KEY_VAULT=false
```

## VS Code Settings

Create `.vscode/settings.json`:

```json
{
  "mcp.servers": {
    "work-items": {
      "command": "python",
      "args": ["src/server/main.py"],
      "cwd": "${workspaceFolder}",
      "env": {
        "PERSONAL_DOCUMENTATION_ROOT_DIRECTORY": "./data/work-items"
      }
    }
  },
  "python.defaultInterpreterPath": "./venv/Scripts/python.exe",
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["tests"]
}
```

## MCP Server Configuration

Create `config/mcp-config.json`:

```json
{
  "server": {
    "name": "work-items-mcp",
    "version": "1.0.0",
    "description": "MCP server for work item documentation retrieval and question answering"
  },
  "capabilities": {
    "resources": true,
    "tools": true,
    "prompts": false,
    "logging": true
  },
  "tools": [
    {
      "name": "search_work_items",
      "description": "Search for relevant work items using natural language query",
      "enabled": true
    },
    {
      "name": "ask_question",
      "description": "Ask a question about work items and get an AI-generated answer",
      "enabled": true
    },
    {
      "name": "get_work_item_details",
      "description": "Get detailed information about a specific work item",
      "enabled": true
    },
    {
      "name": "list_work_items",
      "description": "List available work items with metadata",
      "enabled": true
    },
    {
      "name": "update_knowledge_base",
      "description": "Refresh the document index with latest changes",
      "enabled": true
    }
  ],
  "search": {
    "default_limit": 5,
    "max_limit": 20,
    "chunk_size": 1000,
    "chunk_overlap": 200
  },
  "chat": {
    "temperature": 0.7,
    "max_tokens": 1000,
    "system_prompt_template": "You are a helpful assistant that answers questions about work items based on provided documentation.\n\nContext: {context}\n\nGuidelines:\n- Answer based only on the provided context\n- If information is not available, say so clearly\n- Provide specific references to work items when possible\n- Be concise but comprehensive\n- Use a professional, helpful tone"
  }
}
```

## Development Setup Scripts

### Setup Script (`scripts/setup.py`)

```python
#!/usr/bin/env python3
"""
Setup script for Work Item Documentation MCP Server
"""
import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd, cwd=None):
    """Run a command and return the result"""
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, check=True,
                              capture_output=True, text=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {cmd}")
        print(f"Error output: {e.stderr}")
        sys.exit(1)

def setup_virtual_environment():
    """Set up Python virtual environment"""
    print("Setting up Python virtual environment...")

    if not Path("venv").exists():
        run_command("python -m venv venv")
        print("✓ Virtual environment created")
    else:
        print("✓ Virtual environment already exists")

def install_dependencies():
    """Install Python dependencies"""
    print("Installing Python dependencies...")

    # Activate virtual environment and install dependencies
    if os.name == 'nt':  # Windows
        pip_cmd = "venv\\Scripts\\pip install -r requirements.txt"
    else:  # Unix/Linux/Mac
        pip_cmd = "venv/bin/pip install -r requirements.txt"

    run_command(pip_cmd)
    print("✓ Dependencies installed")

def create_directories():
    """Create necessary directories"""
    print("Creating project directories...")

    directories = [
        "data/work-items",
        "logs",
        "scripts",
        "tests",
        "config"
    ]

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)

    print("✓ Directories created")

def create_config_files():
    """Create configuration files if they don't exist"""
    print("Creating configuration files...")

    # Create .env file from template if it doesn't exist
    if not Path(".env").exists():
        if Path(".env.example").exists():
            import shutil
            shutil.copy(".env.example", ".env")
            print("✓ .env file created from template")
            print("  Please edit .env file with your Azure credentials")
        else:
            print("⚠ .env.example not found, please create .env manually")
    else:
        print("✓ .env file already exists")

def validate_environment():
    """Validate the setup"""
    print("Validating environment setup...")

    # Check if required files exist
    required_files = [
        "requirements.txt",
        ".env",
        "src/server/main.py"
    ]

    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)

    if missing_files:
        print(f"⚠ Missing required files: {', '.join(missing_files)}")
        return False

    print("✓ Environment validation passed")
    return True

def main():
    """Main setup function"""
    print("Setting up Work Item Documentation MCP Server...")
    print("=" * 50)

    setup_virtual_environment()
    install_dependencies()
    create_directories()
    create_config_files()

    if validate_environment():
        print("\n" + "=" * 50)
        print("✓ Setup completed successfully!")
        print("\nNext steps:")
        print("1. Edit .env file with your Azure credentials")
        print("2. Add your markdown files to data/work-items/")
        print("3. Run: python scripts/upload_documents.py")
        print("4. Start MCP server: python src/server/main.py")
    else:
        print("✗ Setup completed with warnings")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

### Configuration Validation Script (`scripts/validate_config.py`)

```python
#!/usr/bin/env python3
"""
Configuration validation script for Work Item Documentation MCP Server
"""
import os
import sys
from pathlib import Path
from openai import AzureOpenAI
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv

def check_environment_variables():
    """Check that all required environment variables are set"""
    print("Checking environment variables...")

    required_vars = [
        'AZURE_OPENAI_ENDPOINT',
        'AZURE_OPENAI_API_KEY',
        'AZURE_OPENAI_DEPLOYMENT_NAME',
        'AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME',
        'AZURE_SEARCH_SERVICE_NAME',
        'AZURE_SEARCH_ADMIN_KEY',
        'AZURE_SEARCH_INDEX_NAME'
    ]

    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        return False
    else:
        print("✅ All required environment variables are set")
        return True

def test_azure_openai_connection():
    """Test connection to Azure OpenAI"""
    print("Testing Azure OpenAI connection...")

    try:
        client = AzureOpenAI(
            azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT'),
            api_key=os.getenv('AZURE_OPENAI_API_KEY'),
            api_version="2024-02-01"
        )

        # Test embedding generation
        response = client.embeddings.create(
            input=["test"],
            model=os.getenv('AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME')
        )

        if response.data and len(response.data[0].embedding) > 0:
            print("✅ Azure OpenAI embedding API working")
            return True
        else:
            print("❌ Azure OpenAI embedding API returned empty response")
            return False

    except Exception as e:
        print(f"❌ Azure OpenAI connection failed: {e}")
        return False

def test_azure_search_connection():
    """Test connection to Azure Cognitive Search"""
    print("Testing Azure Cognitive Search connection...")

    try:
        search_client = SearchClient(
            endpoint=f"https://{os.getenv('AZURE_SEARCH_SERVICE_NAME')}.search.windows.net",
            index_name=os.getenv('AZURE_SEARCH_INDEX_NAME'),
            credential=AzureKeyCredential(os.getenv('AZURE_SEARCH_ADMIN_KEY'))
        )

        # Test basic search (this will work even if index is empty)
        results = search_client.search(search_text="*", top=1)
        result_list = list(results)

        print("✅ Azure Cognitive Search connection working")
        print(f"📊 Index contains {len(result_list)} documents (showing max 1)")

        return True

    except Exception as e:
        print(f"❌ Azure Cognitive Search connection failed: {e}")
        return False

def check_work_items_directory():
    """Check work items directory"""
    print("Checking work items directory")

    PERSONAL_DOCUMENTATION_ROOT_DIRECTORY = Path(os.getenv('PERSONAL_DOCUMENTATION_ROOT_DIRECTORY', './data/work-items'))

    if not PERSONAL_DOCUMENTATION_ROOT_DIRECTORY.exists():
        print(f"❌ Work items directory does not exist: {PERSONAL_DOCUMENTATION_ROOT_DIRECTORY}")
        return False

    md_files = list(PERSONAL_DOCUMENTATION_ROOT_DIRECTORY.rglob("*.md"))

    if not md_files:
        print(f"⚠️  No markdown files found in: {PERSONAL_DOCUMENTATION_ROOT_DIRECTORY}")
        print("Add some .md files to get started")
    else:
        print(f"✅ Found {len(md_files)} markdown files in work items directory")

    return True

def main():
    """Main validation function"""
    print("🔍 Validating Work Item Documentation MCP Server configuration...\n")

    # Load environment variables
    load_dotenv()

    all_checks_passed = True

    # Run all validation checks
    checks = [
        check_environment_variables,
        test_azure_openai_connection,
        test_azure_search_connection,
        check_work_items_directory
    ]

    for check in checks:
        try:
            result = check()
            if not result:
                all_checks_passed = False
        except Exception as e:
            print(f"❌ Check failed with exception: {e}")
            all_checks_passed = False
        print()  # Add spacing between checks

    if all_checks_passed:
        print("🎉 All validation checks passed! Your configuration is ready.")
    else:
        print("❌ Some validation checks failed. Please fix the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

### Development Commands (`scripts/dev.py`)

```python
#!/usr/bin/env python3
"""
Development helper commands
"""
import argparse
import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, cwd=None):
    """Run a command"""
    try:
        subprocess.run(cmd, shell=True, cwd=cwd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {cmd}")
        sys.exit(1)

def activate_venv():
    """Get the virtual environment activation command"""
    if os.name == 'nt':  # Windows
        return "venv\\Scripts\\activate && "
    else:  # Unix/Linux/Mac
        return "source venv/bin/activate && "

def run_tests():
    """Run tests"""
    print("Running tests...")
    cmd = f"{activate_venv()}python -m pytest tests/ -v"
    run_command(cmd)

def run_linting():
    """Run code linting"""
    print("Running linting...")
    cmd = f"{activate_venv()}flake8 src/ tests/"
    run_command(cmd)

def run_formatting():
    """Run code formatting"""
    print("Running code formatting...")
    cmd = f"{activate_venv()}black src/ tests/ scripts/"
    run_command(cmd)

def run_type_checking():
    """Run type checking"""
    print("Running type checking...")
    cmd = f"{activate_venv()}mypy src/"
    run_command(cmd)

def run_server():
    """Run the MCP server"""
    print("Starting MCP server...")
    cmd = f"{activate_venv()}python src/server/main.py"
    run_command(cmd)

def upload_documents():
    """Upload documents to Azure Cognitive Search"""
    print("Uploading documents...")
    cmd = f"{activate_venv()}python scripts/upload_documents.py"
    run_command(cmd)

def validate_setup():
    """Validate Azure setup"""
    print("Validating Azure setup...")
    cmd = f"{activate_venv()}python scripts/validate_azure_setup.py"
    run_command(cmd)

def main():
    parser = argparse.ArgumentParser(description="Development helper commands")
    parser.add_argument("command", choices=[
        "test", "lint", "format", "typecheck", "server", "upload", "validate", "all"
    ])

    args = parser.parse_args()

    if args.command == "test":
        run_tests()
    elif args.command == "lint":
        run_linting()
    elif args.command == "format":
        run_formatting()
    elif args.command == "typecheck":
        run_type_checking()
    elif args.command == "server":
        run_server()
    elif args.command == "upload":
        upload_documents()
    elif args.command == "validate":
        validate_setup()
    elif args.command == "all":
        run_formatting()
        run_linting()
        run_type_checking()
        run_tests()
        print("✓ All checks passed!")

if __name__ == "__main__":
    main()
```

## Docker Configuration (Optional)

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ src/
COPY config/ config/
COPY scripts/ scripts/

# Create data directory
RUN mkdir -p data/work-items

# Set environment variables
ENV PYTHONPATH=/app
ENV MCP_SERVER_PORT=3000

# Expose port
EXPOSE 3000

# Run the MCP server
CMD ["python", "src/server/main.py"]
```

### docker-compose.yml

```yaml
version: "3.8"

services:
  work-items-mcp:
    build: .
    ports:
      - "3000:3000"
    environment:
      - AZURE_OPENAI_ENDPOINT=${AZURE_OPENAI_ENDPOINT}
      - AZURE_OPENAI_API_KEY=${AZURE_OPENAI_API_KEY}
      - AZURE_OPENAI_DEPLOYMENT_NAME=${AZURE_OPENAI_DEPLOYMENT_NAME}
      - AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME=${AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME}
      - AZURE_SEARCH_SERVICE_NAME=${AZURE_SEARCH_SERVICE_NAME}
      - AZURE_SEARCH_ADMIN_KEY=${AZURE_SEARCH_ADMIN_KEY}
      - AZURE_SEARCH_INDEX_NAME=${AZURE_SEARCH_INDEX_NAME}
      - PERSONAL_DOCUMENTATION_ROOT_DIRECTORY=/app/data/work-items
      - LOG_LEVEL=INFO
    volumes:
      - ./data/work-items:/app/data/work-items:ro
      - ./logs:/app/logs
    restart: unless-stopped
```

## GitHub Actions CI/CD (Optional)

### .github/workflows/ci.yml

```yaml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run linting
        run: |
          flake8 src/ tests/

      - name: Run type checking
        run: |
          mypy src/

      - name: Run tests
        run: |
          pytest tests/ -v
```

## Quick Start Commands

```bash
# Initial setup
python scripts/setup.py

# Activate virtual environment (Windows)
venv\Scripts\activate

# Activate virtual environment (Unix/Linux/Mac)
source venv/bin/activate

# Run development commands
python scripts/dev.py format  # Format code
python scripts/dev.py lint    # Run linting
python scripts/dev.py test    # Run tests
python scripts/dev.py upload  # Upload documents
python scripts/dev.py server  # Start MCP server

# Or run all checks
python scripts/dev.py all
```
