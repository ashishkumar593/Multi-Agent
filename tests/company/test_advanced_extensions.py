"""Tests for the advanced optional extensions: Agent Factory and Persistent Liaison Memory."""
import pytest
from pathlib import Path
from backend.db.company_database import init_db, SessionLocal
from backend.company.orchestrator import CompanyOrchestrator
from backend.company.memory import LiaisonMemory
from backend.db.company_models import RoleSpecModel, AgentModel, TaskModel, BlockerModel


@pytest.fixture(autouse=True)
def setup_db():
    init_db(reset=True)
    yield


def test_agent_factory_dynamic_role_creation():
    """Verify CEO/HR can register custom roles at runtime and spawn workers from it."""
    with SessionLocal() as db:
        orch = CompanyOrchestrator(db)

        # 1. Register a new role spec dynamically
        res = orch.runner.tools.register_role_spec(
            role="security_auditor",
            system_prompt="You are a Cybersecurity Auditor checking for zero-day vulnerabilities.",
            tools=["read_file", "run_sandbox"],
            model_tier="strong",
            max_steps=5,
            token_budget=15000,
            agent_id="agent_ceo",
        )
        assert res["status"] == "registered"

        # Verify spec exists in DB
        spec = db.query(RoleSpecModel).filter(RoleSpecModel.role == "security_auditor").first()
        assert spec is not None
        assert "run_sandbox" in spec.tools

        # 2. Spawn worker from the new spec
        spawn_res = orch.runner.tools.spawn_agent(
            role="security_auditor",
            team_id="team_ops",
            agent_id="agent_hr",
        )
        assert spawn_res["status"] == "spawned"
        new_agent_id = spawn_res["agent_id"]

        agent = db.query(AgentModel).filter(AgentModel.id == new_agent_id).first()
        assert agent is not None
        assert agent.role == "security_auditor"


def test_liaison_persistent_memory_and_deduplication():
    """Verify human decisions are recorded in memory and prevent duplicate questions."""
    memory_file = Path("./data/test_liaison_memory.json")
    if memory_file.exists():
        memory_file.unlink()

    memory = LiaisonMemory(filepath=memory_file)

    # 1. Record a decision
    memory.record_decision(
        task_title="Public Deployment Sign-Off",
        question_or_details="Task requires human owner sign-off prior to external release.",
        human_decision="Approved & Published",
        blocker_id=42,
    )

    # 2. Check if identical query matches memory
    match = memory.find_existing_decision(
        task_title="Public Deployment Sign-Off",
        details="Task requires human owner sign-off prior to external release.",
    )
    assert match is not None
    assert match["decision"] == "Approved & Published"

    # Clean up test artifact
    if memory_file.exists():
        memory_file.unlink()
