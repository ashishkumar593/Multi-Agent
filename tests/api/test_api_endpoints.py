"""Integration tests for FastAPI REST API schemas and route handlers."""
import pytest
from backend.api.schemas.requests import ResearchRequest
from backend.api.schemas.responses import ResearchResponse, DocumentResponse, HealthResponse
from backend.services.research_service import ResearchService


def test_api_pydantic_schemas():
    """Verify API request and response models parse and validate payloads correctly."""
    req = ResearchRequest(
        topic="Generative AI in Cybersecurity",
        scope="comprehensive",
        max_iterations=2,
    )
    assert req.topic == "Generative AI in Cybersecurity"
    assert req.scope == "comprehensive"
    assert req.max_iterations == 2

    job_resp = ResearchResponse(
        research_id="job_test_123",
        topic="Generative AI in Cybersecurity",
        status="completed",
        title="Generative AI in Cybersecurity",
        report_markdown="# Report Title\nContent",
        quality_score=9.5,
    )
    assert job_resp.research_id == "job_test_123"
    assert job_resp.status == "completed"

    doc_resp = DocumentResponse(
        id="doc_123",
        filename="threat_model.pdf",
        chunks_count=12,
        size_bytes=1024,
    )
    assert doc_resp.id == "doc_123"


def test_research_service_synchronous_lifecycle():
    """Verify backend research service executes and returns structured response."""
    service = ResearchService()
    res = service.execute_research_sync(
        topic="Microservices vs Monoliths in 2026",
        scope="fast",
        max_iterations=1,
    )

    assert "research_id" in res
    assert res["status"] in ("completed", "approved")
    assert "report_markdown" in res
    assert len(res["report_markdown"]) > 50


def test_fastapi_app_client():
    """Verify FastAPI routes when fastapi and testclient are available."""
    fastapi = pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient
    from backend.api.app import app

    if app is None:
        pytest.skip("FastAPI app not initialized")

    client = TestClient(app)
    
    # Test health check
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
