"""Integration tests for hybrid retrieval and RRF scoring."""
from backend.rag.bm25 import BM25Retriever
from backend.rag.loaders import DocumentChunk
from backend.rag.retriever import HybridRetriever
from backend.rag.store import VectorStore

def test_hybrid_retriever_ranking():
    store = VectorStore()
    bm25 = BM25Retriever()
    hybrid = HybridRetriever(vector_store=store, bm25_retriever=bm25)

    chunks = [
        DocumentChunk(chunk_id="c1", doc_id="d1", content="Transformer architectures rely on multi-head self-attention mechanisms."),
        DocumentChunk(chunk_id="c2", doc_id="d2", content="Gradient descent optimizes loss functions in neural networks."),
    ]
    hybrid.index_documents(chunks)

    results = hybrid.retrieve("multi-head attention", top_k=1)
    assert len(results) == 1
    assert results[0][0].chunk_id == "c1"
