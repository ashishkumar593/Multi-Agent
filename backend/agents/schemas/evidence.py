"""Pydantic schemas for retrieved evidence items."""
from typing import Literal
from pydantic import BaseModel

class EvidenceItem(BaseModel):
    evidence_id: str
    content: str
    source_title: str
    source_url_or_path: str
    source_type: Literal["web", "document"] = "web"
    page_number: int | None = None
    credibility_score: float = 0.5
