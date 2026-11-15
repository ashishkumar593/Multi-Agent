"""Tests for security guardrails (SSRF and path traversal)."""
from pathlib import Path
import pytest
from backend.core.exceptions import SecurityError
from backend.core.security import validate_safe_path, validate_safe_url

def test_ssrf_blocking_localhost():
    with pytest.raises(SecurityError, match="SSRF blocked"):
        validate_safe_url("http://127.0.0.1/admin")

    with pytest.raises(SecurityError, match="SSRF blocked"):
        validate_safe_url("http://localhost:8000/secret")

def test_safe_public_url():
    # Test valid public domain
    assert validate_safe_url("https://example.com") is True

def test_path_traversal_prevention(tmp_path: Path):
    base_dir = tmp_path / "sandbox"
    base_dir.mkdir()
    traversal_path = base_dir / ".." / "outside.txt"

    with pytest.raises(SecurityError, match="Path traversal detected"):
        validate_safe_path(base_dir, traversal_path)
