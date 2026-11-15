"""Business logic service for research workflows."""
import uuid
from typing import Any
from src.backend.db.repositories.research_repo import ResearchRepository
from src.backend.graph.workflow import ResearchWorkflow
from src.backend.rag.retriever import HybridRetriever

class ResearchService:
    """Manages the lifecycle of research queries and persistent state."""

    def __init__(self, retriever: HybridRetriever, repository: ResearchRepository | None = None):
        self.retriever = retriever
        self.workflow = ResearchWorkflow(retriever=retriever)
        self.repository = repository or ResearchRepository()

    def execute_research_sync(
        self, topic: str, scope: str = "comprehensive", max_iterations: int = 2
    ) -> dict[str, Any]:
        """Run research workflow synchronously and persist outcome."""
        job_id = f"job_{uuid.uuid4().hex[:12]}"
        self.repository.create(job_id=job_id, topic=topic, scope=scope)

        state = self.workflow.run_sync(topic=topic, scope=scope, max_iterations=max_iterations)
        draft = state.get("draft_report")
        critic = state.get("critic_feedback")

        title = draft.title if draft else f"Research: {topic}"
        markdown = draft.body_markdown if draft else "No content generated."
        score = critic.quality_score if critic else 0.0

        self.repository.update(
            job_id=job_id,
            status=state.get("status", "completed"),
            report_title=title,
            report_markdown=markdown,
            quality_score=score,
        )

        return {
            "research_id": job_id,
            "topic": topic,
            "status": state.get("status", "completed"),
            "title": title,
            "report_markdown": markdown,
            "comparison_table": draft.comparison_table_markdown if draft else "",
            "references_markdown": draft.references_markdown if draft else "",
            "evidence_count": len(state.get("evidence", [])),
            "quality_score": score,
        }

    async def execute_research(
        self, topic: str, scope: str = "comprehensive", max_iterations: int = 2
    ) -> dict[str, Any]:
        """Async wrapper for research execution."""
        return self.execute_research_sync(topic, scope, max_iterations)
