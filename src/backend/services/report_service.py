"""Report export and presentation service."""
from pathlib import Path
from src.backend.tools.pdf_export import PDFExporter

class ReportService:
    """Handles report generation, formatting, and file exports."""

    @staticmethod
    def export_pdf(report_markdown: str, output_path: Path) -> Path:
        """Export report markdown to PDF."""
        return PDFExporter.export(report_markdown, output_path)

    @staticmethod
    def export_markdown(report_markdown: str, output_path: Path) -> Path:
        """Export report markdown to file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report_markdown, encoding="utf-8")
        return output_path
