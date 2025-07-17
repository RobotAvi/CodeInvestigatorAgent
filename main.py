#!/usr/bin/env python3
"""
Architecture Agent - Main Application Entry Point

This is the main entry point for the Architecture Agent application.
It provides a comprehensive solution for analyzing microservice architectures,
generating C4 diagrams, and helping with feature planning.
"""

import asyncio
import uvicorn
from web_interface import app
from config import settings
from llm_client import LocalLLMClient
from gitlab_client import gitlab_client


async def check_dependencies():
    """Check if all dependencies are available"""
    print("Checking dependencies...")
    
    # Check LLM availability
    llm_client = LocalLLMClient()
    if llm_client.is_available():
        models = llm_client.get_models()
        print(f"✅ Local LLM available. Models: {models}")
    else:
        print("⚠️  Local LLM not available. Please ensure Ollama is running.")
    
    # Check MCP server
    try:
        await gitlab_client.connect()
        print("✅ MCP server connection successful")
        await gitlab_client.disconnect()
    except Exception as e:
        print(f"⚠️  MCP server connection failed: {e}")
    
    print("Dependency check complete.\n")


def print_startup_info():
    """Print startup information"""
    print("=" * 60)
    print("🏗️  Architecture Agent")
    print("=" * 60)
    print(f"Version: 1.0.0")
    print(f"Host: {settings.host}")
    print(f"Port: {settings.port}")
    print(f"Local LLM URL: {settings.local_llm_url}")
    print(f"MCP Server URL: {settings.mcp_server_url}")
    print("=" * 60)
    print()


def main():
    """Main application entry point"""
    print_startup_info()
    
    # Check dependencies
    asyncio.run(check_dependencies())
    
    # Start the web server
    print("Starting Architecture Agent...")
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        log_level="info"
    )


if __name__ == "__main__":
    main()