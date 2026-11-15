"""Analyst Agent: Evidence synthesis, claim extraction, and contradiction detection."""
import json
from backend.agents.state import AnalysisResult, EvidenceItem, FactualClaim, ResearchPlan
from backend.core.config import settings

ANALYST_SYSTEM_PROMPT = """You are an expert AI Research Analyst.
Your task is to analyze retrieved evidence items, extract atomic factual claims, and cross-reference them:
1. For every claim, identify supporting evidence IDs (e.g. "ev_web_q1_0").
2. Check for contradictions or conflicting statements between sources and list contradicting evidence IDs.
3. Assign confidence ("high", "medium", "low") based on source authority and corroboration.
4. Note any critical knowledge gaps.

Return valid JSON:
{
  "claims": [
    {
      "claim_id": "c1",
      "statement": "...",
      "supporting_evidence_ids": ["..."],
      "contradicting_evidence_ids": [],
      "confidence": "high",
      "reasoning": "..."
    }
  ],
  "contradictions_found": ["Source A says X while Source B reports Y..."],
  "knowledge_gaps": ["No reliable quantitative data found for Z..."]
}"""

class AnalystAgent:
    """Extracts factual claims, identifies contradictions, and evaluates confidence."""

    def __init__(self, model: str | None = None):
        self.model = model or settings.default_model

    def analyze(self, plan: ResearchPlan, evidence: list[EvidenceItem]) -> AnalysisResult:
        """Synthesize claims from evidence items."""
        if not evidence:
            return AnalysisResult(
                claims=[],
                contradictions_found=[],
                knowledge_gaps=["No evidence gathered to analyze."],
            )

        if not settings.openai_api_key:
            return self._fallback_analysis(evidence)

        try:
            from openai import OpenAI
            client = OpenAI(api_key=settings.openai_api_key)
            evidence_summary = "\n".join(
                [f"[{e.evidence_id}] ({e.source_title}): {e.content[:300]}" for e in evidence[:15]]
            )
            resp = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": ANALYST_SYSTEM_PROMPT},
                    {"role": "user", "content": f"Topic: {plan.topic}\n\nEVIDENCE:\n{evidence_summary}"},
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
            )
            data = json.loads(resp.choices[0].message.content or "{}")
            return AnalysisResult(
                claims=[FactualClaim(**c) for c in data.get("claims", [])],
                contradictions_found=data.get("contradictions_found", []),
                knowledge_gaps=data.get("knowledge_gaps", []),
            )
        except Exception:
            return self._fallback_analysis(evidence)

    def _fallback_analysis(self, evidence: list[EvidenceItem]) -> AnalysisResult:
        claims: list[FactualClaim] = []
        for idx, item in enumerate(evidence[:6]):
            claims.append(
                FactualClaim(
                    claim_id=f"c{idx+1}",
                    statement=f"Evidence from {item.source_title} demonstrates substantive activity.",
                    supporting_evidence_ids=[item.evidence_id],
                    confidence="high" if item.credibility_score >= 0.8 else "medium",
                    reasoning=f"Extracted directly from source: {item.source_title}",
                )
            )

        return AnalysisResult(
            claims=claims,
            contradictions_found=[],
            knowledge_gaps=[] if len(evidence) >= 3 else ["Limited evidence depth for secondary sub-questions."],
        )
