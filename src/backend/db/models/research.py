"""SQLAlchemy models for research jobs and progress tracking."""
from datetime import datetime
from src.backend.db.database import Base

try:
    from sqlalchemy import Column, DateTime, Float, Integer, String, Text

    class ResearchJobModel(Base):
        """Persistent research job record."""
        __tablename__ = "research_jobs"

        id = Column(String(64), primary_key=True, index=True)
        topic = Column(String(512), nullable=False)
        scope = Column(String(64), default="comprehensive")
        status = Column(String(32), default="pending", index=True)
        current_agent = Column(String(32), default="planner")
        quality_score = Column(Float, default=0.0)
        report_title = Column(String(512), nullable=True)
        report_markdown = Column(Text, nullable=True)
        created_at = Column(DateTime, default=datetime.utcnow)
        updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
except Exception:
    class ResearchJobModel:  # type: ignore
        pass
