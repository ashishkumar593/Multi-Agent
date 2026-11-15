"""Unit tests for Analyst Agent."""
from src.backend.agents.analyst import AnalystAgent
from src.backend.agents.state import EvidenceItem, ResearchPlan

def test_analyst_claim_extraction():
    analyst = AnalystAgent()
    plan = ResearchPlan(topic="Quantum Encryption", objective="Evaluate readiness", sub_questions=[], strategy="Test")
    evidence = [
        EvidenceItem(
            evidence_id="ev1",
            content="NIST finalized post-quantum encryption standards in 2024.",
            source_title="NIST Release",
            source_url_or_path="https://nist.gov/pqc",
            credibility_score=0.95,
        )
    ]
    res = analyst.analyze(plan, evidence)
    assert len(res.claims) >= 1
    assert "ev1" in res.claims[0].supporting_evidence_ids
    assert res.claims[0].confidence == "high"
