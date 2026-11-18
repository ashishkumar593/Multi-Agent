"""SQLite-backed zero-dependency database engine for the Autonomous AI Company.
Implements the 11-table schema with full ACID guarantees, identity map tracking, and atomic transactions.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Generator, Generic, List, Optional, Type, TypeVar

from backend.db.company_models import (
    AgentModel,
    BlockerModel,
    BudgetLedgerModel,
    CredentialRegistryModel,
    EventModel,
    ProjectModel,
    ReviewModel,
    RewardModel,
    RoleSpecModel,
    TaskModel,
    TeamModel,
)

T = TypeVar("T")
DEFAULT_DB_FILE = Path("./company.db").resolve()


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Query(Generic[T]):
    """Chainable query builder over in-memory / SQLite records."""

    def __init__(self, session: "CompanySession", model_cls: Type[T]):
        self.session = session
        self.model_cls = model_cls
        self.predicates: list[Callable[[T], bool]] = []
        self._order_by_fn: Optional[Callable[[T], Any]] = None
        self._reverse: bool = False

    def filter(self, *predicates: Any) -> "Query[T]":
        for pred in predicates:
            if callable(pred):
                self.predicates.append(pred)
        return self

    def order_by(self, key_fn: Any, reverse: bool = False) -> "Query[T]":
        if callable(key_fn):
            self._order_by_fn = key_fn
            self._reverse = reverse
        return self

    def all(self) -> list[T]:
        items = self.session.get_all(self.model_cls)
        for pred in self.predicates:
            items = [item for item in items if pred(item)]
        if self._order_by_fn:
            items.sort(key=self._order_by_fn, reverse=self._reverse)
        return items

    def first(self) -> Optional[T]:
        results = self.all()
        return results[0] if results else None

    def count(self) -> int:
        return len(self.all())


class CompanySession:
    """Manages transactional state, identity map, and persistence across the 11 tables."""

    def __init__(self, db_path: Path | str = DEFAULT_DB_FILE):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._ensure_tables()
        self._pending_adds: list[Any] = []
        self._identity_map: dict[tuple[Type, Any], Any] = {}

    def _ensure_tables(self) -> None:
        """Create the 11 tables if they do not exist."""
        cur = self.conn.cursor()
        cur.executescript("""
            CREATE TABLE IF NOT EXISTS agents (
                id TEXT PRIMARY KEY,
                role TEXT NOT NULL,
                team_id TEXT,
                spec_json TEXT,
                status TEXT,
                score REAL,
                last_heartbeat TEXT,
                created_at TEXT,
                replaced_by TEXT
            );

            CREATE TABLE IF NOT EXISTS role_specs (
                role TEXT PRIMARY KEY,
                system_prompt TEXT,
                tools_json TEXT,
                model_tier TEXT,
                max_steps INTEGER,
                token_budget INTEGER
            );

            CREATE TABLE IF NOT EXISTS teams (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                manager_agent_id TEXT,
                min_headcount INTEGER,
                max_headcount INTEGER
            );

            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                goal TEXT,
                status TEXT,
                budget_limit REAL,
                owner_agent_id TEXT,
                created_at TEXT
            );

            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                team_id TEXT,
                title TEXT NOT NULL,
                spec TEXT,
                status TEXT,
                owner_agent_id TEXT,
                attempts INTEGER,
                result TEXT,
                depends_on_json TEXT,
                created_at TEXT,
                updated_at TEXT
            );

            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT,
                agent_id TEXT,
                task_id TEXT,
                type TEXT NOT NULL,
                payload_json TEXT
            );

            CREATE TABLE IF NOT EXISTS budget_ledger (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT,
                agent_id TEXT,
                project_id TEXT,
                tokens INTEGER,
                cost REAL,
                tool_calls INTEGER
            );

            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL,
                reviewer_id TEXT,
                verdict TEXT,
                quality_score REAL,
                notes TEXT,
                created_at TEXT
            );

            CREATE TABLE IF NOT EXISTS rewards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT NOT NULL,
                task_id TEXT NOT NULL,
                points REAL,
                reason TEXT,
                ts TEXT
            );

            CREATE TABLE IF NOT EXISTS blockers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT NOT NULL,
                task_id TEXT NOT NULL,
                type TEXT,
                priority TEXT,
                status TEXT,
                details TEXT,
                options_json TEXT,
                created_at TEXT,
                resolved_at TEXT
            );

            CREATE TABLE IF NOT EXISTS credentials_registry (
                name TEXT PRIMARY KEY,
                scope TEXT,
                allowed_roles_json TEXT,
                vault_ref TEXT,
                last_used TEXT
            );
        """)
        self.conn.commit()

    def query(self, model_cls: Type[T]) -> Query[T]:
        return Query(self, model_cls)

    def add(self, item: Any) -> None:
        self._pending_adds.append(item)
        key = (type(item), getattr(item, "id", None) or getattr(item, "role", None))
        self._identity_map[key] = item

    def add_all(self, items: list[Any]) -> None:
        for it in items:
            self.add(it)

    def commit(self) -> None:
        """Persist all pending adds and tracked identity instances to SQLite."""
        cur = self.conn.cursor()
        saved_keys = set()
        
        for item in self._pending_adds:
            self._save_record(cur, item)
            key = (type(item), getattr(item, "id", None) or getattr(item, "role", None))
            saved_keys.add(key)
        self._pending_adds.clear()

        for key, item in list(self._identity_map.items()):
            if key not in saved_keys:
                self._save_record(cur, item)

        self.conn.commit()

    def refresh(self, item: Any) -> None:
        """Reload item attributes from SQLite."""
        cls = type(item)
        rec_id = getattr(item, "id", None) or getattr(item, "role", None)
        if rec_id is not None:
            loaded = self._query_single_from_db(cls, rec_id)
            if loaded:
                for k, v in loaded.__dict__.items():
                    setattr(item, k, v)
                self._identity_map[(cls, rec_id)] = item

    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> "CompanySession":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is None:
            self.commit()
        self.close()

    # -------------------------------------------------------------
    # Low-level Serialization & Deserialization
    # -------------------------------------------------------------
    def _save_record(self, cur: sqlite3.Cursor, item: Any) -> None:
        if isinstance(item, AgentModel):
            cur.execute("""
                INSERT OR REPLACE INTO agents (id, role, team_id, spec_json, status, score, last_heartbeat, created_at, replaced_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item.id, item.role, item.team_id, item.spec_json, item.status, item.score,
                item.last_heartbeat.isoformat() if isinstance(item.last_heartbeat, datetime) else str(item.last_heartbeat),
                item.created_at.isoformat() if isinstance(item.created_at, datetime) else str(item.created_at),
                item.replaced_by
            ))

        elif isinstance(item, RoleSpecModel):
            cur.execute("""
                INSERT OR REPLACE INTO role_specs (role, system_prompt, tools_json, model_tier, max_steps, token_budget)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (item.role, item.system_prompt, item.tools_json, item.model_tier, item.max_steps, item.token_budget))

        elif isinstance(item, TeamModel):
            cur.execute("""
                INSERT OR REPLACE INTO teams (id, name, manager_agent_id, min_headcount, max_headcount)
                VALUES (?, ?, ?, ?, ?)
            """, (item.id, item.name, item.manager_agent_id, item.min_headcount, item.max_headcount))

        elif isinstance(item, ProjectModel):
            cur.execute("""
                INSERT OR REPLACE INTO projects (id, name, goal, status, budget_limit, owner_agent_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                item.id, item.name, item.goal, item.status, item.budget_limit, item.owner_agent_id,
                item.created_at.isoformat() if isinstance(item.created_at, datetime) else str(item.created_at)
            ))

        elif isinstance(item, TaskModel):
            cur.execute("""
                INSERT OR REPLACE INTO tasks (id, project_id, team_id, title, spec, status, owner_agent_id, attempts, result, depends_on_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item.id, item.project_id, item.team_id, item.title, item.spec, item.status, item.owner_agent_id,
                item.attempts, item.result, item.depends_on_json,
                item.created_at.isoformat() if isinstance(item.created_at, datetime) else str(item.created_at),
                item.updated_at.isoformat() if isinstance(item.updated_at, datetime) else str(item.updated_at)
            ))

        elif isinstance(item, EventModel):
            cur.execute("""
                INSERT INTO events (ts, agent_id, task_id, type, payload_json)
                VALUES (?, ?, ?, ?, ?)
            """, (
                item.ts.isoformat() if isinstance(item.ts, datetime) else str(item.ts),
                item.agent_id, item.task_id, item.type, item.payload_json
            ))
            item.id = cur.lastrowid

        elif isinstance(item, BudgetLedgerModel):
            cur.execute("""
                INSERT INTO budget_ledger (ts, agent_id, project_id, tokens, cost, tool_calls)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                item.ts.isoformat() if isinstance(item.ts, datetime) else str(item.ts),
                item.agent_id, item.project_id, item.tokens, item.cost, item.tool_calls
            ))
            item.id = cur.lastrowid

        elif isinstance(item, ReviewModel):
            cur.execute("""
                INSERT INTO reviews (task_id, reviewer_id, verdict, quality_score, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                item.task_id, item.reviewer_id, item.verdict, item.quality_score, item.notes,
                item.created_at.isoformat() if isinstance(item.created_at, datetime) else str(item.created_at)
            ))
            item.id = cur.lastrowid

        elif isinstance(item, RewardModel):
            cur.execute("""
                INSERT INTO rewards (agent_id, task_id, points, reason, ts)
                VALUES (?, ?, ?, ?, ?)
            """, (
                item.agent_id, item.task_id, item.points, item.reason,
                item.ts.isoformat() if isinstance(item.ts, datetime) else str(item.ts)
            ))
            item.id = cur.lastrowid

        elif isinstance(item, BlockerModel):
            if item.id:
                cur.execute("""
                    UPDATE blockers SET status=?, details=?, options_json=?, resolved_at=? WHERE id=?
                """, (
                    item.status, item.details, item.options_json,
                    item.resolved_at.isoformat() if isinstance(item.resolved_at, datetime) else None,
                    item.id
                ))
            else:
                cur.execute("""
                    INSERT INTO blockers (agent_id, task_id, type, priority, status, details, options_json, created_at, resolved_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    item.agent_id, item.task_id, item.type, item.priority, item.status, item.details, item.options_json,
                    item.created_at.isoformat() if isinstance(item.created_at, datetime) else str(item.created_at),
                    item.resolved_at.isoformat() if isinstance(item.resolved_at, datetime) else None
                ))
                item.id = cur.lastrowid

    def get_all(self, model_cls: Type[T]) -> list[T]:
        """Fetch all records of model_cls from database with identity map tracking."""
        table_map = {
            AgentModel: ("agents", self._row_to_agent),
            RoleSpecModel: ("role_specs", self._row_to_role_spec),
            TeamModel: ("teams", self._row_to_team),
            ProjectModel: ("projects", self._row_to_project),
            TaskModel: ("tasks", self._row_to_task),
            EventModel: ("events", self._row_to_event),
            BudgetLedgerModel: ("budget_ledger", self._row_to_budget),
            ReviewModel: ("reviews", self._row_to_review),
            RewardModel: ("rewards", self._row_to_reward),
            BlockerModel: ("blockers", self._row_to_blocker),
        }
        if model_cls not in table_map:
            return []

        table_name, mapper = table_map[model_cls]
        cur = self.conn.cursor()
        rows = cur.execute(f"SELECT * FROM {table_name}").fetchall()
        results: list[T] = []

        for r in rows:
            obj = mapper(r)
            rec_id = getattr(obj, "id", None) or getattr(obj, "role", None)
            key = (model_cls, rec_id)
            if key in self._identity_map:
                results.append(self._identity_map[key])
            else:
                self._identity_map[key] = obj
                results.append(obj)

        return results

    def _query_single_from_db(self, model_cls: Type[T], record_id: Any) -> Optional[T]:
        table_map = {
            AgentModel: ("agents", "id", self._row_to_agent),
            RoleSpecModel: ("role_specs", "role", self._row_to_role_spec),
            TeamModel: ("teams", "id", self._row_to_team),
            ProjectModel: ("projects", "id", self._row_to_project),
            TaskModel: ("tasks", "id", self._row_to_task),
            ReviewModel: ("reviews", "id", self._row_to_review),
            RewardModel: ("rewards", "id", self._row_to_reward),
            BlockerModel: ("blockers", "id", self._row_to_blocker),
        }
        if model_cls not in table_map:
            return None
        table_name, id_col, mapper = table_map[model_cls]
        cur = self.conn.cursor()
        row = cur.execute(f"SELECT * FROM {table_name} WHERE {id_col} = ?", (record_id,)).fetchone()
        return mapper(row) if row else None

    # Row mappers
    def _parse_dt(self, s: Any) -> datetime:
        if not s:
            return utcnow()
        if isinstance(s, datetime):
            return s
        try:
            return datetime.fromisoformat(s)
        except Exception:
            return utcnow()

    def _row_to_agent(self, r: sqlite3.Row) -> AgentModel:
        return AgentModel(
            id=r["id"], role=r["role"], team_id=r["team_id"], spec_json=r["spec_json"],
            status=r["status"], score=r["score"], last_heartbeat=self._parse_dt(r["last_heartbeat"]),
            created_at=self._parse_dt(r["created_at"]), replaced_by=r["replaced_by"]
        )

    def _row_to_role_spec(self, r: sqlite3.Row) -> RoleSpecModel:
        return RoleSpecModel(
            role=r["role"], system_prompt=r["system_prompt"], tools_json=r["tools_json"],
            model_tier=r["model_tier"], max_steps=r["max_steps"], token_budget=r["token_budget"]
        )

    def _row_to_team(self, r: sqlite3.Row) -> TeamModel:
        return TeamModel(
            id=r["id"], name=r["name"], manager_agent_id=r["manager_agent_id"],
            min_headcount=r["min_headcount"], max_headcount=r["max_headcount"]
        )

    def _row_to_project(self, r: sqlite3.Row) -> ProjectModel:
        return ProjectModel(
            id=r["id"], name=r["name"], goal=r["goal"], status=r["status"],
            budget_limit=r["budget_limit"], owner_agent_id=r["owner_agent_id"],
            created_at=self._parse_dt(r["created_at"])
        )

    def _row_to_task(self, r: sqlite3.Row) -> TaskModel:
        return TaskModel(
            id=r["id"], project_id=r["project_id"], team_id=r["team_id"], title=r["title"],
            spec=r["spec"], status=r["status"], owner_agent_id=r["owner_agent_id"],
            attempts=r["attempts"], result=r["result"], depends_on_json=r["depends_on_json"],
            created_at=self._parse_dt(r["created_at"]), updated_at=self._parse_dt(r["updated_at"])
        )

    def _row_to_event(self, r: sqlite3.Row) -> EventModel:
        return EventModel(
            id=r["id"], ts=self._parse_dt(r["ts"]), agent_id=r["agent_id"],
            task_id=r["task_id"], type=r["type"], payload_json=r["payload_json"]
        )

    def _row_to_budget(self, r: sqlite3.Row) -> BudgetLedgerModel:
        return BudgetLedgerModel(
            id=r["id"], ts=self._parse_dt(r["ts"]), agent_id=r["agent_id"],
            project_id=r["project_id"], tokens=r["tokens"], cost=r["cost"], tool_calls=r["tool_calls"]
        )

    def _row_to_review(self, r: sqlite3.Row) -> ReviewModel:
        return ReviewModel(
            id=r["id"], task_id=r["task_id"], reviewer_id=r["reviewer_id"],
            verdict=r["verdict"], quality_score=r["quality_score"], notes=r["notes"],
            created_at=self._parse_dt(r["created_at"])
        )

    def _row_to_reward(self, r: sqlite3.Row) -> RewardModel:
        return RewardModel(
            id=r["id"], agent_id=r["agent_id"], task_id=r["task_id"],
            points=r["points"], reason=r["reason"], ts=self._parse_dt(r["ts"])
        )

    def _row_to_blocker(self, r: sqlite3.Row) -> BlockerModel:
        return BlockerModel(
            id=r["id"], agent_id=r["agent_id"], task_id=r["task_id"], type=r["type"],
            priority=r["priority"], status=r["status"], details=r["details"],
            options_json=r["options_json"], created_at=self._parse_dt(r["created_at"]),
            resolved_at=self._parse_dt(r["resolved_at"]) if r["resolved_at"] else None
        )


