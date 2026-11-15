"""Batch document ingestion pipeline."""
import time
from dataclasses import dataclass, field
from pathlib import Path

from src.backend.core.config import settings
from src.backend.core.logging import logger
from src.backend.rag.chunker import RecursiveChunker
from src.backend.rag.loaders import DocumentChunk, DocumentLoader
from src.backend.rag.retriever import HybridRetriever

@dataclass
class IngestionSummary:
    total_files: int = 0
    successful_files: int = 0
    failed_files: int = 0
    total_chunks: int = 0
    elapsed_seconds: float = 0.0
    errors: list[str] = field(default_factory=list)

class DocumentIngestionPipeline:
    """Processes directories of documents, chunks them, and indexes into hybrid store."""

    def __init__(self, retriever: HybridRetriever, chunk_size: int | None = None, chunk_overlap: int | None = None):
        self.retriever = retriever
        self.chunker = RecursiveChunker(
            target_chunk_tokens=chunk_size or settings.chunk_size,
            overlap_tokens=chunk_overlap or settings.chunk_overlap,
        )

    def ingest_directory(self, directory: Path) -> IngestionSummary:
        """Scan directory and ingest all supported document files."""
        start_time = time.perf_counter()
        summary = IngestionSummary()

        if not directory.exists() or not directory.is_dir():
            summary.errors.append(f"Directory not found: {directory}")
            return summary

        supported_suffixes = {".pdf", ".docx", ".txt", ".md"}
        files = [p for p in directory.rglob("*") if p.is_file() and p.suffix.lower() in supported_suffixes]
        summary.total_files = len(files)

        all_chunks: list[DocumentChunk] = []
        for file_path in files:
            try:
                raw_chunks = DocumentLoader.load(file_path)
                split_chunks = self.chunker.split_chunks(raw_chunks)
                all_chunks.extend(split_chunks)
                summary.successful_files += 1
                logger.info(f"Ingested {file_path.name}: {len(split_chunks)} chunks created.")
            except Exception as e:
                summary.failed_files += 1
                err_msg = f"Failed to ingest {file_path.name}: {e}"
                summary.errors.append(err_msg)
                logger.error(err_msg)

        if all_chunks:
            self.retriever.index_documents(all_chunks)
            summary.total_chunks = len(all_chunks)

        summary.elapsed_seconds = time.perf_counter() - start_time
        return summary
