"""Tests for configuration settings."""
from src.backend.core.config import Settings

def test_default_settings():
    settings = Settings()
    assert settings.app_name == "AI Research & Report Agent"
    assert settings.chunk_size == 800
    assert settings.chunk_overlap == 100
    assert settings.debug is True
