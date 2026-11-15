"""Health check routes."""
from src.backend.core.config import settings

try:
    from fastapi import APIRouter
    router = APIRouter(tags=["Health"])

    @router.get("/health")
    def health_check() -> dict[str, str]:
        return {"status": "ok", "app": settings.app_name, "env": settings.app_env}
except ImportError:
    router = None  # type: ignore
