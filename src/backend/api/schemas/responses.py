"""API response schemas."""
from typing import Any
from pydantic import BaseModel, Field

class ResearchResponse(BaseModel):
    research_id: str
    topic: str
    status: str
    title: str
    report_markdown: str
    comparison_table: str = ""
    references_markdown: str = ""
    evidence_count: int = 0
    quality_score: float = 0.0

class DocumentResponse(BaseModel):
    id: str
    filename: str
    chunks_count: int
    size_bytes: int

class HealthResponse(BaseModel):
    status: str = "ok"
    app_name: str
    environment: str
