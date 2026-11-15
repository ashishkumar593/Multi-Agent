"""Repository for documents."""
from typing import Any
from src.backend.db.models.document import DocumentModel

class DocumentRepository:
    """Handles persistence for uploaded and indexed documents."""

    def __init__(self, session: Any = None):
        self.session = session
        self._memory_docs: dict[str, dict[str, Any]] = {}

    def save(self, doc_id: str, filename: str, file_hash: str, chunks_count: int, size_bytes: int) -> dict[str, Any]:
        record = {
            "id": doc_id,
            "filename": filename,
            "file_hash": file_hash,
            "chunks_count": chunks_count,
            "size_bytes": size_bytes,
        }
        if self.session:
            try:
                db_doc = DocumentModel(
                    id=doc_id,
                    filename=filename,
                    file_hash=file_hash,
                    chunks_count=chunks_count,
                    size_bytes=size_bytes,
                )
                self.session.add(db_doc)
                self.session.commit()
            except Exception:
                pass
        self._memory_docs[doc_id] = record
        return record

    def list_all(self) -> list[dict[str, Any]]:
        return list(self._memory_docs.values())
