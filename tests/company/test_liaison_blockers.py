"""Tests for Human Liaison approval gates, blocker posting, and human unblocking."""
import pytest
from backend.company.orchestrator import CompanyOrchestrator
from backend.db.company_database import SessionLocal, init_db
from backend.db.company_models import BlockerModel, TaskModel


@pytest.fixture(autouse=True)
def setup_company_db():
    init_db(reset=True)
    yield


def test_human_approval_gate_and_blocker_resolution():
    """Verify sensitive tasks escalate to human owner and unblock upon reply."""
    with SessionLocal() as db:
        orch = CompanyOrchestrator(db)
        project = orch.start_project(goal="Deployment approval test")

        # Task 5 is "Human Approval for Public Deployment"
        t5 = db.query(TaskModel).filter(TaskModel.id == f"{project.id}_t5").first()
        t5.depends_on_json = "[]"
        db.commit()

        # Liaison claims the task
        claimed = orch.runner.claim_task_atomically("agent_liaison")
        assert claimed.id == t5.id

        # Liaison executes task and discovers it requires human release approval
        res = orch.runner.execute_task("agent_liaison", claimed)
        assert res["status"] == "blocked"

        db.refresh(t5)
        assert t5.status == "blocked"

        # Verify blocker was posted
        blocker = db.query(BlockerModel).filter(BlockerModel.task_id == t5.id).first()
        assert blocker is not None
        assert blocker.status == "pending"
        assert blocker.type == "approval"
        assert "Approve & Publish" in blocker.options

        # Human unblocks
        unblock_res = orch.resolve_blocker(blocker.id, action="Approve & Publish")
        assert unblock_res["status"] == "resolved"

        # Task is now marked done with human approval
        db.refresh(t5)
        assert t5.status == "done"
        assert "Approved by human owner" in t5.result
