"""Hybrid retrieval engine combining BM25 lexical and dense vector search via RRF."""
from backend.rag.bm25 import BM25Retriever
from backend.rag.loaders import DocumentChunk
from backend.rag.reranker import CrossEncoderReranker
from backend.rag.store import VectorStore

class HybridRetriever:
    """Fuses dense semantic search and BM25 lexical search with neural reranking."""

    def __init__(
        self,
        vector_store: VectorStore,
        bm25_retriever: BM25Retriever | None = None,
        reranker: CrossEncoderReranker | None = None,
        rrf_k: int = 60,
    ):
        self.vector_store = vector_store
        self.bm25 = bm25_retriever or BM25Retriever()
        self.reranker = reranker or CrossEncoderReranker()
        self.rrf_k = rrf_k

    def index_documents(self, chunks: list[DocumentChunk]) -> None:
        """Index chunks into both dense vector store and sparse BM25."""
        self.vector_store.add_chunks(chunks)
        self.bm25.index(chunks)

    def retrieve(
        self, query: str, top_k: int = 5, candidate_pool: int = 20
    ) -> list[tuple[DocumentChunk, float]]:
        """Execute hybrid search: dense + sparse -> RRF -> Cross-Encoder rerank."""
        # 1. Dense vector search
        dense_results = self.vector_store.similarity_search(query, top_k=candidate_pool)

        # 2. Sparse BM25 search
        bm25_scored = self.bm25.search(query, top_k=candidate_pool)
        sparse_results = [(s.chunk, s.score) for s in bm25_scored]

        # 3. Reciprocal Rank Fusion (RRF)
        chunk_map: dict[str, DocumentChunk] = {}
        rrf_scores: dict[str, float] = {}

        for rank, (chunk, _) in enumerate(dense_results, start=1):
            chunk_map[chunk.chunk_id] = chunk
            rrf_scores[chunk.chunk_id] = rrf_scores.get(chunk.chunk_id, 0.0) + (1.0 / (self.rrf_k + rank))

        for rank, (chunk, _) in enumerate(sparse_results, start=1):
            chunk_map[chunk.chunk_id] = chunk
            rrf_scores[chunk.chunk_id] = rrf_scores.get(chunk.chunk_id, 0.0) + (1.0 / (self.rrf_k + rank))

        # 4. Neural reranking over candidate pool
        merged_candidates = [(chunk_map[cid], score) for cid, score in rrf_scores.items()]
        reranked = self.reranker.rerank(query, merged_candidates, top_n=top_k)
        return reranked
