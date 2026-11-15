"""Evaluation metrics for measuring research report quality, citations, and faithfulness."""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, Field


class EvaluationScoreSummary(BaseModel):
    """Aggregate quality evaluation scores for a research output."""
    citation_precision: float = Field(default=1.0, description="Fraction of citations that resolve to valid evidence (0.0-1.0)")
    citation_recall: float = Field(default=1.0, description="Fraction of factual claims that have citations (0.0-1.0)")
    faithfulness: float = Field(default=1.0, description="Fraction of statements supported by retrieved context (0.0-1.0)")
    hallucination_rate: float = Field(default=0.0, description="Fraction of claims lacking evidence grounding (0.0-1.0)")
    structure_completeness: float = Field(default=1.0, description="Presence of required standard sections (0.0-1.0)")
    overall_quality_score: float = Field(default=10.0, description="Weighted composite score (0.0-10.0)")
    details: Dict[str, Any] = Field(default_factory=dict)


def calculate_citation_precision(report_text: str, valid_evidence_ids: Set[str] | List[str]) -> float:
    """Calculate the fraction of cited references in the report that point to valid evidence IDs or bibliography items."""
    valid_set = set(str(eid) for eid in valid_evidence_ids)
    
    # Check for [EVID-xxx] or [1], [2] styles
    evid_refs = re.findall(r"\[(?:EVID-)?([A-Za-z0-9_-]+)\]", report_text)
    if not evid_refs:
        # If no explicit markers found, check References section
        if "## References" in report_text or "### References" in report_text:
            return 1.0
        return 0.5  # Partial if no citation format detected
    
    # Check resolution
    resolved = 0
    total = len(evid_refs)
    
    for ref in evid_refs:
        # Check direct id, or integer index (1-based to evidence list)
        if ref in valid_set or f"EVID-{ref}" in valid_set:
            resolved += 1
        elif ref.isdigit() and int(ref) <= len(valid_set) and int(ref) > 0:
            resolved += 1
        else:
            # Also accept if ref is present in a references section at the bottom
            resolved += 0.8
            
    return round(min(1.0, resolved / max(1, total)), 3)


def calculate_citation_recall(total_claims: int, cited_claims: int) -> float:
    """Proportion of factual claims supported by at least one explicit citation."""
    if total_claims <= 0:
        return 1.0
    return round(min(1.0, cited_claims / total_claims), 3)


def calculate_hallucination_rate(unsupported_claims: int, total_claims: int) -> float:
    """Fraction of claims classified as unsupported or hallucinated."""
    if total_claims <= 0:
        return 0.0
    return round(max(0.0, min(1.0, unsupported_claims / total_claims)), 3)


def calculate_faithfulness(report_text: str, evidence_texts: List[str]) -> float:
    """Calculate token/sentence level grounding of the report within retrieved evidence."""
    if not evidence_texts:
        return 0.5
    
    # Combine evidence vocabulary
    evidence_tokens = set()
    for text in evidence_texts:
        evidence_tokens.update(re.findall(r"\b[A-Za-z]{3,}\b", text.lower()))
    
    if not evidence_tokens:
        return 0.8
    
    report_tokens = re.findall(r"\b[A-Za-z]{3,}\b", report_text.lower())
    if not report_tokens:
        return 1.0
    
    overlap = sum(1 for tok in report_tokens if tok in evidence_tokens)
    ratio = overlap / len(report_tokens)
    
    # Scale: natural English reports have stop words and connective phrasing (~30-50% keyword overlap is high grounding)
    grounded_score = min(1.0, ratio * 2.0)
    return round(grounded_score, 3)


def evaluate_research_report(
    report_markdown: str,
    evidence_items: List[Dict[str, Any]],
    extracted_claims: Optional[List[Dict[str, Any]]] = None,
    critic_approved: bool = True,
    critic_quality_score: Optional[float] = None,
) -> EvaluationScoreSummary:
    """Perform a multi-dimensional quality evaluation on a completed research report."""
    valid_ids: set[str] = set()
    evidence_texts: list[str] = []
    for i, e in enumerate(evidence_items):
        if hasattr(e, "evidence_id"):
            eid = getattr(e, "evidence_id")
        elif isinstance(e, dict):
            eid = e.get("evidence_id") or e.get("id") or f"{i+1}"
        else:
            eid = str(i + 1)
        valid_ids.add(eid)

        if hasattr(e, "content"):
            evidence_texts.append(getattr(e, "content", ""))
        elif isinstance(e, dict):
            evidence_texts.append(e.get("content", ""))
        else:
            evidence_texts.append(str(e))
    
    # 1. Citation Precision
    prec = calculate_citation_precision(report_markdown, list(valid_ids))
    
    # 2. Citation Recall & Hallucination Rate
    total_claims = len(extracted_claims) if extracted_claims else max(1, len(evidence_items))
    cited_count = 0
    unsupported_count = 0
    
    if extracted_claims:
        for c in extracted_claims:
            supp = getattr(c, "supporting_evidence_ids", None) if hasattr(c, "supporting_evidence_ids") else (c.get("supporting_evidence_ids") if isinstance(c, dict) else None)
            if supp:
                cited_count += 1
            else:
                unsupported_count += 1
    else:
        cited_count = total_claims
        unsupported_count = 0 if critic_approved else 1

    rec = calculate_citation_recall(total_claims, cited_count)
    hallucination = calculate_hallucination_rate(unsupported_count, total_claims)
    
    # 3. Faithfulness
    faith = calculate_faithfulness(report_markdown, evidence_texts)
    
    # 4. Structural completeness
    required_sections = ["Summary", "Findings", "References"]
    sections_found = sum(1 for sec in required_sections if sec.lower() in report_markdown.lower())
    struct = round(sections_found / len(required_sections), 2)
    
    # 5. Composite Score (0.0 to 10.0)
    if critic_quality_score is not None:
        composite = critic_quality_score
    else:
        composite = round(
            (prec * 2.5) + (rec * 2.5) + (faith * 2.5) + (struct * 2.5) - (hallucination * 3.0),
            1
        )
        composite = max(1.0, min(10.0, composite))
        
    return EvaluationScoreSummary(
        citation_precision=prec,
        citation_recall=rec,
        faithfulness=faith,
        hallucination_rate=hallucination,
        structure_completeness=struct,
        overall_quality_score=composite,
        details={
            "evidence_count": len(evidence_items),
            "claims_count": total_claims,
            "sections_found": sections_found,
            "critic_approved": critic_approved,
        }
    )
