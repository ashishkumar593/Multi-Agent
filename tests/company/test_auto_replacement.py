"""Tests for health monitoring, dead worker reaping, and HR auto-replacement."""
from datetime import datetime, timedelta, timezone
import pytest
from backend.company.orchestrator import CompanyOrchestrator
from backend.db.company_database import SessionLocal, init_db
from backend.db.company_models import AgentModel, TaskModel


@pytest.fixture(autouse=True)
def setup_company_db():
    init_db(reset=True)
    yield


def test_monitor_reaps_dead_agent_and_hr_replaces():
    """Verify dead workers are reaped, abandoned tasks return to todo, and HR spawns a replacement."""
    with SessionLocal() as db:
        orch = CompanyOrchestrator(db)
        project = orch.start_project(goal="Test auto replacement")

        # Worker claims task 1
        t1 = db.query(TaskModel).filter(TaskModel.id == f"{project.id}_t1").first()
        claimed = orch.runner.claim_task_atomically("agent_res_01")
        assert claimed.status == "doing"
        assert claimed.owner_agent_id == "agent_res_01"

        # Simulate agent crash / lost heartbeat (> 30s)
        agent = db.query(AgentModel).filter(AgentModel.id == "agent_res_01").first()
        agent.last_heartbeat = datetime.now(timezone.utc) - timedelta(seconds=60)
        db.commit()

        # 1. Monitor reaps dead agent
        dead_agents = orch.monitor.check_heartbeats_and_reap()
        assert "agent_res_01" in dead_agents

        # Abandoned task is restored to 'todo'
        db.refresh(t1)
        assert t1.status == "todo"
        assert t1.owner_agent_id is None

        # Dead agent has status 'dead'
        db.refresh(agent)
        assert agent.status == "dead"

        # 2. HR replaces the dead agent
        replacements = orch.monitor.handle_hr_replacements(dead_agents)
        assert len(replacements) == 1
        replacement_id = replacements[0]

        db.refresh(agent)
        assert agent.replaced_by == replacement_id

        # 3. Replacement agent claims and executes the task
        replacement_agent = db.query(AgentModel).filter(AgentModel.id == replacement_id).first()
        assert replacement_agent is not None
        assert replacement_agent.role == "researcher"
        assert replacement_agent.status == "alive"

        claimed_by_rep = orch.runner.claim_task_atomically(replacement_id)
        assert claimed_by_rep is not None
        assert claimed_by_rep.id == t1.id
        assert claimed_by_rep.status == "doing"
