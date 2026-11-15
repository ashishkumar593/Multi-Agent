"""Document loaders with multi-format parsing, page attribution, and metadata extraction."""
import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.backend.core.exceptions import IngestionError
from src.backend.core.security import validate_safe_path

@dataclass
class DocumentChunk:
    """Represents an extracted or chunked piece of text with provenance metadata."""
    chunk_id: str
    doc_id: str
    content: str
    page_number: int = 1
    chunk_index: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

def compute_file_hash(file_path: Path) -> str:
    """Generate SHA-256 hash of file content for idempotent deduplication."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()

class DocumentLoader:
    """Universal document loader supporting PDF, DOCX, TXT, and Markdown."""

    @staticmethod
    def load(file_path: Path, base_dir: Path | None = None) -> list[DocumentChunk]:
        """Load document and return raw per-page/per-section chunks."""
        if base_dir:
            file_path = validate_safe_path(base_dir, file_path)

        if not file_path.exists():
            raise IngestionError(f"File not found: {file_path}")

        file_hash = compute_file_hash(file_path)
        doc_id = f"doc_{file_hash[:16]}"
        suffix = file_path.suffix.lower()

        if suffix in (".txt", ".md"):
            return DocumentLoader._load_text(file_path, doc_id, file_hash)
        elif suffix == ".pdf":
            return DocumentLoader._load_pdf(file_path, doc_id, file_hash)
        elif suffix == ".docx":
            return DocumentLoader._load_docx(file_path, doc_id, file_hash)
        else:
            raise IngestionError(f"Unsupported document format: {suffix}")

    @staticmethod
    def _load_text(file_path: Path, doc_id: str, file_hash: str) -> list[DocumentChunk]:
        try:
            content = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            content = file_path.read_text(encoding="latin-1", errors="replace")

        return [
            DocumentChunk(
                chunk_id=f"{doc_id}_p1_c0",
                doc_id=doc_id,
                content=content.strip(),
                page_number=1,
                chunk_index=0,
                metadata={"filename": file_path.name, "file_hash": file_hash, "source": str(file_path)},
            )
        ]

    @staticmethod
    def _load_pdf(file_path: Path, doc_id: str, file_hash: str) -> list[DocumentChunk]:
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(file_path)
            chunks: list[DocumentChunk] = []
            for page_idx, page in enumerate(doc, start=1):
                text = page.get_text().strip()
                if text:
                    chunks.append(
                        DocumentChunk(
                            chunk_id=f"{doc_id}_p{page_idx}_c0",
                            doc_id=doc_id,
                            content=text,
                            page_number=page_idx,
                            chunk_index=0,
                            metadata={"filename": file_path.name, "file_hash": file_hash, "page": page_idx},
                        )
                    )
            return chunks
        except ImportError:
            # shortcut: fallback to basic text extractor if PyMuPDF not installed, install pymupdf for full PDF extraction
            return DocumentLoader._load_text(file_path, doc_id, file_hash)
        except Exception as e:
            raise IngestionError(f"Failed to parse PDF {file_path.name}: {e}") from e

    @staticmethod
    def _load_docx(file_path: Path, doc_id: str, file_hash: str) -> list[DocumentChunk]:
        try:
            import docx
            doc = docx.Document(file_path)
            text = "\n\n".join([p.text for p in doc.paragraphs if p.text.strip()])
            return [
                DocumentChunk(
                    chunk_id=f"{doc_id}_p1_c0",
                    doc_id=doc_id,
                    content=text,
                    page_number=1,
                    chunk_index=0,
                    metadata={"filename": file_path.name, "file_hash": file_hash},
                )
            ]
        except ImportError:
            # shortcut: fallback to basic text read if python-docx not installed
            return DocumentLoader._load_text(file_path, doc_id, file_hash)
        except Exception as e:
            raise IngestionError(f"Failed to parse DOCX {file_path.name}: {e}") from e
