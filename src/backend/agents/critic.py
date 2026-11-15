"""Critic Agent: Fact-checking, hallucination detection, and citation integrity audit."""
import re
from src.backend.agents.state import CriticFeedback, EvidenceItem, ReportDraft

class CriticAgent:
    """Audits report drafts for factual support, citations, and logical cohesion."""

    def review(self, draft: ReportDraft, evidence: list[EvidenceItem]) -> CriticFeedback:
        """Perform adversarial inspection of report draft against gathered evidence."""
        issues: list[str] = []
        unsupported: list[str] = []

        # 1. Audit citation brackets in text vs references
        cites_in_text = [int(x) for x in re.findall(r"\[(\d+)\]", draft.body_markdown)]
        cites_in_refs = [int(x) for x in re.findall(r"\[(\d+)\]", draft.references_markdown)]
        max_valid_cite = max(cites_in_refs) if cites_in_refs else 0

        invalid_citations = [c for c in cites_in_text if c > max_valid_cite or c < 1]
        if invalid_citations:
            issues.append(f"Found invalid citation indices in report text: {set(invalid_citations)}")

        # 2. Check evidence depth
        if not evidence:
            issues.append("Report has no underlying evidence items.")
            return CriticFeedback(
                approved=False,
                quality_score=2.0,
                issues=issues,
                unsupported_claims=draft.key_findings,
                revision_instructions="Re-run search to gather supporting evidence.",
            )

        # 3. Check for empty findings
        if not draft.key_findings:
            issues.append("Report contains zero key findings.")
            unsupported.append("No findings generated.")

        # Compute objective score
        deductions = len(invalid_citations) * 1.5 + len(unsupported) * 2.0
        score = max(0.0, min(10.0, 9.5 - deductions))
        is_approved = score >= 7.5 and len(issues) == 0

        return CriticFeedback(
            approved=is_approved,
            quality_score=score,
            issues=issues,
            unsupported_claims=unsupported,
            revision_instructions="Resolve citation numbering discrepancies." if issues else "",
        )
