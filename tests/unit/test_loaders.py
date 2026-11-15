"""Tests for document loaders."""
from pathlib import Path
from src.backend.rag.loaders import DocumentLoader

def test_load_text_file(sample_text_file: Path):
    chunks = DocumentLoader.load(sample_text_file)
    assert len(chunks) >= 1
    assert "Generative AI" in chunks[0].content
    assert chunks[0].metadata["filename"] == "sample_research.txt"
    assert chunks[0].page_number == 1
