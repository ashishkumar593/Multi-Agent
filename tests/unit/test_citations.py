"""Tests for citation registry and validation."""
from src.backend.rag.citations import CitationRegistry

def test_citation_registration_and_validation():
    registry = CitationRegistry()
    idx1 = registry.register_source("src_1", "Study A", "https://arxiv.org/abs/1")
    idx2 = registry.register_source("src_2", "Report B", "https://reuters.com/2")

    assert idx1 == 1
    assert idx2 == 2

    # Valid citation
    text_valid = "According to recent data [1], productivity jumped significantly [2]."
    is_valid, valid, invalid = registry.validate_citations(text_valid)
    assert is_valid is True
    assert valid == [1, 2]
    assert invalid == []

    # Invalid citation ([99] does not exist)
    text_invalid = "Unverified claim asserts something else [99]."
    is_valid2, valid2, invalid2 = registry.validate_citations(text_invalid)
    assert is_valid2 is False
    assert invalid2 == [99]
