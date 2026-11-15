"""Recursive token-aware chunker for document normalization."""
import re
from typing import Any
from src.backend.rag.loaders import DocumentChunk

class RecursiveChunker:
    """Splits document text along natural boundaries with token-aware chunking."""

    def __init__(self, target_chunk_tokens: int = 800, overlap_tokens: int = 100):
        # shortcut: 1 token approx 4 characters for rapid English/code token estimation, upgrade to tiktoken when precise budget needed
        self.chunk_size = target_chunk_tokens * 4
        self.overlap = overlap_tokens * 4
        self.separators = ["\n\n", "\n", ". ", " "]

    def split_chunks(self, parent_chunks: list[DocumentChunk]) -> list[DocumentChunk]:
        """Split a list of loaded page chunks into uniform chunks with overlap."""
        split_results: list[DocumentChunk] = []

        for parent in parent_chunks:
            text = parent.content
            if len(text) <= self.chunk_size:
                split_results.append(parent)
                continue

            sub_texts = self._recursive_split(text, self.separators)
            for idx, sub_text in enumerate(sub_texts):
                chunk_id = f"{parent.doc_id}_p{parent.page_number}_c{idx}"
                metadata: dict[str, Any] = {
                    **parent.metadata,
                    "parent_doc_id": parent.doc_id,
                    "page_number": parent.page_number,
                    "chunk_index": idx,
                    "char_length": len(sub_text),
                }
                split_results.append(
                    DocumentChunk(
                        chunk_id=chunk_id,
                        doc_id=parent.doc_id,
                        content=sub_text,
                        page_number=parent.page_number,
                        chunk_index=idx,
                        metadata=metadata,
                    )
                )

        return split_results

    def _recursive_split(self, text: str, separators: list[str]) -> list[str]:
        if not separators or len(text) <= self.chunk_size:
            return [text.strip()] if text.strip() else []

        sep = separators[0]
        remaining_seps = separators[1:]
        parts = text.split(sep)

        chunks: list[str] = []
        current = ""

        for part in parts:
            candidate = f"{current}{sep}{part}" if current else part
            if len(candidate) <= self.chunk_size:
                current = candidate
            else:
                if current:
                    chunks.append(current.strip())
                if len(part) > self.chunk_size and remaining_seps:
                    chunks.extend(self._recursive_split(part, remaining_seps))
                    current = ""
                else:
                    current = part

        if current and current.strip():
            chunks.append(current.strip())

        return chunks
