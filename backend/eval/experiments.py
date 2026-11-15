"""Empirical retrieval experiments testing chunk sizes, dense, sparse, and reranking."""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

# Safeguard sys.path for direct execution
_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from typing import Any, Dict, List
from backend.rag.bm25 import BM25Retriever
from backend.rag.loaders import DocumentChunk
from backend.rag.chunker import RecursiveChunker
from backend.rag.reranker import CrossEncoderReranker
from backend.rag.retriever import HybridRetriever
from backend.rag.store import VectorStore


SAMPLE_CORPUS = [
    "Artificial intelligence in software development enhances productivity by automating code generation and unit testing.",
    "Recent studies show a 26% to 55% reduction in coding task duration when engineers use generative AI coding assistants.",
    "Junior developer hiring has seen a 15% reduction in entry-level openings due to automation of routine boilerplate tasks.",
    "Prompt engineering and system architecture have emerged as mission-critical competencies for modern software engineering.",
    "Enterprise AI adoption faces major challenges including code privacy, hallucinations, licensing compliance, and security vulnerabilities.",
    "Multi-agent AI frameworks enable autonomous task decomposition, parallel execution, and self-correcting validation loops.",
    "Retrieval-Augmented Generation (RAG) combines semantic vector search with lexical BM25 retrieval to ground LLM generations.",
    "Cross-Encoder reranking scores full query-document pairs together, significantly outperforming dual-encoder bi-encoder ranking alone.",
    "Vector databases like ChromaDB persist dense document embeddings and provide fast approximate nearest neighbor lookups.",
    "Deterministic citation verification programmatically matches claims to unique evidence identifiers preventing hallucinations.",
]

TEST_QUERIES = [
    "How does generative AI impact software engineering productivity and junior hiring?",
    "What are the benefits of cross-encoder reranking over vector search?",
    "What challenges do enterprises face when adopting AI coding assistants?",
    "Explain how multi-agent architectures and RAG prevent hallucinations.",
]


def run_retrieval_experiment() -> Dict[str, Any]:
    """Execute grid-comparison of retrieval configurations."""
    print("\n=== Running Empirical Retrieval Experiments ===")
    
    # 1. Chunking Experiment
    chunkers = {
        "500_tokens": RecursiveChunker(target_chunk_tokens=500, overlap_tokens=50),
        "800_tokens": RecursiveChunker(target_chunk_tokens=800, overlap_tokens=80),
        "1200_tokens": RecursiveChunker(target_chunk_tokens=1200, overlap_tokens=120),
    }
    
    print("\n[Phase 1: Chunking Latency & Token Splits]")
    full_text = " ".join(SAMPLE_CORPUS * 5)
    sample_parent = [
        DocumentChunk(
            chunk_id="parent_001",
            doc_id="sample_doc",
            content=full_text,
            page_number=1,
            chunk_index=0,
            metadata={"source": "benchmark"},
        )
    ]
    for name, chunker in chunkers.items():
        t0 = time.perf_counter()
        chunks = chunker.split_chunks(sample_parent)
        dt = (time.perf_counter() - t0) * 1000
        print(f"  - Config {name}: produced {len(chunks)} chunks in {dt:.3f}ms")

    # 2. Retrieval Comparison
    doc_chunks = [
        DocumentChunk(
            chunk_id=f"chk_{i:03d}",
            doc_id=f"doc_{i:02d}",
            content=text,
            page_number=1,
            chunk_index=i,
            metadata={"source": f"doc_{i:02d}.txt"},
        )
        for i, text in enumerate(SAMPLE_CORPUS)
    ]
    
    store = VectorStore(collection_name="eval_experiment_test")
    store.add_chunks(doc_chunks)
    
    bm25 = BM25Retriever()
    bm25.index(doc_chunks)
    
    reranker = CrossEncoderReranker()
    hybrid = HybridRetriever(vector_store=store, bm25_retriever=bm25, reranker=reranker)
    
    print("\n[Phase 2: Retrieval Mode Comparison (Hits & Latency)]")
    for query in TEST_QUERIES:
        print(f"\nQuery: '{query[:50]}...'")
        
        # Dense only
        t0 = time.perf_counter()
        dense_hits = store.similarity_search(query, top_k=3)
        dt_dense = (time.perf_counter() - t0) * 1000
        print(f"  - [Dense Only]          Hits: {len(dense_hits)} | Latency: {dt_dense:.2f}ms")
        
        # BM25 only
        t0 = time.perf_counter()
        bm25_hits = bm25.search(query, top_k=3)
        dt_bm25 = (time.perf_counter() - t0) * 1000
        print(f"  - [BM25 Only]           Hits: {len(bm25_hits)} | Latency: {dt_bm25:.2f}ms")
        
        # Hybrid RRF + Reranker
        t0 = time.perf_counter()
        hybrid_hits = hybrid.retrieve(query, top_k=3)
        dt_hybrid = (time.perf_counter() - t0) * 1000
        print(f"  - [Hybrid RRF + Rerank]  Hits: {len(hybrid_hits)} | Latency: {dt_hybrid:.2f}ms")
        
    print("\n=== Experiments Completed Successfully ===")
    return {"status": "success", "queries_tested": len(TEST_QUERIES)}


if __name__ == "__main__":
    run_retrieval_experiment()
