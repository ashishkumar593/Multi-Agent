"""Document management service."""
from pathlib import Path
from typing import Any
from backend.core.config import settings
from backend.db.repositories.document_repo import DocumentRepository
from backend.rag.chunker import RecursiveChunker
from backend.rag.loaders import DocumentLoader, compute_file_hash
from backend.rag.retriever import HybridRetriever

class DocumentService:
    """Manages document uploads, chunking, indexing, and metadata persistence."""

    def __init__(self, retriever: HybridRetriever, repository: DocumentRepository | None = None):
        self.retriever = retriever
        self.repository = repository or DocumentRepository()
        self.chunker = RecursiveChunker(target_chunk_tokens=settings.chunk_size, overlap_tokens=settings.chunk_overlap)

    def process_file(self, file_path: Path) -> dict[str, Any]:
        """Ingest a single file, chunk, index into Hybrid RAG, and record in DB."""
        raw_chunks = DocumentLoader.load(file_path)
        split_chunks = self.chunker.split_chunks(raw_chunks)
        self.retriever.index_documents(split_chunks)

        file_hash = compute_file_hash(file_path)
        doc_id = raw_chunks[0].doc_id if raw_chunks else f"doc_{file_hash[:16]}"
        size_bytes = file_path.stat().st_size

        return self.repository.save(
            doc_id=doc_id,
            filename=file_path.name,
            file_hash=file_hash,
            chunks_count=len(split_chunks),
            size_bytes=size_bytes,
        )

    def list_documents(self) -> list[dict[str, Any]]:
        return self.repository.list_all()
