"""Repositories export."""
from backend.db.repositories.document_repo import DocumentRepository
from backend.db.repositories.research_repo import ResearchRepository

__all__ = ["ResearchRepository", "DocumentRepository"]
