"""Report download and inspection API routes."""
from pathlib import Path
from src.backend.services.report_service import ReportService

try:
    from fastapi import APIRouter, HTTPException
    from fastapi.responses import FileResponse

    router = APIRouter(prefix="/api/v1/reports", tags=["Reports"])

    @router.get("/{report_id}/export")
    def export_report_pdf(report_id: str) -> FileResponse:
        output_path = Path(f"./data/processed/{report_id}.pdf")
        if not output_path.exists():
            raise HTTPException(status_code=404, detail="Report PDF not found.")
        return FileResponse(path=output_path, filename=f"{report_id}.pdf", media_type="application/pdf")
except ImportError:
    router = None  # type: ignore
