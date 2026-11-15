"""PDF report generation utility."""
from pathlib import Path

class PDFExporter:
    """Exports structured research report Markdown into PDF document."""

    @staticmethod
    def export(report_markdown: str, output_path: Path) -> Path:
        """Convert markdown text into a formatted PDF file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
            from reportlab.lib.styles import getSampleStyleSheet

            doc = SimpleDocTemplate(str(output_path), pagesize=letter)
            styles = getSampleStyleSheet()
            story = []

            for line in report_markdown.splitlines():
                clean_line = line.strip()
                if not clean_line:
                    story.append(Spacer(1, 8))
                    continue

                if clean_line.startswith("# "):
                    story.append(Paragraph(f"<b>{clean_line[2:]}</b>", styles["Title"]))
                    story.append(Spacer(1, 12))
                elif clean_line.startswith("## "):
                    story.append(Paragraph(f"<b>{clean_line[3:]}</b>", styles["Heading2"]))
                    story.append(Spacer(1, 8))
                elif clean_line.startswith("### "):
                    story.append(Paragraph(f"<b>{clean_line[4:]}</b>", styles["Heading3"]))
                    story.append(Spacer(1, 6))
                else:
                    # Strip unsupported markdown characters for basic reportlab rendering
                    safe_line = clean_line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                    story.append(Paragraph(safe_line, styles["Normal"]))
                    story.append(Spacer(1, 4))

            doc.build(story)
            return output_path
        except Exception:
            # Fallback: Save text file if reportlab encounters formatting issue
            fallback_path = output_path.with_suffix(".txt")
            fallback_path.write_text(report_markdown, encoding="utf-8")
            return fallback_path
