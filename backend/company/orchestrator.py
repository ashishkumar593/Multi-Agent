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
    def start_project(
        self,
        goal: str,
        project_name: str = "VerdeBrew Landing Page",
        business_type: str = "website",
    ) -> ProjectModel:
        """CEO initiates the project and Manager creates 5 to 10 dependent tasks based on business model."""
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

        if business_type == "lead_research" or "lead" in goal.lower():
            tasks_spec = [
                {
                    "id": f"{proj_id}_t1",
                    "team_id": "team_mktg",
                    "title": "Define ICP & Lead Sourcing Criteria",
                    "spec": "Formulate Ideal Customer Profile (ICP), industry filters, and headcount bounds.",
                    "depends_on": [],
                },
                {
                    "id": f"{proj_id}_t2",
                    "team_id": "team_mktg",
                    "title": "Company Discovery & Market Prospecting",
                    "spec": "Gather verified target companies matching ICP criteria.",
                    "depends_on": [f"{proj_id}_t1"],
                },
                {
                    "id": f"{proj_id}_t3",
                    "team_id": "team_mktg",
                    "title": "Decision Maker & Contact Context Enrichment",
                    "spec": "Extract key stakeholder roles and value alignment context.",
                    "depends_on": [f"{proj_id}_t2"],
                },
                {
                    "id": f"{proj_id}_t4",
                    "team_id": "team_eng",
                    "title": "CSV Dataset Generation & Export",
                    "spec": "Generate structured leads.csv in the sandbox with verified records.",
                    "depends_on": [f"{proj_id}_t3"],
                },
                {
                    "id": f"{proj_id}_t5",
                    "team_id": "team_ops",
                    "title": "Human Approval for Client Delivery",
                    "spec": "Gate release behind human owner sign-off via Human Liaison.",
                    "depends_on": [f"{proj_id}_t4"],
                },
            ]
        elif business_type == "data_report" or "report" in goal.lower() or "data" in goal.lower():
            tasks_spec = [
                {
                    "id": f"{proj_id}_t1",
                    "team_id": "team_mktg",
                    "title": "Data Ingestion & Statistical Analysis",
                    "spec": "Aggregate performance and market metrics into statistical summary.",
                    "depends_on": [],
                },
                {
                    "id": f"{proj_id}_t2",
                    "team_id": "team_eng",
                    "title": "Generate Analytical Metrics Dataset",
                    "spec": "Compile and output structured metrics.json and dataset in sandbox.",
                    "depends_on": [f"{proj_id}_t1"],
                },
                {
                    "id": f"{proj_id}_t3",
                    "team_id": "team_mktg",
                    "title": "Draft Executive Data Report & Insights",
                    "spec": "Produce detailed executive briefing data_report.md with KPIs and findings.",
                    "depends_on": [f"{proj_id}_t2"],
                },
                {
                    "id": f"{proj_id}_t4",
                    "team_id": "team_eng",
                    "title": "Compile Analytical PDF Briefing",
                    "spec": "Export data_report.md to client-ready executive data_report.pdf.",
                    "depends_on": [f"{proj_id}_t3"],
                },
                {
                    "id": f"{proj_id}_t5",
                    "team_id": "team_ops",
                    "title": "Human Approval for Executive Release",
                    "spec": "Gate executive report release behind human owner sign-off via Liaison.",
                    "depends_on": [f"{proj_id}_t4"],
                },
            ]
        elif business_type == "seo_content" or "seo" in goal.lower() or "article" in goal.lower():
            tasks_spec = [
                {
                    "id": f"{proj_id}_t1",
                    "team_id": "team_mktg",
                    "title": "Keyword Research & Search Intent Mapping",
                    "spec": "Extract high-intent search keywords and competitor content gaps.",
                    "depends_on": [],
                },
                {
                    "id": f"{proj_id}_t2",
                    "team_id": "team_mktg",
                    "title": "Article Outline & Content Architecture",
                    "spec": "Draft comprehensive H2/H3 semantic outline and key takeaways.",
                    "depends_on": [f"{proj_id}_t1"],
                },
                {
                    "id": f"{proj_id}_t3",
                    "team_id": "team_mktg",
                    "title": "Draft Publication-Ready SEO Article",
                    "spec": "Write complete Markdown article.md with engaging prose and headers.",
                    "depends_on": [f"{proj_id}_t2"],
                },
                {
                    "id": f"{proj_id}_t4",
                    "team_id": "team_eng",
                    "title": "Technical SEO & Readability Validation",
                    "spec": "Validate markdown structure, keyword density, and schema metadata.",
                    "depends_on": [f"{proj_id}_t3"],
                },
                {
                    "id": f"{proj_id}_t5",
                    "team_id": "team_ops",
                    "title": "Human Approval for Live Publishing",
                    "spec": "Gate release behind human owner sign-off via Human Liaison.",
                    "depends_on": [f"{proj_id}_t4"],
                },
            ]
        else:
            # Default: Website / Landing page agency
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

        # Loop 1: Parallel Task Execution Fan-Out
        executed_tasks = []
        idle_agents = (
            self.db.query(AgentModel)
            .filter(AgentModel.status.in_(["alive", "idle"]))
            .all()
        )

        # Separate operational agents from workers
        workers = [a for a in idle_agents if a.role not in ("reviewer", "ceo", "hr", "monitor")]

        # Claim tasks atomically for all available idle workers
        worker_task_pairs = []
        for worker in workers:
            claimed = self.runner.claim_task_atomically(worker.id)
            if claimed:
                worker_task_pairs.append((worker.id, claimed))

        # Parallel fan-out execution using ThreadPoolExecutor
        if worker_task_pairs:
            from concurrent.futures import ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=min(5, len(worker_task_pairs))) as executor:
                futures = [
                    executor.submit(self.runner.execute_task, w_id, task)
                    for w_id, task in worker_task_pairs
                ]
                for f in futures:
                    res = f.result()
                    if res.get("task_id"):
                        executed_tasks.append(res["task_id"])

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
        task_title = task.title if task else ""

        # Persist human decision into LiaisonMemory so no agent repeats the question
        from backend.company.memory import LiaisonMemory
        memory = LiaisonMemory()
        memory.record_decision(
            task_title=task_title,
            question_or_details=blocker.details or "",
            human_decision=action,
            blocker_id=blocker.id,
        )

        if task:
            if action.lower() in ("approve", "approve & publish"):
                task.status = "done"
                task.result = json.dumps({"human_approval": "Approved by human owner for public release."})
            else:
                task.status = "todo"  # Send back for revision

        self.db.commit()
        return {"status": "resolved", "blocker_id": blocker_id, "action": action}
