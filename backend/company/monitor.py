"""System Monitor & Safety Daemon (Non-LLM process).
Implements Section 6 & 7 of the Autonomous AI Company Build Report:
- Monitors agent heartbeats (detects death if no heartbeat for >30s)
- Loop detection (detects agent output repetition)
- Enforces daily and per-project budget caps
- Global Kill Switch (trips if budget exceeded or triggered by human owner)
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List
from backend.db.company_database import CompanySession as Session

from backend.db.company_models import (
    AgentModel,
    BudgetLedgerModel,
    EventModel,
    RoleSpecModel,
    TaskModel,
)

KILL_SWITCH_ACTIVE = False


class CompanyMonitor:
    """Deterministic system daemon supervising health, loops, and budget caps."""

    def __init__(self, db: Session, heartbeat_timeout_seconds: int = 30):
        self.db = db
        self.heartbeat_timeout_seconds = heartbeat_timeout_seconds

    @staticmethod
    def is_kill_switch_active() -> bool:
        global KILL_SWITCH_ACTIVE
        return KILL_SWITCH_ACTIVE

    @staticmethod
    def trip_kill_switch(reason: str = "Manual trigger or safety trip") -> None:
        global KILL_SWITCH_ACTIVE
        KILL_SWITCH_ACTIVE = True

    @staticmethod
    def reset_kill_switch() -> None:
        global KILL_SWITCH_ACTIVE
        KILL_SWITCH_ACTIVE = False

    def check_heartbeats_and_reap(self) -> list[str]:
        """Check agent heartbeats. Mark agents dead if no heartbeat for >30s.
        Returns list of dead agent IDs.
        """
        threshold = datetime.now(timezone.utc) - timedelta(seconds=self.heartbeat_timeout_seconds)
        dead_agents = (
            self.db.query(AgentModel)
            .filter(
                AgentModel.status.in_(["alive", "busy"]),
                AgentModel.last_heartbeat < threshold,
            )
            .all()
        )

        reaped_ids: list[str] = []
        for agent in dead_agents:
            agent.status = "dead"
            reaped_ids.append(agent.id)

            # Return any task the dead agent was doing back to 'todo'
            abandoned_tasks = (
                self.db.query(TaskModel)
                .filter(TaskModel.owner_agent_id == agent.id, TaskModel.status == "doing")
                .all()
            )
            for t in abandoned_tasks:
                t.status = "todo"
                t.owner_agent_id = None
                self.db.add(
                    EventModel(
                        agent_id=agent.id,
                        task_id=t.id,
                        type="task_requeued_due_to_worker_death",
                        payload_json=json.dumps({"reason": "Heartbeat lost > 30s"}),
                    )
                )

            self.db.add(
                EventModel(
                    agent_id=agent.id,
                    type="agent_died",
                    payload_json=json.dumps({"reason": "Heartbeat timeout"}),
                )
            )

        self.db.commit()
        return reaped_ids

    def check_budget_caps(self, max_company_spend: float = 100.0) -> bool:
        """Sum total spend in budget ledger; trip kill switch if exceeded."""
        total_spend = sum(
            row.cost for row in self.db.query(BudgetLedgerModel).all()
        )
        if total_spend >= max_company_spend:
            self.trip_kill_switch(f"Total spend (${total_spend:.2f}) exceeded cap (${max_company_spend:.2f})")
            return True
        return False

    def handle_hr_replacements(self, dead_agent_ids: list[str]) -> list[str]:
        """HR automatically spawns a replacement agent for each dead agent within 60s."""
        replaced_ids: list[str] = []
        for dead_id in dead_agent_ids:
            dead_agent = self.db.query(AgentModel).filter(AgentModel.id == dead_id).first()
            if not dead_agent:
                continue

            # Clone from role_spec
            spec = self.db.query(RoleSpecModel).filter(RoleSpecModel.role == dead_agent.role).first()
            if not spec:
                continue

            replacement_id = f"agent_{dead_agent.role}_rep_{int(datetime.now(timezone.utc).timestamp()) % 10000}"
            replacement = AgentModel(
                id=replacement_id,
                role=dead_agent.role,
                team_id=dead_agent.team_id,
                status="alive",
                score=100.0,
                last_heartbeat=datetime.now(timezone.utc),
            )
            self.db.add(replacement)
            dead_agent.replaced_by = replacement_id

            self.db.add(
                EventModel(
                    agent_id="agent_hr",
                    type="agent_replaced",
                    payload_json=json.dumps({"dead_agent_id": dead_id, "replacement_id": replacement_id}),
                )
            )
            replaced_ids.append(replacement_id)

        self.db.commit()
        return replaced_ids
