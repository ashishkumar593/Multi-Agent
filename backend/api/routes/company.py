"""Company API endpoints for autonomous multi-agent cockpit integration."""
from typing import Any, Dict, List, Optional

try:
    from fastapi import APIRouter, HTTPException
    from pydantic import BaseModel, Field

    router = APIRouter(prefix="/company", tags=["Autonomous AI Company"])

    class ProjectCreateRequest(BaseModel):
        name: str = Field(..., example="Fintech Landing Page")
        goal: str = Field(..., example="Create a responsive HTML/CSS website for a fintech startup.")
        business_type: str = Field("website", example="website")
        budget_limit: float = Field(25.0, example=25.0)

    class BlockerResolveRequest(BaseModel):
        resolution: Optional[str] = Field("Approved by human supervisor", example="Approved")

    class KillSwitchRequest(BaseModel):
        tripped: bool = Field(True, example=True)

except ImportError:
    APIRouter = None  # type: ignore
    HTTPException = Exception  # type: ignore
    BaseModel = object  # type: ignore
    Field = lambda *args, **kwargs: None  # type: ignore
    router = None  # type: ignore


from backend.company.orchestrator import CompanyOrchestrator
from backend.db.company_database import get_company_db
from backend.db.company_models import (
    AgentModel,
    BlockerModel,
    BudgetLedgerModel,
    EventModel,
    ProjectModel,
    RewardModel,
    RoleSpecModel,
    TaskModel,
)

if router is not None:
    @router.get("/status")
    def get_company_status() -> Dict[str, Any]:
    """Get high-level status of the autonomous company."""
    with get_company_db() as session:
        agents = session.query(AgentModel).all()
        tasks = session.query(TaskModel).all()
        blockers = session.query(BlockerModel).all()
        ledger = session.query(BudgetLedgerModel).all()

        total_cost = sum(float(l.cost or 0.0) for l in ledger)
        open_blockers = [b for b in blockers if b.status == "open"]

        return {
            "status": "active",
            "agents_count": len(agents),
            "agents_alive": sum(1 for a in agents if a.status in ("alive", "busy")),
            "tasks_total": len(tasks),
            "tasks_done": sum(1 for t in tasks if t.status == "done"),
            "tasks_doing": sum(1 for t in tasks if t.status == "doing"),
            "tasks_todo": sum(1 for t in tasks if t.status == "todo"),
            "tasks_review": sum(1 for t in tasks if t.status == "review"),
            "tasks_blocked": sum(1 for t in tasks if t.status == "blocked"),
            "open_blockers": len(open_blockers),
            "total_spend": round(total_cost, 4),
        }


@router.get("/tasks")
def list_tasks(status: Optional[str] = None) -> List[Dict[str, Any]]:
    """List tasks on the board, optionally filtered by status."""
    with get_company_db() as session:
        query = session.query(TaskModel)
        if status:
            tasks = query.filter(TaskModel.status == status).all()
        else:
            tasks = query.all()

        return [
            {
                "id": t.id,
                "project_id": t.project_id,
                "team_id": t.team_id,
                "title": t.title,
                "status": t.status,
                "owner_agent_id": t.owner_agent_id,
                "attempts": t.attempts,
                "spec": t.spec,
                "result": t.result,
            }
            for t in tasks
        ]


@router.get("/agents")
def list_agents() -> List[Dict[str, Any]]:
    """List all registered agents and their current statuses."""
    with get_company_db() as session:
        agents = session.query(AgentModel).all()
        return [
            {
                "id": a.id,
                "role": a.role,
                "team_id": a.team_id,
                "status": a.status,
                "score": float(a.score or 0.0),
                "last_heartbeat": str(a.last_heartbeat) if a.last_heartbeat else None,
                "replaced_by": a.replaced_by,
            }
            for a in agents
        ]


@router.get("/blockers")
def list_blockers(status: Optional[str] = "open") -> List[Dict[str, Any]]:
    """List human approval blockers."""
    with get_company_db() as session:
        query = session.query(BlockerModel)
        if status:
            blockers = query.filter(BlockerModel.status == status).all()
        else:
            blockers = query.all()

        return [
            {
                "id": b.id,
                "agent_id": b.agent_id,
                "task_id": b.task_id,
                "type": b.type,
                "priority": b.priority,
                "status": b.status,
                "details": b.details,
                "created_at": str(b.created_at) if b.created_at else None,
            }
            for b in blockers
        ]


@router.post("/blockers/{blocker_id}/resolve")
def resolve_blocker(blocker_id: int, req: BlockerResolveRequest) -> Dict[str, Any]:
    """Resolve a blocker and return the associated task to the board."""
    with get_company_db() as session:
        blocker = session.query(BlockerModel).filter(BlockerModel.id == blocker_id).first()
        if not blocker:
            raise HTTPException(status_code=404, detail=f"Blocker {blocker_id} not found.")

        blocker.status = "resolved"
        task = session.query(TaskModel).filter(TaskModel.id == blocker.task_id).first()
        if task and task.status == "blocked":
            task.status = "todo"

        session.commit()
        return {"status": "resolved", "blocker_id": blocker_id, "task_id": blocker.task_id}


@router.post("/projects")
def create_project(req: ProjectCreateRequest) -> Dict[str, Any]:
    """Create a project and seed tasks via the CEO/Manager orchestrator."""
    orch = CompanyOrchestrator()
    project_id = orch.seed_project_and_tasks(
        project_name=req.name,
        goal=req.goal,
        business_type=req.business_type,
        budget_limit=req.budget_limit,
    )
    return {"status": "created", "project_id": project_id, "business_type": req.business_type}


@router.post("/orchestrator/step")
def run_orchestrator_step() -> Dict[str, Any]:
    """Run one step of the company orchestrator (executes 5 loops)."""
    orch = CompanyOrchestrator()
    summary = orch.step()
    return {"status": "stepped", "summary": summary}


@router.post("/kill-switch")
def toggle_kill_switch(req: KillSwitchRequest) -> Dict[str, Any]:
    """Trip or reset the emergency kill switch."""
    orch = CompanyOrchestrator()
    if req.tripped:
        orch.monitor.trip_kill_switch("Activated via API endpoint")
    else:
        orch.monitor.reset_kill_switch()
    return {"kill_switch": orch.monitor.kill_switch_active}
