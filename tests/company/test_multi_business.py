"""Tests for multi-business expansion: Lead Research Service and SEO Content Agency."""
import pytest
from pathlib import Path
from backend.company.orchestrator import CompanyOrchestrator
from backend.db.company_database import SessionLocal, init_db
from backend.db.company_models import TaskModel


@pytest.fixture(autouse=True)
def setup_company_db():
    init_db(reset=True)
    yield


def test_lead_research_business_workflow():
    """Verify Lead Research service runs end-to-end and outputs leads.csv deliverable."""
    with SessionLocal() as db:
        orch = CompanyOrchestrator(db)
        project = orch.start_project(
            goal="Generate 50 qualified B2B leads for CleanTech sustainable packaging",
            project_name="CleanTech Lead Campaign",
            business_type="lead_research",
        )

        tasks = db.query(TaskModel).filter(TaskModel.project_id == project.id).all()
        assert len(tasks) == 5
        assert "Define ICP" in tasks[0].title
        assert "CSV" in tasks[3].title

        # Step the company to execute tasks through auto-pilot
        for _ in range(5):
            orch.step()

        # Unblock deployment gate
        blocker = orch.db.query(TaskModel).filter(TaskModel.status == "blocked").first()
        if blocker:
            blocker_rec = orch.db.query(TaskModel).filter(TaskModel.id == blocker.id).first()
            from backend.db.company_models import BlockerModel
            blk = orch.db.query(BlockerModel).filter(BlockerModel.task_id == blocker.id).first()
            if blk:
                orch.resolve_blocker(blk.id, action="Approve")

        # Verify leads.csv exists in sandbox
        leads_csv = Path("./sandbox/leads.csv")
        assert leads_csv.exists()
        content = leads_csv.read_text(encoding="utf-8")
        assert "Company" in content
        assert "Fit Score" in content


def test_seo_content_agency_workflow():
    """Verify SEO Content Agency runs end-to-end and outputs article.md deliverable."""
    with SessionLocal() as db:
        orch = CompanyOrchestrator(db)
        project = orch.start_project(
            goal="Write an in-depth SEO pillar article on Carbon-Negative Specialty Coffee",
            project_name="SEO Pillar Content",
            business_type="seo_content",
        )

        tasks = db.query(TaskModel).filter(TaskModel.project_id == project.id).all()
        assert len(tasks) == 5
        assert "Keyword Research" in tasks[0].title
        assert "Article" in tasks[2].title

        # Step through execution
        for _ in range(5):
            orch.step()

        # Verify article.md exists in sandbox
        article_md = Path("./sandbox/article.md")
        assert article_md.exists()
        content = article_md.read_text(encoding="utf-8")
        assert "# " in content
        assert "Carbon-Negative" in content
