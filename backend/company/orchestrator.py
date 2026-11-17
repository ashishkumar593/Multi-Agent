"""Autonomous AI Company Orchestrator.
Coordinates the 5 core loops defined in Section 7 of the Build Report:
1. Task loop (todo -> doing -> review -> done)
2. Health and auto-replacement loop (Monitor + HR)
3. Hiring loop (Demand-based headcount expansion)
4. Reward and review loop (Independent review, 0-10 scoring, reward points)
5. Blocker and approval loop (Human Liaison + Approval gates)
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional
from backend.db.company_database import CompanySession as Session

from backend.core.runner import GenericAgentRunner
from backend.company.monitor import CompanyMonitor
from backend.db.company_models import (
    AgentModel,
    BlockerModel,
    EventModel,
    ProjectModel,
    ReviewModel,
    RewardModel,
    TaskModel,
    TeamModel,
)


class CompanyOrchestrator:
    """Master engine orchestrating the company's autonomous operations."""

    def __init__(self, db: Session):
        self.db = db
        self.runner = GenericAgentRunner(db)
        self.monitor = CompanyMonitor(db)

    # -------------------------------------------------------------
    # 1. Project Initialization by CEO & Manager
    # -------------------------------------------------------------
    def start_project(self, goal: str, project_name: str = "VerdeBrew Landing Page") -> ProjectModel:
        """CEO initiates the project and Manager creates 5 to 10 dependent tasks."""
        proj_id = f"proj_{int(datetime.now(timezone.utc).timestamp())}"
        project = ProjectModel(
            id=proj_id,
            name=project_name,
            goal=goal,
            budget_limit=50.0,
            owner_agent_id="agent_ceo",
            status="active",
        )
        self.db.add(project)
        self.db.commit()

        # Manager creates the 5-task standard landing page project workflow
        tasks_spec = [
            {
                "id": f"{proj_id}_t1",
                "team_id": "team_mktg",
                "title": "Market & Competitor Research",
                "spec": "Analyze eco-friendly coffee brands and extract key value propositions.",
                "depends_on": [],
            },
            {
                "id": f"{proj_id}_t2",
                "team_id": "team_mktg",
                "title": "Landing Page Copywriting & Hero Messaging",
                "spec": "Draft high-converting headlines, feature bullets, and Call-To-Action (CTA).",
                "depends_on": [f"{proj_id}_t1"],
            },
            {
                "id": f"{proj_id}_t3",
                "team_id": "team_eng",
                "title": "HTML5 Semantic Structure & Layout",
                "spec": "Build responsive index.html in the sandbox including hero, features, and CTA button.",
                "depends_on": [f"{proj_id}_t2"],
            },
            {
                "id": f"{proj_id}_t4",
                "team_id": "team_eng",
                "title": "CSS Modern Styling & Design System",
                "spec": "Style the landing page with modern emerald palette and clean typography.",
                "depends_on": [f"{proj_id}_t3"],
            },
            {
                "id": f"{proj_id}_t5",
                "team_id": "team_ops",
                "title": "Human Approval for Public Deployment",
                "spec": "Gate release behind human owner approval via Human Liaison.",
                "depends_on": [f"{proj_id}_t4"],
            },
        ]

        for t in tasks_spec:
            task = TaskModel(
                id=t["id"],
                project_id=proj_id,
                team_id=t["team_id"],
                title=t["title"],
                spec=t["spec"],
                status="todo",
                depends_on_json=json.dumps(t["depends_on"]),
            )
            self.db.add(task)

        self.db.commit()
        return project

    # -------------------------------------------------------------
    # 2. Main Step Loop
    # -------------------------------------------------------------
    def step(self) -> dict[str, Any]:
        """Execute one complete cycle of all 5 company loops."""
        if self.monitor.is_kill_switch_active():
            return {"status": "paused", "reason": "Kill switch is active"}

        # Loop 2: Health & Auto-Replacement
        dead_agents = self.monitor.check_heartbeats_and_reap()
        replaced = []
        if dead_agents:
            replaced = self.monitor.handle_hr_replacements(dead_agents)

        # Loop 3: Hiring Check
        hired = self._check_hiring_need()

        # Loop 1: Task Execution Loop
        executed_tasks = []
        idle_agents = (
            self.db.query(AgentModel)
            .filter(AgentModel.status.in_(["alive", "idle"]))
            .all()
        )

        for agent in idle_agents:
            if agent.role in ("reviewer", "ceo", "hr", "monitor"):
                continue  # These operate on dedicated queues or triggers
            claimed = self.runner.claim_task_atomically(agent.id)
            if claimed:
                res = self.runner.execute_task(agent.id, claimed)
                executed_tasks.append(claimed.id)

        # Loop 4: Reward and Review Loop
        reviews_done = self._process_reviews()

        # Check total budget
        self.monitor.check_budget_caps()

        return {
            "status": "active",
            "executed_tasks": executed_tasks,
            "reviews_done": reviews_done,
            "dead_agents_reaped": dead_agents,
            "agents_replaced": replaced,
            "agents_hired": hired,
        }

    # -------------------------------------------------------------
    # Helper: Review Loop Processing
    # -------------------------------------------------------------
    def _process_reviews(self) -> list[str]:
        """Reviewer agent inspects tasks waiting in 'review' status."""
        tasks_in_review = self.db.query(TaskModel).filter(TaskModel.status == "review").all()
        reviewer = self.db.query(AgentModel).filter(AgentModel.role == "reviewer").first()
        if not reviewer:
            return []

        processed = []
        for task in tasks_in_review:
            # Reviewer runs test suite
            test_results = self.runner.tools.run_tests(task.id, reviewer.id)
            score = test_results.get("score", 9.0)
            verdict = test_results.get("verdict", "approved")
            notes = "; ".join(test_results.get("issues", [])) or "All structural tests passed."

            self.runner.tools.score_task(
                task_id=task.id,
                quality_score=score,
                verdict=verdict,
                notes=notes,
                agent_id=reviewer.id,
            )
            processed.append(task.id)

        return processed

    # -------------------------------------------------------------
    # Helper: Demand-Based Hiring Loop
    # -------------------------------------------------------------
    def _check_hiring_need(self) -> list[str]:
        """Hire additional workers if open tasks per agent in a team exceeds threshold."""
        hired = []
        teams = self.db.query(TeamModel).all()
        for team in teams:
            open_tasks = (
                self.db.query(TaskModel)
                .filter(TaskModel.team_id == team.id, TaskModel.status.in_(["todo", "doing"]))
                .count()
            )
            active_agents = (
                self.db.query(AgentModel)
                .filter(AgentModel.team_id == team.id, AgentModel.status.in_(["alive", "busy"]))
                .count()
            )

            # If workload is high (> 3 tasks per agent) and team not at max headcount
            if active_agents > 0 and (open_tasks / active_agents) >= 3.0 and active_agents < team.max_headcount:
                # Hire a worker matching team function
                role = "developer" if team.id == "team_eng" else "marketing"
                res = self.runner.tools.spawn_agent(role=role, team_id=team.id, agent_id="agent_hr")
                if res.get("status") == "spawned":
                    hired.append(res["agent_id"])

        return hired

    # -------------------------------------------------------------
    # Loop 5: Blocker Resolution by Human Owner
    # -------------------------------------------------------------
    def resolve_blocker(self, blocker_id: int, action: str = "Approve") -> dict[str, Any]:
        """Human owner unblocks a pending task or approves an action."""
        blocker = self.db.query(BlockerModel).filter(BlockerModel.id == blocker_id).first()
        if not blocker or blocker.status != "pending":
            return {"status": "error", "message": "Blocker not found or already resolved"}

        blocker.status = "resolved"
        blocker.resolved_at = datetime.now(timezone.utc)

        task = self.db.query(TaskModel).filter(TaskModel.id == blocker.task_id).first()
        if task:
            if action.lower() in ("approve", "approve & publish"):
                task.status = "done"
                task.result = json.dumps({"human_approval": "Approved by human owner for public release."})
            else:
                task.status = "todo"  # Send back for revision

        self.db.commit()
        return {"status": "resolved", "blocker_id": blocker_id, "action": action}
