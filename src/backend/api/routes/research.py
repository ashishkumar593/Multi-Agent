"""Research API routes."""
from src.backend.api.schemas import ResearchRequest, ResearchResponse
from src.backend.core.logging import logger

try:
    from fastapi import APIRouter, HTTPException
    router = APIRouter(prefix="/api/v1/research", tags=["Research"])

    @router.post("", response_model=ResearchResponse)
    async def run_research(request: ResearchRequest) -> ResearchResponse:
        from src.backend.api.app import workflow

        if not request.topic.strip():
            raise HTTPException(status_code=400, detail="Research topic cannot be empty.")

        logger.info(f"Initiating research API job: {request.topic}")
        state = await workflow.run(
            topic=request.topic,
            scope=request.scope,
            max_iterations=request.max_iterations,
        )

        draft = state.get("draft_report")
        critic = state.get("critic_feedback")

        return ResearchResponse(
            research_id=state.get("research_id", "job_0"),
            topic=state.get("topic", request.topic),
            status=state.get("status", "completed"),
            title=draft.title if draft else f"Research: {request.topic}",
            report_markdown=draft.body_markdown if draft else "",
            comparison_table=draft.comparison_table_markdown if draft else "",
            references_markdown=draft.references_markdown if draft else "",
            evidence_count=len(state.get("evidence", [])),
            quality_score=critic.quality_score if critic else 0.0,
        )
except ImportError:
    router = None  # type: ignore
