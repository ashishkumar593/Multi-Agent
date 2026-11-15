"""API routes export."""
from src.backend.api.routes.documents import router as documents_router
from src.backend.api.routes.health import router as health_router
from src.backend.api.routes.reports import router as reports_router
from src.backend.api.routes.research import router as research_router

__all__ = ["health_router", "research_router", "documents_router", "reports_router"]
