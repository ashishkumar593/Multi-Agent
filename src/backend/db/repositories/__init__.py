"""Repositories export."""
from src.backend.db.repositories.document_repo import DocumentRepository
from src.backend.db.repositories.research_repo import ResearchRepository

__all__ = ["ResearchRepository", "DocumentRepository"]
