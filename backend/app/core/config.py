import os
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # General configuration
    PROJECT_NAME: str = "AI Knowledge Assistant API"
    ENVIRONMENT: str = Field(default="development")
    DEBUG: bool = Field(default=False)
    PORT: int = Field(default=8000)
    CORS_ORIGINS: List[str] = Field(default=["http://localhost:3000"])

    # OpenAI configuration
    OPENAI_API_KEY: str = Field(default="")
    OPENAI_BASE_URL: str = Field(default="")
    OPENAI_MODEL: str = Field(default="gpt-4o-mini")
    OPENAI_EMBEDDING_MODEL: str = Field(default="text-embedding-3-small")

    # Supabase configuration
    SUPABASE_URL: str = Field(default="")
    SUPABASE_ANON_KEY: str = Field(default="")
    SUPABASE_SERVICE_ROLE_KEY: str = Field(default="")
    SUPABASE_JWT_SECRET: str = Field(default="")

    # MCP configuration
    MCP_SERVER_PATH: str = Field(default="mcp-server/mcp_server.py")

settings = Settings()
