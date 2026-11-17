"""Tests for the emergency kill switch and financial budget ledger caps."""
import pytest
from backend.company.monitor import CompanyMonitor
from backend.company.orchestrator import CompanyOrchestrator
from backend.db.company_database import SessionLocal, init_db
from backend.db.company_models import BudgetLedgerModel


@pytest.fixture(autouse=True)
def setup_company_db():
    init_db(reset=True)
    CompanyMonitor.reset_kill_switch()
    yield
    CompanyMonitor.reset_kill_switch()


def test_kill_switch_halts_company():
    """Verify tripping kill switch immediately prevents agent task execution."""
    with SessionLocal() as db:
        orch = CompanyOrchestrator(db)
        orch.start_project(goal="Kill switch test")

        # Trip switch
        CompanyMonitor.trip_kill_switch("Safety test")
        assert CompanyMonitor.is_kill_switch_active() is True

        # Attempt to step
        step_res = orch.step()
        assert step_res["status"] == "paused"
        assert "Kill switch is active" in step_res["reason"]

        # Reset switch
        CompanyMonitor.reset_kill_switch()
        assert CompanyMonitor.is_kill_switch_active() is False

        step_res_after = orch.step()
        assert step_res_after["status"] == "active"


def test_budget_cap_trips_kill_switch():
    """Verify exceeding total budget cap automatically trips the kill switch."""
    with SessionLocal() as db:
        orch = CompanyOrchestrator(db)
        orch.start_project(goal="Budget cap test")

        # Simulate heavy spend in budget ledger exceeding $50 cap
        db.add(
            BudgetLedgerModel(
                agent_id="agent_dev_01",
                project_id="proj_test",
                tokens=500000,
                cost=65.0,  # Exceeds cap
                tool_calls=25,
            )
        )
        db.commit()

        # Monitor checks budget
        tripped = orch.monitor.check_budget_caps(max_company_spend=50.0)
        assert tripped is True
        assert CompanyMonitor.is_kill_switch_active() is True
