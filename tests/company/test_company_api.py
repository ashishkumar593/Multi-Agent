"""Tests for the company API endpoints."""
import pytest

try:
    from fastapi.testclient import TestClient
    from backend.api.app import app
    HAS_FASTAPI = app is not None
except ImportError:
    HAS_FASTAPI = False

from backend.db.company_database import init_db

@pytest.mark.skipif(not HAS_FASTAPI, reason="FastAPI or TestClient not installed in environment")
def test_company_api_flow():
    init_db()
    client = TestClient(app)

    # 1. Check status
    res = client.get("/company/status")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "active"
    assert data["agents_count"] >= 8

    # 2. List agents
    res = client.get("/company/agents")
    assert res.status_code == 200
    assert len(res.json()) >= 8

    # 3. Create project
    res = client.post("/company/projects", json={
        "name": "API Test Project",
        "goal": "Test company API via FastAPI",
        "business_type": "website",
        "budget_limit": 10.0
    })
    assert res.status_code == 200
    assert res.json()["status"] == "created"

    # 4. List tasks
    res = client.get("/company/tasks")
    assert res.status_code == 200
    assert len(res.json()) >= 3

    # 5. Step orchestrator
    res = client.post("/company/orchestrator/step")
    assert res.status_code == 200
    assert res.json()["status"] == "stepped"

    # 6. Kill switch toggle
    res = client.post("/company/kill-switch", json={"tripped": True})
    assert res.status_code == 200
    assert res.json()["kill_switch"] is True

    res = client.post("/company/kill-switch", json={"tripped": False})
    assert res.status_code == 200
    assert res.json()["kill_switch"] is False
