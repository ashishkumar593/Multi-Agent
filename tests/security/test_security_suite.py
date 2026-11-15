"""Adversarial security test suite."""
from pathlib import Path
import pytest
from src.backend.core.exceptions import SecurityError
from src.backend.core.security import validate_safe_path, validate_safe_url

def test_security_suite_ssrf_localhost():
    with pytest.raises(SecurityError, match="SSRF blocked"):
        validate_safe_url("http://127.0.0.1:8080/admin")

    with pytest.raises(SecurityError, match="SSRF blocked"):
        validate_safe_url("http://localhost:3000")

def test_security_suite_path_traversal(tmp_path: Path):
    base_dir = tmp_path / "sandbox"
    base_dir.mkdir()
    attack_path = base_dir / ".." / "etc" / "passwd"

    with pytest.raises(SecurityError, match="Path traversal detected"):
        validate_safe_path(base_dir, attack_path)
