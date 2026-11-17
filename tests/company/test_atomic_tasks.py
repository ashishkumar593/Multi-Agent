"""Tests for atomic task claiming, state transitions, and dependency resolution."""
import pytest
from backend.company.orchestrator import CompanyOrchestrator
from backend.db.company_database import SessionLocal, init_db
from backend.db.company_models import TaskModel


@pytest.fixture(autouse=True)
def setup_company_db():
    init_db(reset=True)
    yield


def test_atomic_task_claim_and_dependency_blocking():
    """Verify tasks with pending dependencies cannot be claimed until parent is done."""
    with SessionLocal() as db:
        orch = CompanyOrchestrator(db)
        project = orch.start_project(goal="Build landing page for VerdeBrew")

        # t1 has no dependencies
        t1 = db.query(TaskModel).filter(TaskModel.id == f"{project.id}_t1").first()
        # t2 depends on t1
        t2 = db.query(TaskModel).filter(TaskModel.id == f"{project.id}_t2").first()

        assert t1.status == "todo"
        assert t2.status == "todo"

        # Worker attempts to claim
        claimed_first = orch.runner.claim_task_atomically("agent_res_01")
        assert claimed_first is not None
        assert claimed_first.id == t1.id  # Must claim t1, NOT t2
        assert claimed_first.status == "doing"

        # Another worker attempts to claim; t2 should NOT be claimed because t1 is not yet done!
        claimed_second = orch.runner.claim_task_atomically("agent_mktg_01")
        assert claimed_second is None

        # Execute t1 to review and mark done
        orch.runner.execute_task("agent_res_01", claimed_first)
        claimed_first.status = "done"
        db.commit()

        # Now t2 has all dependencies satisfied and can be claimed!
        claimed_after_done = orch.runner.claim_task_atomically("agent_mktg_01")
        assert claimed_after_done is not None
        assert claimed_after_done.id == t2.id
        assert claimed_after_done.status == "doing"
