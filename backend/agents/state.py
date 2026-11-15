"""Multi-agent shared state and data contracts."""
from typing import TypedDict
from backend.agents.schemas import (
    AnalysisResult,
    CriticFeedback,
    EvidenceItem,
    FactualClaim,
    ReportDraft,
    ResearchPlan,
    SubQuestion,
)

class ResearchState(TypedDict):
    """Workflow state dictionary passed across LangGraph nodes."""
    research_id: str
    topic: str
    scope: str
    plan: ResearchPlan | None
    evidence: list[EvidenceItem]
    analysis: AnalysisResult | None
    draft_report: ReportDraft | None
    critic_feedback: CriticFeedback | None
    iteration_count: int
    max_iterations: int
    status: str
    errors: list[str]

__all__ = [
    "SubQuestion",
    "ResearchPlan",
    "EvidenceItem",
    "FactualClaim",
    "AnalysisResult",
    "ReportDraft",
    "CriticFeedback",
    "ResearchState",
]
