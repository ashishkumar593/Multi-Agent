"""Retrieval benchmark comparing dense, BM25, and hybrid search."""
import sys
import time
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.rag.bm25 import BM25Retriever
from backend.rag.loaders import DocumentChunk
from backend.rag.retriever import HybridRetriever
from backend.rag.store import VectorStore

def main():
    print("\n--- Running Retrieval Engine Benchmark ---")

    # Sample corpus
    sample_corpus = [
        DocumentChunk(chunk_id="c1", doc_id="d1", content="Generative AI significantly impacts software engineering velocity by 30%."),
        DocumentChunk(chunk_id="c2", doc_id="d2", content="PostgreSQL ACID compliance and relational schema integrity."),
        DocumentChunk(chunk_id="c3", doc_id="d3", content="Neural cross-encoders rerank passage candidates via deep attention."),
        DocumentChunk(chunk_id="c4", doc_id="d4", content="BM25 sparse lexical retrieval targets exact acronyms and keywords."),
    ]

    vs = VectorStore()
    bm25 = BM25Retriever()
    hybrid = HybridRetriever(vector_store=vs, bm25_retriever=bm25)
    hybrid.index_documents(sample_corpus)

    test_queries = [
        "software engineering velocity",
        "cross-encoders rerank attention",
        "PostgreSQL relational",
        "sparse lexical retrieval",
    ]

    for q in test_queries:
        t0 = time.perf_counter()
        results = hybrid.retrieve(query=q, top_k=2)
        elapsed_ms = (time.perf_counter() - t0) * 1000
        top_match = results[0][0].chunk_id if results else "None"
        print(f"Query: '{q[:28]:<28}' -> Top Match: {top_match} ({elapsed_ms:.2f}ms)")

    print("\n✅ Benchmark completed successfully.\n")

if __name__ == "__main__":
    main()