def SessionLocal() -> CompanySession:
    """Create a new database session."""
    return CompanySession()


def get_db() -> Generator[CompanySession, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


get_company_db = SessionLocal


def init_db(reset: bool = False) -> None:
    """Initialize SQLite database and seed baseline roles, teams, and agents."""
    if reset and DEFAULT_DB_FILE.exists():
        try:
            DEFAULT_DB_FILE.unlink()
        except Exception:
            pass

    with SessionLocal() as db:
        if db.query(RoleSpecModel).first() is not None:
            return

        # 1. Seed the 9 Role Specs
        specs = [
            RoleSpecModel("ceo", "You are the CEO.", json.dumps(["create_project", "read_board", "read_reports", "request_hire"]), "strong", 5, 15000),
            RoleSpecModel("manager", "You are the Project Manager.", json.dumps(["create_task", "assign_task", "request_hire", "read_board"]), "strong", 8, 12000),
            RoleSpecModel("hr", "You are HR.", json.dumps(["spawn_agent", "retire_agent", "read_registry", "read_budget"]), "fast", 5, 8000),
            RoleSpecModel("liaison", "You are the Human Liaison.", json.dumps(["post_blocker", "send_telegram", "read_blockers", "store_answer"]), "fast", 6, 8000),
            RoleSpecModel("developer", "You are the Full-Stack Developer.", json.dumps(["write_file", "run_sandbox", "read_file"]), "strong", 10, 20000),
            RoleSpecModel("marketing", "You are Marketing.", json.dumps(["web_search", "rag_retrieve", "write_file", "read_file"]), "fast", 6, 10000),
            RoleSpecModel("researcher", "You are Researcher.", json.dumps(["web_search", "rag_retrieve", "read_file"]), "fast", 6, 10000),
            RoleSpecModel("reviewer", "You are Reviewer.", json.dumps(["run_tests", "read_file", "score_task"]), "strong", 6, 10000),
            RoleSpecModel("monitor", "You are Monitor daemon.", json.dumps(["read_registry", "mark_dead", "trip_kill_switch"]), "none", 1, 0),
        ]
        db.add_all(specs)

        # 2. Seed Baseline Teams
        teams = [
            TeamModel("team_exec", "Executive Leadership", min_headcount=1, max_headcount=2),
            TeamModel("team_eng", "Engineering & Product", min_headcount=1, max_headcount=5),
            TeamModel("team_mktg", "Marketing & Content", min_headcount=1, max_headcount=4),
            TeamModel("team_ops", "Operations & Quality", min_headcount=1, max_headcount=3),
        ]
        db.add_all(teams)

        # 3. Seed Baseline Core Agents
        now = utcnow()
        agents = [
            AgentModel("agent_ceo", "ceo", "team_exec", score=100.0, last_heartbeat=now),
            AgentModel("agent_manager", "manager", "team_exec", score=100.0, last_heartbeat=now),
            AgentModel("agent_hr", "hr", "team_ops", score=100.0, last_heartbeat=now),
            AgentModel("agent_liaison", "liaison", "team_ops", score=100.0, last_heartbeat=now),
            AgentModel("agent_reviewer", "reviewer", "team_ops", score=100.0, last_heartbeat=now),
            AgentModel("agent_dev_01", "developer", "team_eng", score=100.0, last_heartbeat=now),
            AgentModel("agent_mktg_01", "marketing", "team_mktg", score=100.0, last_heartbeat=now),
            AgentModel("agent_res_01", "researcher", "team_mktg", score=100.0, last_heartbeat=now),
        ]
        db.add_all(agents)
        db.commit()
