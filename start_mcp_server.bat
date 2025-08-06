@echo off
REM Work Item Documentation MCP Server Startup Script
REM This script activates the virtual environment and starts the MCP server

echo 🚀 Starting Work Item Documentation MCP Server...

REM Change to project directory
cd /d "%~dp0"

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo ❌ Virtual environment not found!
    echo Please run: python -m venv venv
    echo Then run: venv\Scripts\activate
    echo Then run: pip install -r requirements.txt
    pause
    exit /b 1
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate

REM Check if .env file exists
if not exist ".env" (
    echo ❌ .env file not found!
    echo Please copy .env.example to .env and configure your Azure credentials
    pause
    exit /b 1
)

REM Start MCP server
echo 🎯 Starting MCP server...
python mcp_server.py

REM Keep window open on error
if errorlevel 1 (
    echo ❌ MCP server failed to start
    pause
)
