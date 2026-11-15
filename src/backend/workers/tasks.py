"""Celery background worker tasks for asynchronous research execution."""
import asyncio
from typing import Any
from src.backend.core.logging import logger
from src.backend.workers.queue import celery_app

if celery_app:
    @celery_app.task(name="execute_research_job", bind=True)
    def execute_research_job(self, topic: str, scope: str = "comprehensive", max_iterations: int = 2) -> dict[str, Any]:
        """Background task running multi-agent workflow."""
        from src.backend.api.app import workflow

        logger.info(f"[Celery] Processing research job: {topic}")
        state = workflow.run_sync(topic=topic, scope=scope, max_iterations=max_iterations)
        draft = state.get("draft_report")
        critic = state.get("critic_feedback")

        return {
            "research_id": state.get("research_id"),
            "status": state.get("status"),
            "title": draft.title if draft else f"Research: {topic}",
            "quality_score": critic.quality_score if critic else 0.0,
            "report_markdown": draft.body_markdown if draft else "",
        }
else:
    def execute_research_job(topic: str, scope: str = "comprehensive", max_iterations: int = 2) -> dict[str, Any]:  # type: ignore
        from src.backend.api.app import workflow
        state = workflow.run_sync(topic=topic, scope=scope, max_iterations=max_iterations)
        draft = state.get("draft_report")
        return {
            "research_id": state.get("research_id"),
            "status": state.get("status"),
            "report_markdown": draft.body_markdown if draft else "",
        }
