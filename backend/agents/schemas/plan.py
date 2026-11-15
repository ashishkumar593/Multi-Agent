"""Pydantic schemas for research planning."""
from pydantic import BaseModel, Field

class SubQuestion(BaseModel):
    id: str
    question: str
    priority: int = 1
    evidence_type: str = "web_and_docs"

class ResearchPlan(BaseModel):
    topic: str
    objective: str
    sub_questions: list[SubQuestion] = Field(default_factory=list)
    strategy: str = "Iterative multi-source retrieval"
