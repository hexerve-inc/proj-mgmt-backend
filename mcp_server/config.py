import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional

BASE_DIR = Path(__file__).resolve().parent

class MCPSettings(BaseSettings):
    # API Backend URL
    PMTOOL_API_BASE_URL: str
    PMTOOL_API_TOKEN: str = ""
    
    # MCP Server Identity Settings
    MCP_NAME: str = "PMTool"
    MCP_INSTRUCTIONS: str = "You are connected to the PMTool. You can manage projects, tasks, sprints, time entries, etc."

    # MCP Server Network Settings
    PORT: int = 8001
    MCP_HOST: str = "0.0.0.0"
    MCP_TRANSPORT: str = "sse"
    MCP_AUTH_PROVIDER: str = "none"

    
    # OAuth 2.1 PKCE Settings (for remote deployment)
    OAUTH_AUTHORIZATION_URL: Optional[str] = None
    OAUTH_TOKEN_URL: Optional[str] = None
    OAUTH_CLIENT_ID: Optional[str] = None

    class Config:
        env_file = str(BASE_DIR / ".env")
        extra = "ignore" # Ignore extra fields from other .env files (like the backend's)

mcp_settings = MCPSettings()
