"""Pydantic schemas for analysis and claims."""
from typing import Literal
from pydantic import BaseModel, Field

class FactualClaim(BaseModel):
    claim_id: str
    statement: str
    supporting_evidence_ids: list[str] = Field(default_factory=list)
    contradicting_evidence_ids: list[str] = Field(default_factory=list)
    confidence: Literal["high", "medium", "low"] = "medium"
    reasoning: str = ""

class AnalysisResult(BaseModel):
    claims: list[FactualClaim] = Field(default_factory=list)
    contradictions_found: list[str] = Field(default_factory=list)
    knowledge_gaps: list[str] = Field(default_factory=list)
