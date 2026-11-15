"""Pydantic schemas for generated reports and critic feedback."""
from pydantic import BaseModel, Field

class ReportDraft(BaseModel):
    title: str
    executive_summary: str
    key_findings: list[str] = Field(default_factory=list)
    body_markdown: str = ""
    comparison_table_markdown: str = ""
    limitations: str = ""
    references_markdown: str = ""

class CriticFeedback(BaseModel):
    approved: bool
    quality_score: float  # 0.0 to 10.0
    issues: list[str] = Field(default_factory=list)
    unsupported_claims: list[str] = Field(default_factory=list)
    revision_instructions: str = ""
