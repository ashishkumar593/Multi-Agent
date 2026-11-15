"""Persistent vector storage with ChromaDB and in-memory cosine fallback."""
from pathlib import Path
from typing import Any

from src.backend.core.config import settings
from src.backend.rag.embeddings import BaseEmbeddingProvider, OpenAIEmbeddingProvider
from src.backend.rag.loaders import DocumentChunk

class VectorStore:
    """Vector database interface with ChromaDB persistence and in-memory fallback."""

    def __init__(
        self,
        persist_dir: Path | None = None,
        collection_name: str = "research_documents",
        embedding_provider: BaseEmbeddingProvider | None = None,
    ):
        self.persist_dir = persist_dir or settings.chroma_persist_dir
        self.collection_name = collection_name
        self.embedding_provider = embedding_provider or OpenAIEmbeddingProvider()
        self.client = None
        self.collection = None
        # In-memory storage fallback
        self._memory_chunks: dict[str, DocumentChunk] = {}
        self._memory_embeddings: dict[str, list[float]] = {}

        self._init_chroma()

    def _init_chroma(self) -> None:
        try:
            import chromadb
            self.persist_dir.mkdir(parents=True, exist_ok=True)
            self.client = chromadb.PersistentClient(path=str(self.persist_dir))
            self.collection = self.client.get_or_create_collection(name=self.collection_name)
        except Exception:
            # shortcut: in-memory store fallback when chromadb fails or in isolated tests
            self.client = None
            self.collection = None

    def add_chunks(self, chunks: list[DocumentChunk]) -> int:
        """Add or update chunks in vector store. Returns count of chunks stored."""
        if not chunks:
            return 0

        # Deduplicate incoming chunks by chunk_id
        unique_chunks = {c.chunk_id: c for c in chunks}
        chunk_list = list(unique_chunks.values())
        texts = [c.content for c in chunk_list]
        embeddings = self.embedding_provider.embed_texts(texts)

        if self.collection is not None:
            try:
                self.collection.upsert(
                    ids=[c.chunk_id for c in chunk_list],
                    documents=texts,
                    embeddings=embeddings,
                    metadatas=[
                        {
                            "doc_id": c.doc_id,
                            "page_number": c.page_number,
                            "chunk_index": c.chunk_index,
                            **{k: str(v) for k, v in c.metadata.items() if isinstance(v, (str, int, float, bool))},
                        }
                        for c in chunk_list
                    ],
                )
                return len(chunk_list)
            except Exception:
                pass

        # In-memory fallback
        for chunk, emb in zip(chunk_list, embeddings):
            self._memory_chunks[chunk.chunk_id] = chunk
            self._memory_embeddings[chunk.chunk_id] = emb

        return len(chunk_list)

    def similarity_search(self, query: str, top_k: int = 5) -> list[tuple[DocumentChunk, float]]:
        """Return top_k chunks most similar to query with cosine similarity scores."""
        query_emb = self.embedding_provider.embed_query(query)

        if self.collection is not None:
            try:
                results = self.collection.query(
                    query_embeddings=[query_emb],
                    n_results=top_k,
                    include=["documents", "metadatas", "distances"],
                )
                matched: list[tuple[DocumentChunk, float]] = []
                if results and results["ids"] and results["ids"][0]:
                    for idx, chunk_id in enumerate(results["ids"][0]):
                        doc_text = results["documents"][0][idx] if results["documents"] else ""
                        meta = results["metadatas"][0][idx] if results["metadatas"] else {}
                        dist = results["distances"][0][idx] if results["distances"] else 1.0
                        score = max(0.0, 1.0 - (dist / 2.0))  # Convert cosine distance to similarity
                        chunk = DocumentChunk(
                            chunk_id=chunk_id,
                            doc_id=str(meta.get("doc_id", "")),
                            content=doc_text,
                            page_number=int(meta.get("page_number", 1)),
                            chunk_index=int(meta.get("chunk_index", 0)),
                            metadata=dict(meta),
                        )
                        matched.append((chunk, score))
                return matched
            except Exception:
                pass

        # In-memory similarity computation
        scored: list[tuple[DocumentChunk, float]] = []
        for chunk_id, emb in self._memory_embeddings.items():
            # Dot product for cosine similarity (assumes unit normalized vectors)
            dot = sum(a * b for a, b in zip(query_emb, emb))
            scored.append((self._memory_chunks[chunk_id], max(0.0, dot)))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

    def delete_by_doc_id(self, doc_id: str) -> None:
        """Remove all chunks associated with doc_id."""
        if self.collection is not None:
            try:
                self.collection.delete(where={"doc_id": doc_id})
            except Exception:
                pass

        keys_to_del = [cid for cid, chunk in self._memory_chunks.items() if chunk.doc_id == doc_id]
        for k in keys_to_del:
            self._memory_chunks.pop(k, None)
            self._memory_embeddings.pop(k, None)
