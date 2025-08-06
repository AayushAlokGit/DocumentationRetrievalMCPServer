#!/usr/bin/env python3
"""
Work Item Documentation MCP Server Entry Point
==============================================

Entry point for the Model Context Protocol server that provides search capabilities
for Work Item documentation stored in Azure Cognitive Search.
"""

import sys
from pathlib import Path

# ONE simple line to fix all imports - find project root and add src
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'src'))

# Import and run our MCP server (renamed to avoid conflicts)
from workitem_mcp.server import main

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
