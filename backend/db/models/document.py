"""SQLAlchemy models for uploaded documents and metadata."""
from datetime import datetime
from backend.db.database import Base

try:
    from sqlalchemy import Column, DateTime, Integer, String

    class DocumentModel(Base):
        """Persistent record of an ingested document."""
        __tablename__ = "documents"

        id = Column(String(64), primary_key=True, index=True)
        filename = Column(String(256), nullable=False)
        file_hash = Column(String(64), nullable=False, unique=True, index=True)
        chunks_count = Column(Integer, default=0)
        size_bytes = Column(Integer, default=0)
        created_at = Column(DateTime, default=datetime.utcnow)
except Exception:
    class DocumentModel:  # type: ignore
        pass
