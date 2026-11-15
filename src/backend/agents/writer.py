"""Writer Agent: Generates publication-ready cited research reports with comparison tables."""
import json
import re
from src.backend.agents.state import AnalysisResult, EvidenceItem, ReportDraft, ResearchPlan
from src.backend.core.config import settings

class WriterAgent:
    """Drafts comprehensive cited reports from structured analytical findings."""

    def __init__(self, model: str | None = None):
        self.model = model or settings.default_model

    def draft_report(
        self, plan: ResearchPlan, analysis: AnalysisResult, evidence: list[EvidenceItem]
    ) -> ReportDraft:
        """Synthesize final report draft and format verified citations."""
        evidence_map = {e.evidence_id: e for e in evidence}
        evidence_index_map: dict[str, int] = {}
        ordered_sources: list[EvidenceItem] = []

        # Map each evidence item used to a sequential citation index
        for claim in analysis.claims:
            for eid in claim.supporting_evidence_ids:
                if eid in evidence_map and eid not in evidence_index_map:
                    ordered_sources.append(evidence_map[eid])
                    evidence_index_map[eid] = len(ordered_sources)

        # Build comparison table markdown
        table_lines = [
            "| Claim ID | Factual Assertion | Confidence | Supporting Citations |",
            "| :--- | :--- | :--- | :--- |",
        ]
        for c in analysis.claims:
            cites = " ".join([f"[{evidence_index_map[eid]}]" for eid in c.supporting_evidence_ids if eid in evidence_index_map])
            table_lines.append(f"| {c.claim_id} | {c.statement} | **{c.confidence.upper()}** | {cites or 'N/A'} |")
        comparison_table = "\n".join(table_lines)

        # Build references markdown
        ref_lines = ["\n### References & Verified Sources"]
        for idx, src in enumerate(ordered_sources, start=1):
            page_info = f", Page {src.page_number}" if src.page_number else ""
            ref_lines.append(f"[{idx}] **{src.source_title}** — [{src.source_url_or_path}]({src.source_url_or_path}){page_info} (Credibility: {int(src.credibility_score*100)}%)")
        references_md = "\n".join(ref_lines)

        # Generate report content
        body_parts: list[str] = [
            f"# Research Report: {plan.topic}",
            f"\n## 1. Executive Summary\nThis report investigates {plan.topic}. Across analyzed empirical and industry sources, {len(analysis.claims)} primary factual claims were verified.",
            f"\n## 2. Research Objective & Methodology\n- **Objective**: {plan.objective}\n- **Strategy**: {plan.strategy}\n- **Sources Evaluated**: {len(evidence)} total retrieved passages.",
            "\n## 3. Key Findings & Cross-Evidence Analysis",
        ]

        for claim in analysis.claims:
            cites = " ".join([f"[{evidence_index_map[eid]}]" for eid in claim.supporting_evidence_ids if eid in evidence_index_map])
            body_parts.append(f"- **{claim.statement}** {cites}\n  *Confidence*: {claim.confidence.title()} | *Reasoning*: {claim.reasoning}")

        body_parts.append("\n## 4. Evidence Matrix & Comparative Analysis\n" + comparison_table)

        if analysis.contradictions_found:
            body_parts.append("\n## 5. Contradictory Evidence & Nuances")
            for contra in analysis.contradictions_found:
                body_parts.append(f"- {contra}")

        limitations = (
            "Findings reflect current retrieved web and document sources. "
            + (" ".join(analysis.knowledge_gaps) if analysis.knowledge_gaps else "No major knowledge gaps were detected.")
        )
        body_parts.append(f"\n## 6. Limitations & Knowledge Gaps\n{limitations}")
        body_parts.append(references_md)

        full_markdown = "\n".join(body_parts)

        return ReportDraft(
            title=f"Research Report: {plan.topic}",
            executive_summary=f"Analysis of {plan.topic} based on {len(ordered_sources)} verified source citations.",
            key_findings=[c.statement for c in analysis.claims],
            body_markdown=full_markdown,
            comparison_table_markdown=comparison_table,
            limitations=limitations,
            references_markdown=references_md,
        )
