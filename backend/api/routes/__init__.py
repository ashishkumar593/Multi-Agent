"""API routes export."""
from backend.api.routes.company import router as company_router
from backend.api.routes.documents import router as documents_router
from backend.api.routes.health import router as health_router
from backend.api.routes.reports import router as reports_router
from backend.api.routes.research import router as research_router

__all__ = ["health_router", "research_router", "documents_router", "reports_router", "company_router"]
