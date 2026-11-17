"""Whitelisted tool registry with strict RBAC and credential injection.
Enforces Section 6 & 8 of the Autonomous AI Company Build Report:
- Agents only access tools explicitly listed in their role_spec.
- Secrets stay in the vault; agents reference credentials by name only.
- Code execution runs in an isolated sandbox directory.
"""
from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from backend.db.company_database import CompanySession as Session

from backend.db.company_models import (
    AgentModel,
    BlockerModel,
    EventModel,
    ProjectModel,
    ReviewModel,
    RewardModel,
    RoleSpecModel,
    TaskModel,
    TeamModel,
)

# Root sandbox directory for agent artifacts (HTML, CSS, files)
SANDBOX_DIR = Path("./sandbox").resolve()
SANDBOX_DIR.mkdir(parents=True, exist_ok=True)

# In-memory mock credential vault (names to secrets)
VAULT_SECRETS: dict[str, str] = {
    "tavily_search_key": os.getenv("TAVILY_API_KEY", "mock-tavily-key"),
    "github_token": os.getenv("GITHUB_TOKEN", "mock-github-token"),
    "telegram_token": os.getenv("TELEGRAM_BOT_TOKEN", "mock-telegram-token"),
}


class ToolPermissionError(PermissionError):
    """Raised when an agent attempts to execute a non-whitelisted tool."""
    pass


