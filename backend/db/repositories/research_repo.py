"""Repository for research jobs."""
from typing import Any
from backend.db.models.research import ResearchJobModel

class ResearchRepository:
    """Handles database queries and updates for research jobs."""

    def __init__(self, session: Any = None):
        self.session = session
        self._memory_jobs: dict[str, dict[str, Any]] = {}

    def create(self, job_id: str, topic: str, scope: str = "comprehensive") -> dict[str, Any]:
        record = {
            "id": job_id,
            "topic": topic,
            "scope": scope,
            "status": "pending",
            "quality_score": 0.0,
            "report_title": None,
            "report_markdown": None,
        }
        if self.session:
            try:
                db_job = ResearchJobModel(id=job_id, topic=topic, scope=scope, status="pending")
                self.session.add(db_job)
                self.session.commit()
            except Exception:
                pass
        self._memory_jobs[job_id] = record
        return record

    def get_by_id(self, job_id: str) -> dict[str, Any] | None:
        if self.session:
            try:
                job = self.session.query(ResearchJobModel).filter_by(id=job_id).first()
                if job:
                    return {
                        "id": job.id,
                        "topic": job.topic,
                        "scope": job.scope,
                        "status": job.status,
                        "quality_score": job.quality_score,
                        "report_title": job.report_title,
                        "report_markdown": job.report_markdown,
                    }
            except Exception:
                pass
        return self._memory_jobs.get(job_id)

    def update(self, job_id: str, **kwargs: Any) -> None:
        if job_id in self._memory_jobs:
            self._memory_jobs[job_id].update(kwargs)
        if self.session:
            try:
                job = self.session.query(ResearchJobModel).filter_by(id=job_id).first()
                if job:
                    for k, v in kwargs.items():
                        setattr(job, k, v)
                    self.session.commit()
            except Exception:
                pass

    def list_all(self) -> list[dict[str, Any]]:
        return list(self._memory_jobs.values())
