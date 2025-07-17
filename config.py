import os
from typing import Optional
from pydantic import BaseSettings


class Settings(BaseSettings):
    # LLM Configuration
    local_llm_url: str = "http://localhost:11434"
    local_llm_model: str = "llama2"
    
    # GitLab Configuration
    gitlab_url: Optional[str] = None
    gitlab_token: Optional[str] = None
    
    # MCP Configuration
    mcp_server_url: str = "ws://localhost:3000"
    
    # Database Configuration
    database_url: str = "sqlite:///./agents.db"
    
    # Web Interface Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Agent Configuration
    max_context_length: int = 4096
    max_agents: int = 10
    
    class Config:
        env_file = ".env"


settings = Settings()