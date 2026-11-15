"""FastAPI dependency injection utilities."""
from typing import Generator
from src.backend.core.config import settings

def get_settings():
    """Dependency provider for application settings."""
    return settings
