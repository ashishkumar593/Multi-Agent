"""Data models with SQLAlchemy-compatible column descriptors for zero-dependency execution.
Implements the 11-table schema specified in Section 5 of the Autonomous AI Company Build Report:
1. agents
2. role_specs
3. teams
4. projects
5. tasks
6. events
7. budget_ledger
8. reviews
9. rewards
10. blockers
11. credentials_registry
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Callable, List, Optional


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Predicate:
    """Wraps a filter condition and supports boolean operators (| and &)."""

    def __init__(self, fn: Callable[[Any], bool]):
        self.fn = fn

    def __call__(self, obj: Any) -> bool:
        return bool(self.fn(obj))

    def __or__(self, other: Any) -> "Predicate":
        return Predicate(lambda obj: self(obj) or (other(obj) if callable(other) else bool(other)))

    def __and__(self, other: Any) -> "Predicate":
        return Predicate(lambda obj: self(obj) and (other(obj) if callable(other) else bool(other)))

    def __invert__(self) -> "Predicate":
        return Predicate(lambda obj: not self(obj))


def _normalize_dt(val: Any) -> Any:
    if isinstance(val, datetime):
        return val.replace(tzinfo=None)
    return val


class Column:
    """Descriptor supporting SQLAlchemy-like filter syntax: (Model.field == val), in_(), <, >, is_()."""

    def __init__(self, name: str):
        self.name = name

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return instance.__dict__.get(self.name)

    def __set__(self, instance, value):
        instance.__dict__[self.name] = value

    def __eq__(self, other: Any) -> Predicate:
        return Predicate(lambda obj: getattr(obj, self.name) == other)

    def __ne__(self, other: Any) -> Predicate:
        return Predicate(lambda obj: getattr(obj, self.name) != other)

    def __lt__(self, other: Any) -> Predicate:
        norm_other = _normalize_dt(other)
        return Predicate(
            lambda obj: getattr(obj, self.name) is not None
            and _normalize_dt(getattr(obj, self.name)) < norm_other
        )

    def __gt__(self, other: Any) -> Predicate:
        norm_other = _normalize_dt(other)
        return Predicate(
            lambda obj: getattr(obj, self.name) is not None
            and _normalize_dt(getattr(obj, self.name)) > norm_other
        )

    def in_(self, values: Any) -> Predicate:
        return Predicate(lambda obj: getattr(obj, self.name) in values)

    def is_(self, other: Any) -> Predicate:
        return Predicate(lambda obj: getattr(obj, self.name) is other)

    def asc(self) -> Callable[[Any], Any]:
        return lambda obj: getattr(obj, self.name)

    def desc(self) -> Callable[[Any], Any]:
        return lambda obj: getattr(obj, self.name)


class AgentModel:
    """1. Registry of every agent and its health."""
    id = Column("id")
    role = Column("role")
    team_id = Column("team_id")
    spec_json = Column("spec_json")
    status = Column("status")
    score = Column("score")
    last_heartbeat = Column("last_heartbeat")
    created_at = Column("created_at")
    replaced_by = Column("replaced_by")

    def __init__(
        self,
        id: str,
        role: str,
        team_id: Optional[str] = None,
        spec_json: str = "{}",
        status: str = "alive",
        score: float = 100.0,
        last_heartbeat: Optional[datetime] = None,
        created_at: Optional[datetime] = None,
        replaced_by: Optional[str] = None,
    ):
        self.id = id
        self.role = role
        self.team_id = team_id
        self.spec_json = spec_json
        self.status = status
        self.score = score
        self.last_heartbeat = last_heartbeat or utcnow()
        self.created_at = created_at or utcnow()
        self.replaced_by = replaced_by

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "role": self.role,
            "team_id": self.team_id,
            "status": self.status,
            "score": round(self.score, 1),
            "last_heartbeat": self.last_heartbeat.isoformat() if isinstance(self.last_heartbeat, datetime) else str(self.last_heartbeat),
            "created_at": self.created_at.isoformat() if isinstance(self.created_at, datetime) else str(self.created_at),
            "replaced_by": self.replaced_by,
        }


class RoleSpecModel:
    """2. Templates HR clones to hire."""
    role = Column("role")
    system_prompt = Column("system_prompt")
    tools_json = Column("tools_json")
    model_tier = Column("model_tier")
    max_steps = Column("max_steps")
    token_budget = Column("token_budget")

    def __init__(
        self,
        role: str,
        system_prompt: str,
        tools_json: str = "[]",
        model_tier: str = "fast",
        max_steps: int = 8,
        token_budget: int = 10000,
    ):
        self.role = role
        self.system_prompt = system_prompt
        self.tools_json = tools_json
        self.model_tier = model_tier
        self.max_steps = max_steps
        self.token_budget = token_budget

    @property
    def tools(self) -> list[str]:
        return json.loads(self.tools_json) if self.tools_json else []


class TeamModel:
    """3. Company departments."""
    id = Column("id")
    name = Column("name")
    manager_agent_id = Column("manager_agent_id")
    min_headcount = Column("min_headcount")
    max_headcount = Column("max_headcount")

    def __init__(
        self,
        id: str,
        name: str,
        manager_agent_id: Optional[str] = None,
        min_headcount: int = 1,
        max_headcount: int = 5,
    ):
        self.id = id
        self.name = name
        self.manager_agent_id = manager_agent_id
        self.min_headcount = min_headcount
        self.max_headcount = max_headcount


class ProjectModel:
    """4. CEO-created projects."""
    id = Column("id")
    name = Column("name")
    goal = Column("goal")
    status = Column("status")
    budget_limit = Column("budget_limit")
    owner_agent_id = Column("owner_agent_id")
    created_at = Column("created_at")

    def __init__(
        self,
        id: str,
        name: str,
        goal: str,
        status: str = "active",
        budget_limit: float = 50.0,
        owner_agent_id: str = "agent_ceo",
        created_at: Optional[datetime] = None,
    ):
        self.id = id
        self.name = name
        self.goal = goal
        self.status = status
        self.budget_limit = budget_limit
        self.owner_agent_id = owner_agent_id
        self.created_at = created_at or utcnow()


class TaskModel:
    """5. The shared board."""
    id = Column("id")
    project_id = Column("project_id")
    team_id = Column("team_id")
    title = Column("title")
    spec = Column("spec")
    status = Column("status")
    owner_agent_id = Column("owner_agent_id")
    attempts = Column("attempts")
    result = Column("result")
    depends_on_json = Column("depends_on_json")
    created_at = Column("created_at")
    updated_at = Column("updated_at")

    def __init__(
        self,
        id: str,
        project_id: str,
        team_id: Optional[str],
        title: str,
        spec: str,
        status: str = "todo",
        owner_agent_id: Optional[str] = None,
        attempts: int = 0,
        result: Optional[str] = None,
        depends_on_json: str = "[]",
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        self.id = id
        self.project_id = project_id
        self.team_id = team_id
        self.title = title
        self.spec = spec
        self.status = status
        self.owner_agent_id = owner_agent_id
        self.attempts = attempts
        self.result = result
        self.depends_on_json = depends_on_json
        self.created_at = created_at or utcnow()
        self.updated_at = updated_at or utcnow()

    @property
    def depends_on(self) -> list[str]:
        return json.loads(self.depends_on_json) if self.depends_on_json else []

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "team_id": self.team_id,
            "title": self.title,
            "spec": self.spec,
            "status": self.status,
            "owner_agent_id": self.owner_agent_id,
            "attempts": self.attempts,
            "result": self.result,
            "depends_on": self.depends_on,
        }


class EventModel:
    """6. Append-only log for tracing and monitoring."""
    id = Column("id")
    ts = Column("ts")
    agent_id = Column("agent_id")
    task_id = Column("task_id")
    type = Column("type")
    payload_json = Column("payload_json")

    def __init__(
        self,
        agent_id: Optional[str],
        type: str,
        payload_json: str = "{}",
        task_id: Optional[str] = None,
        id: Optional[int] = None,
        ts: Optional[datetime] = None,
    ):
        self.agent_id = agent_id
        self.type = type
        self.payload_json = payload_json
        self.task_id = task_id
        self.id = id
        self.ts = ts or utcnow()


class BudgetLedgerModel:
    """7. Spend tracking for caps."""
    id = Column("id")
    ts = Column("ts")
    agent_id = Column("agent_id")
    project_id = Column("project_id")
    tokens = Column("tokens")
    cost = Column("cost")
    tool_calls = Column("tool_calls")

    def __init__(
        self,
        agent_id: str,
        project_id: str,
        tokens: int = 0,
        cost: float = 0.0,
        tool_calls: int = 0,
        id: Optional[int] = None,
        ts: Optional[datetime] = None,
    ):
        self.agent_id = agent_id
        self.project_id = project_id
        self.tokens = tokens
        self.cost = cost
        self.tool_calls = tool_calls
        self.id = id
        self.ts = ts or utcnow()


class ReviewModel:
    """8. Independent quality judgement."""
    id = Column("id")
    task_id = Column("task_id")
    reviewer_id = Column("reviewer_id")
    verdict = Column("verdict")
    quality_score = Column("quality_score")
    notes = Column("notes")
    created_at = Column("created_at")

    def __init__(
        self,
        task_id: str,
        reviewer_id: str,
        verdict: str,
        quality_score: float,
        notes: str = "",
        id: Optional[int] = None,
        created_at: Optional[datetime] = None,
    ):
        self.task_id = task_id
        self.reviewer_id = reviewer_id
        self.verdict = verdict
        self.quality_score = quality_score
        self.notes = notes
        self.id = id
        self.created_at = created_at or utcnow()


class RewardModel:
    """9. Point history."""
    id = Column("id")
    agent_id = Column("agent_id")
    task_id = Column("task_id")
    points = Column("points")
    reason = Column("reason")
    ts = Column("ts")

    def __init__(
        self,
        agent_id: str,
        task_id: str,
        points: float,
        reason: str,
        id: Optional[int] = None,
        ts: Optional[datetime] = None,
    ):
        self.agent_id = agent_id
        self.task_id = task_id
        self.points = points
        self.reason = reason
        self.id = id
        self.ts = ts or utcnow()


class BlockerModel:
    """10. Requests to the human owner."""
    id = Column("id")
    agent_id = Column("agent_id")
    task_id = Column("task_id")
    type = Column("type")
    priority = Column("priority")
    status = Column("status")
    details = Column("details")
    options_json = Column("options_json")
    created_at = Column("created_at")
    resolved_at = Column("resolved_at")

    def __init__(
        self,
        agent_id: str,
        task_id: str,
        type: str,
        priority: str = "medium",
        status: str = "pending",
        details: str = "",
        options_json: str = "[]",
        id: Optional[int] = None,
        created_at: Optional[datetime] = None,
        resolved_at: Optional[datetime] = None,
    ):
        self.agent_id = agent_id
        self.task_id = task_id
        self.type = type
        self.priority = priority
        self.status = status
        self.details = details
        self.options_json = options_json
        self.id = id
        self.created_at = created_at or utcnow()
        self.resolved_at = resolved_at

    @property
    def options(self) -> list[str]:
        return json.loads(self.options_json) if self.options_json else []


class CredentialRegistryModel:
    """11. Names and permissions only."""
    name = Column("name")
    scope = Column("scope")
    vault_ref = Column("vault_ref")
    allowed_roles_json = Column("allowed_roles_json")
    last_used = Column("last_used")

    def __init__(
        self,
        name: str,
        scope: str,
        vault_ref: str,
        allowed_roles_json: str = "[]",
        last_used: Optional[datetime] = None,
    ):
        self.name = name
        self.scope = scope
        self.vault_ref = vault_ref
        self.allowed_roles_json = allowed_roles_json
        self.last_used = last_used

    @property
    def allowed_roles(self) -> list[str]:
        return json.loads(self.allowed_roles_json) if self.allowed_roles_json else []
