"""Tests for BM25 lexical retrieval."""
from backend.rag.bm25 import BM25Retriever
from backend.rag.loaders import DocumentChunk

def test_bm25_retrieval():
    chunks = [
        DocumentChunk(chunk_id="c1", doc_id="d1", content="Quantum computing uses qubits and superposition."),
        DocumentChunk(chunk_id="c2", doc_id="d2", content="Generative AI models leverage transformers and self-attention."),
        DocumentChunk(chunk_id="c3", doc_id="d3", content="PostgreSQL is an ACID compliant relational database."),
    ]
    bm25 = BM25Retriever()
    bm25.index(chunks)

    results = bm25.search("transformers attention", top_k=2)
    assert len(results) > 0
    assert results[0].chunk.chunk_id == "c2"
