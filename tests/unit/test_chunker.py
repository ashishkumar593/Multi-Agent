"""Tests for recursive chunker."""
from src.backend.rag.chunker import RecursiveChunker
from src.backend.rag.loaders import DocumentChunk

def test_chunker_splitting():
    chunker = RecursiveChunker(target_chunk_tokens=50, overlap_tokens=10)
    long_text = "Paragraph one with important insights.\n\n" * 15
    parent = DocumentChunk(
        chunk_id="doc1_p1_c0",
        doc_id="doc1",
        content=long_text,
        page_number=1,
    )
    results = chunker.split_chunks([parent])
    assert len(results) > 1
    for c in results:
        assert c.doc_id == "doc1"
        assert c.page_number == 1
        assert len(c.content) <= chunker.chunk_size
