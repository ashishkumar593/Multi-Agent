"""Documents management API routes."""
from pathlib import Path
from typing import Any
from src.backend.api.schemas import DocumentResponse

try:
    from fastapi import APIRouter, File, HTTPException, UploadFile
    router = APIRouter(prefix="/api/v1/documents", tags=["Documents"])

    @router.post("", response_model=dict[str, Any])
    async def upload_document(file: UploadFile = File(...)) -> dict[str, Any]:
        from src.backend.api.app import document_service

        filename = file.filename or "uploaded_file"
        suffix = Path(filename).suffix.lower()
        if suffix not in (".pdf", ".docx", ".txt", ".md"):
            raise HTTPException(status_code=400, detail=f"Unsupported format: {suffix}")

        upload_dir = Path("./data/raw")
        upload_dir.mkdir(parents=True, exist_ok=True)
        temp_path = upload_dir / filename

        content = await file.read()
        temp_path.write_bytes(content)

        try:
            record = document_service.process_file(temp_path)
            return {"status": "success", "document": record}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Ingestion failed: {e}") from e

    @router.get("", response_model=list[dict[str, Any]])
    def list_documents() -> list[dict[str, Any]]:
        from src.backend.api.app import document_service
        return document_service.list_documents()
except ImportError:
    router = None  # type: ignore
