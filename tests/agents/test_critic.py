"""Unit tests for Critic Agent."""
from src.backend.agents.critic import CriticAgent
from src.backend.agents.state import EvidenceItem, ReportDraft

def test_critic_flags_invalid_citation():
    critic = CriticAgent()
    draft = ReportDraft(
        title="Test Report",
        executive_summary="Summary",
        key_findings=["Finding A"],
        body_markdown="Claim with hallucinated citation [99].",
        references_markdown="[1] Real Source",
    )
    evidence = [EvidenceItem(evidence_id="e1", content="Text", source_title="S1", source_url_or_path="https://s1.org")]
    feedback = critic.review(draft, evidence)
    assert feedback.approved is False
    assert any("invalid citation" in issue.lower() for issue in feedback.issues)
