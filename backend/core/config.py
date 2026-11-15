"""Centralized application settings."""
from pathlib import Path
from typing import Literal

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
except ImportError:  # shortcut: fallback if pydantic-settings not yet installed, use pydantic BaseModel
    from pydantic import BaseModel as BaseSettings  # type: ignore
    SettingsConfigDict = dict  # type: ignore

class Settings(BaseSettings):
    """Runtime configuration loaded from environment or .env file."""
    app_env: Literal["development", "testing", "production"] = "development"
    app_name: str = "AI Research & Report Agent"
    debug: bool = True
    api_prefix: str = "/api/v1"

    # LLM Settings
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    default_model: str = "gpt-4o"
    fast_model: str = "gpt-4o-mini"
    embedding_model: str = "text-embedding-3-small"

    # Search & Tool Settings
    tavily_api_key: str = ""

    # Storage Paths
    chroma_persist_dir: Path = Path("./data/chroma")
    database_url: str = "sqlite:///./data/app.db"
    redis_url: str = "redis://localhost:6379/0"

    # RAG Hyperparameters
    chunk_size: int = 800
    chunk_overlap: int = 100
    max_upload_size_mb: int = 25

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    ) if hasattr(BaseSettings, "model_config") else {}

settings = Settings()
