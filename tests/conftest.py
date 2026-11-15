"""Pytest configuration and shared fixtures."""
import pytest
from pathlib import Path

@pytest.fixture
def sample_text_file(tmp_path: Path) -> Path:
    """Create a temporary text file with sample research content."""
    file = tmp_path / "sample_research.txt"
    file.write_text(
        "Generative AI has fundamentally shifted software development workflows between 2023 and 2026.\n\n"
        "Developer productivity measured via Pull Request velocity increased by an estimated 25% to 35%.\n\n"
        "However, code review overhead and security remediation workloads also climbed by 18% during the same observation period.",
        encoding="utf-8",
    )
    return file
