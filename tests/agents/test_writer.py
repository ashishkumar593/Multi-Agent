"""Unit tests for WriterAgent report synthesis and citation bibliography formatting."""
from backend.agents.schemas.analysis import AnalysisResult, FactualClaim
from backend.agents.schemas.evidence import EvidenceItem
from backend.agents.schemas.plan import ResearchPlan, SubQuestion
from backend.agents.writer import WriterAgent


def test_writer_agent_report_structure():
    """Verify WriterAgent creates all standard sections, citations, and comparison table."""
    plan = ResearchPlan(
        topic="Enterprise Cloud Migration",
        objective="Assess cloud ROI",
        sub_questions=[
            SubQuestion(
                id="sq1",
                question="What are typical cost savings?",
                priority=1,
            )
        ],
    )

    evidence = [
        EvidenceItem(
            evidence_id="ev_1",
            content="Gartner reports 20% average cost savings after year two.",
            source_title="Gartner Cloud Report 2024",
            source_url_or_path="https://gartner.com/cloud2024",
            source_type="web",
            credibility_score=0.95,
        ),
        EvidenceItem(
            evidence_id="ev_2",
            content="Initial migration costs often exceed estimates by 15%.",
            source_title="McKinsey Cloud Survey",
            source_url_or_path="https://mckinsey.com/cloud",
            source_type="web",
            credibility_score=0.90,
        ),
    ]

    analysis = AnalysisResult(
        claims=[
            FactualClaim(
                claim_id="cl_1",
                statement="Organizations realize 20% cost savings after year two of cloud migration.",
                supporting_evidence_ids=["ev_1"],
                confidence="high",
                reasoning="Corroborated by enterprise benchmarks",
            ),
            FactualClaim(
                claim_id="cl_2",
                statement="Migration cost overruns average 15% during early phases.",
                supporting_evidence_ids=["ev_2"],
                confidence="medium",
                reasoning="Identified in migration surveys",
            ),
        ],
        contradictions_found=["Initial spend increases despite long-term operational savings."],
    )

    writer = WriterAgent()
    draft = writer.draft_report(plan, analysis, evidence)

    assert "Executive Summary" in draft.body_markdown
    assert "Methodology" in draft.body_markdown
    assert "Key Findings" in draft.body_markdown
    assert "Evidence Matrix" in draft.body_markdown
    assert "References" in draft.body_markdown
    assert "| Claim ID |" in draft.comparison_table_markdown
    assert "[1]" in draft.body_markdown
    assert "gartner.com/cloud2024" in draft.references_markdown
