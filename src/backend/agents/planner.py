"""Planner Agent: Breaks open-ended research topics into structured, prioritized sub-questions."""
import json
from src.backend.agents.state import ResearchPlan, SubQuestion
from src.backend.core.config import settings

PLANNER_SYSTEM_PROMPT = """You are an expert AI Research Planner.
Your job is to analyze the research topic and break it down into 4 to 6 mutually exclusive, collectively exhaustive (MECE) sub-questions.
For each sub-question, specify its priority (1-5) and required evidence types.

Return valid JSON adhering strictly to this schema:
{
  "topic": "...",
  "objective": "...",
  "sub_questions": [
    {"id": "q1", "question": "...", "priority": 1, "evidence_type": "market_data"},
    {"id": "q2", "question": "...", "priority": 2, "evidence_type": "technical_analysis"}
  ],
  "strategy": "..."
}"""

class PlannerAgent:
    """Decomposes research topics into structured execution plans."""

    def __init__(self, model: str | None = None):
        self.model = model or settings.fast_model

    def plan(self, topic: str, scope: str = "comprehensive") -> ResearchPlan:
        """Generate structured research plan."""
        if not settings.openai_api_key:
            return self._fallback_plan(topic, scope)

        try:
            from openai import OpenAI
            client = OpenAI(api_key=settings.openai_api_key)
            resp = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": PLANNER_SYSTEM_PROMPT},
                    {"role": "user", "content": f"Topic: {topic}\nScope: {scope}"},
                ],
                response_format={"type": "json_object"},
                temperature=0.2,
            )
            data = json.loads(resp.choices[0].message.content or "{}")
            return ResearchPlan(
                topic=data.get("topic", topic),
                objective=data.get("objective", f"Investigate {topic}"),
                sub_questions=[SubQuestion(**sq) for sq in data.get("sub_questions", [])],
                strategy=data.get("strategy", "Iterative multi-source retrieval"),
            )
        except Exception:
            return self._fallback_plan(topic, scope)

    def _fallback_plan(self, topic: str, scope: str) -> ResearchPlan:
        """Deterministic plan when offline or without API key."""
        return ResearchPlan(
            topic=topic,
            objective=f"Analyze and synthesize key evidence regarding {topic}",
            sub_questions=[
                SubQuestion(id="q1", question=f"What is the historical baseline and current state of {topic}?", priority=1),
                SubQuestion(id="q2", question=f"What are the major technological and operational impacts of {topic}?", priority=1),
                SubQuestion(id="q3", question=f"What are the primary industry benchmarks, metrics, and quantitative findings for {topic}?", priority=2),
                SubQuestion(id="q4", question=f"What are the prominent challenges, contradictions, and future projections for {topic}?", priority=2),
            ],
            strategy="Search public web indices and internal documents concurrently.",
        )