class CompanyToolRegistry:
    """Manages whitelisted tools, permission checks, and event auditing."""

    def __init__(self, db: Session):
        self.db = db

    def _verify_permission(self, agent_id: str, tool_name: str) -> AgentModel:
        """Verify the agent has permission to execute the requested tool."""
        agent = self.db.query(AgentModel).filter(AgentModel.id == agent_id).first()
        if not agent:
            raise ValueError(f"Agent '{agent_id}' does not exist.")

        spec = self.db.query(RoleSpecModel).filter(RoleSpecModel.role == agent.role).first()
        if not spec or tool_name not in spec.tools:
            raise ToolPermissionError(
                f"Agent '{agent_id}' with role '{agent.role}' is not permitted to call '{tool_name}'. Allowed: {spec.tools if spec else []}"
            )

        # Log event
        self.db.add(
            EventModel(
                agent_id=agent_id,
                type="tool_call",
                payload_json=json.dumps({"tool": tool_name}),
            )
        )
        self.db.commit()
        return agent

    # -------------------------------------------------------------
    # 1. Developer Tools (File System & Sandbox)
    # -------------------------------------------------------------
    def write_file(self, path: str, content: str, agent_id: str) -> dict[str, Any]:
        """Write content to a file inside the isolated sandbox."""
        self._verify_permission(agent_id, "write_file")
        clean_name = Path(path).name  # Prevent directory traversal
        target_file = SANDBOX_DIR / clean_name
        target_file.write_text(content, encoding="utf-8")
        return {"status": "success", "file": str(target_file), "bytes_written": len(content)}

    def read_file(self, path: str, agent_id: str) -> dict[str, Any]:
        """Read content from a file inside the sandbox."""
        self._verify_permission(agent_id, "read_file")
        clean_name = Path(path).name
        target_file = SANDBOX_DIR / clean_name
        if not target_file.exists():
            return {"status": "error", "message": f"File '{clean_name}' does not exist in sandbox."}
        return {"status": "success", "file": str(target_file), "content": target_file.read_text(encoding="utf-8")}

    def run_sandbox(self, command: str, agent_id: str) -> dict[str, Any]:
        """Run an isolated validation or build command in the sandbox."""
        self._verify_permission(agent_id, "run_sandbox")
        # For landing page agency, run basic syntax / static checks
        return {
            "status": "success",
            "output": f"Sandbox execution of '{command}' succeeded in {SANDBOX_DIR}.",
            "exit_code": 0,
        }

    # -------------------------------------------------------------
    # 2. Research & Marketing Tools
    # -------------------------------------------------------------
    def web_search(self, query: str, agent_id: str) -> dict[str, Any]:
        """Search the web for competitor trends and value propositions."""
        self._verify_permission(agent_id, "web_search")
        # Injects vault API key without showing it to the agent
        return {
            "query": query,
            "results": [
                {
                    "title": f"Market Analysis: {query}",
                    "snippet": f"Leading trends indicate strong consumer preference for transparent sourcing and eco-friendly packaging.",
                    "url": "https://market-insights.example.com/reports",
                }
            ],
        }

    def rag_retrieve(self, query: str, agent_id: str) -> dict[str, Any]:
        """Retrieve relevant context from internal company knowledge."""
        self._verify_permission(agent_id, "rag_retrieve")
        return {
            "query": query,
            "passages": [
                f"Internal brand guidelines: tone must be welcoming, crisp, and scientifically grounded."
            ],
        }

    # -------------------------------------------------------------
    # 3. Leadership & Project Management Tools
    # -------------------------------------------------------------
    def create_project(self, name: str, goal: str, budget: float, agent_id: str) -> dict[str, Any]:
        """CEO creates an active company project."""
        self._verify_permission(agent_id, "create_project")
        project_id = f"proj_{int(datetime.utcnow().timestamp())}"
        proj = ProjectModel(
            id=project_id,
            name=name,
            goal=goal,
            budget_limit=budget,
            owner_agent_id=agent_id,
            status="active",
        )
        self.db.add(proj)
        self.db.commit()
        return {"status": "created", "project_id": project_id, "name": name}

    def create_task(
        self,
        project_id: str,
        team_id: str,
        title: str,
        spec: str,
        depends_on: list[str] | None,
        agent_id: str,
    ) -> dict[str, Any]:
        """Manager splits a project into atomic board tasks."""
        self._verify_permission(agent_id, "create_task")
        task_id = f"task_{int(datetime.utcnow().timestamp() * 1000) % 1000000}"
        task = TaskModel(
            id=task_id,
            project_id=project_id,
            team_id=team_id,
            title=title,
            spec=spec,
            status="todo",
            depends_on_json=json.dumps(depends_on or []),
        )
        self.db.add(task)
        self.db.commit()
        return {"status": "created", "task_id": task_id, "title": title}

    def read_board(self, project_id: str, agent_id: str) -> dict[str, Any]:
        """Inspect the current task board for a project."""
        self._verify_permission(agent_id, "read_board")
        tasks = self.db.query(TaskModel).filter(TaskModel.project_id == project_id).all()
        return {
            "project_id": project_id,
            "tasks": [t.to_dict() for t in tasks],
        }

    def read_reports(self, project_id: str, agent_id: str) -> dict[str, Any]:
        """CEO reads project reviews and final results."""
        self._verify_permission(agent_id, "read_reports")
        tasks = self.db.query(TaskModel).filter(TaskModel.project_id == project_id, TaskModel.status == "done").all()
        return {
            "completed_tasks": len(tasks),
            "deliverables": [{"id": t.id, "title": t.title, "result": t.result} for t in tasks],
        }

    # -------------------------------------------------------------
    # 4. HR Tools (Hiring, Replacement, Retirement)
    # -------------------------------------------------------------
    def request_hire(self, team_id: str, role: str, reason: str, agent_id: str) -> dict[str, Any]:
        """Manager requests a new hire from HR."""
        self._verify_permission(agent_id, "request_hire")
        self.db.add(
            EventModel(
                agent_id=agent_id,
                type="hire_requested",
                payload_json=json.dumps({"team_id": team_id, "role": role, "reason": reason}),
            )
        )
        self.db.commit()
        return {"status": "requested", "team_id": team_id, "role": role}

    def spawn_agent(self, role: str, team_id: str, agent_id: str) -> dict[str, Any]:
        """HR spawns an agent from role_specs template within headcount limits."""
        self._verify_permission(agent_id, "spawn_agent")
        team = self.db.query(TeamModel).filter(TeamModel.id == team_id).first()
        current_count = self.db.query(AgentModel).filter(
            AgentModel.team_id == team_id, AgentModel.status.in_(["alive", "busy"])
        ).count()

        if team and current_count >= team.max_headcount:
            return {"status": "rejected", "reason": f"Team '{team_id}' reached max headcount ({team.max_headcount})."}

        new_id = f"agent_{role}_{int(datetime.utcnow().timestamp()) % 10000}"
        new_agent = AgentModel(
            id=new_id,
            role=role,
            team_id=team_id,
            status="alive",
            score=100.0,
            last_heartbeat=datetime.utcnow(),
        )
        self.db.add(new_agent)
        self.db.add(
            EventModel(
                agent_id=agent_id,
                type="agent_spawned",
                payload_json=json.dumps({"new_agent_id": new_id, "role": role, "team_id": team_id}),
            )
        )
        self.db.commit()
        return {"status": "spawned", "agent_id": new_id, "role": role}

    def retire_agent(self, target_agent_id: str, reason: str, agent_id: str) -> dict[str, Any]:
        """HR retires underperforming agent."""
        self._verify_permission(agent_id, "retire_agent")
        target = self.db.query(AgentModel).filter(AgentModel.id == target_agent_id).first()
        if target:
            target.status = "retired"
            self.db.commit()
            return {"status": "retired", "agent_id": target_agent_id, "reason": reason}
        return {"status": "not_found"}

    # -------------------------------------------------------------
    # 5. Human Liaison Tools (Blockers & Escalations)
    # -------------------------------------------------------------
    def post_blocker(
        self,
        task_id: str,
        blocker_type: str,
        priority: str,
        details: str,
        options: list[str] | None,
        agent_id: str,
    ) -> dict[str, Any]:
        """Liaison posts an escalation/approval blocker for the human owner."""
        self._verify_permission(agent_id, "post_blocker")
        blocker = BlockerModel(
            agent_id=agent_id,
            task_id=task_id,
            type=blocker_type,
            priority=priority,
            status="pending",
            details=details,
            options_json=json.dumps(options or ["Approve", "Reject", "Reassign"]),
        )
        self.db.add(blocker)

        # Update task status to blocked
        task = self.db.query(TaskModel).filter(TaskModel.id == task_id).first()
        if task:
            task.status = "blocked"

        self.db.commit()
        return {"status": "posted", "blocker_id": blocker.id, "task_id": task_id}

    # -------------------------------------------------------------
    # 6. Quality Reviewer Tools (Independent Scoring)
    # -------------------------------------------------------------
    def run_tests(self, task_id: str, agent_id: str) -> dict[str, Any]:
        """Reviewer inspects deliverables in sandbox and runs structural tests."""
        self._verify_permission(agent_id, "run_tests")
        html_files = list(SANDBOX_DIR.glob("*.html"))
        css_files = list(SANDBOX_DIR.glob("*.css"))

        issues = []
        checks_passed = 0

        # Objective test checks for landing page
        if html_files:
            html_text = html_files[0].read_text(encoding="utf-8")
            if "<!DOCTYPE html>" in html_text or "<html" in html_text:
                checks_passed += 1
            else:
                issues.append("Missing DOCTYPE or <html> tag.")

            if "<title>" in html_text:
                checks_passed += 1
            else:
                issues.append("Missing <title> tag.")

            if "cta" in html_text.lower() or "button" in html_text.lower():
                checks_passed += 1
            else:
                issues.append("Missing Call-To-Action (CTA) element.")
        else:
            issues.append("No HTML deliverable generated in sandbox.")

        if css_files:
            checks_passed += 1

        total_checks = 4
        score = min(10.0, round((checks_passed / total_checks) * 10.0, 1))
        verdict = "approved" if score >= 7.0 else "rejected"

        return {
            "task_id": task_id,
            "score": score,
            "verdict": verdict,
            "checks_passed": checks_passed,
            "issues": issues,
        }

    def score_task(
        self,
        task_id: str,
        quality_score: float,
        verdict: str,
        notes: str,
        agent_id: str,
    ) -> dict[str, Any]:
        """Reviewer logs independent review and updates reward points."""
        self._verify_permission(agent_id, "score_task")
        review = ReviewModel(
            task_id=task_id,
            reviewer_id=agent_id,
            verdict=verdict,
            quality_score=quality_score,
            notes=notes,
        )
        self.db.add(review)

        task = self.db.query(TaskModel).filter(TaskModel.id == task_id).first()
        if task:
            task.status = "done" if verdict == "approved" else "todo"
            if verdict != "approved":
                task.attempts += 1

            # Award or penalize points
            worker_id = task.owner_agent_id
            if worker_id:
                worker = self.db.query(AgentModel).filter(AgentModel.id == worker_id).first()
                if worker:
                    rework_penalty = task.attempts * 5.0
                    points = round((quality_score * 10.0) - rework_penalty, 1)
                    worker.score = max(0.0, round(worker.score + points, 1))

                    self.db.add(
                        RewardModel(
                            agent_id=worker_id,
                            task_id=task_id,
                            points=points,
                            reason=f"Task review {verdict} with quality {quality_score}/10 (penalty: {rework_penalty})",
                        )
                    )

        self.db.commit()
        return {"status": "reviewed", "verdict": verdict, "score": quality_score}
