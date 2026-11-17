"""Tests for Reviewer testing, scoring, and reward point calculation."""
import pytest
from backend.company.orchestrator import CompanyOrchestrator
from backend.db.company_database import SessionLocal, init_db
from backend.db.company_models import AgentModel, ReviewModel, RewardModel, TaskModel


@pytest.fixture(autouse=True)
def setup_company_db():
    init_db(reset=True)
    yield


def test_reviewer_scores_deliverable_and_awards_points():
    """Verify Reviewer independently evaluates deliverables and awards points."""
    with SessionLocal() as db:
        orch = CompanyOrchestrator(db)
        project = orch.start_project(goal="Reviewer test")

        # Developer claims and builds landing page (task 3)
        t3 = db.query(TaskModel).filter(TaskModel.id == f"{project.id}_t3").first()
        t3.depends_on_json = "[]"  # bypass dependency for isolated test
        db.commit()

        claimed = orch.runner.claim_task_atomically("agent_dev_01")
        assert claimed.id == t3.id

        dev_agent = db.query(AgentModel).filter(AgentModel.id == "agent_dev_01").first()
        initial_score = dev_agent.score

        # Execute: developer writes index.html & styles.css into sandbox
        orch.runner.execute_task("agent_dev_01", claimed)
        assert claimed.status == "review"

        # Step company: triggers Reviewer loop
        step_res = orch.step()
        assert t3.id in step_res["reviews_done"]

        # Verify task is approved and done
        db.refresh(t3)
        assert t3.status == "done"

        # Verify review recorded
        review = db.query(ReviewModel).filter(ReviewModel.task_id == t3.id).first()
        assert review is not None
        assert review.verdict == "approved"
        assert review.quality_score >= 7.0

        # Verify reward points added to developer
        reward = db.query(RewardModel).filter(RewardModel.task_id == t3.id).first()
        assert reward is not None
        assert reward.points > 0

        db.refresh(dev_agent)
        assert dev_agent.score > initial_score
