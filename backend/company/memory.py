"""Persistent memory and blocker deduplication loop for the Human Liaison.
Enforces Section 8 of the Build Report:
'The Liaison saves your answers in the knowledge base so no agent asks the same question twice.'
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

DECISIONS_STORE_FILE = Path("./data/liaison_memory.json").resolve()
DECISIONS_STORE_FILE.parent.mkdir(parents=True, exist_ok=True)


class LiaisonMemory:
    """Manages persistent human decision records to avoid asking duplicate questions."""

    def __init__(self, filepath: Optional[Path] = None):
        self.filepath = filepath or DECISIONS_STORE_FILE
        self._ensure_storage()

    def _ensure_storage(self) -> None:
        if not self.filepath.exists():
            self.filepath.write_text(json.dumps([]), encoding="utf-8")

    def load_decisions(self) -> List[Dict[str, Any]]:
        try:
            return json.loads(self.filepath.read_text(encoding="utf-8"))
        except Exception:
            return []

    def record_decision(
        self,
        task_title: str,
        question_or_details: str,
        human_decision: str,
        blocker_id: int,
        resolved_by: str = "human_owner",
    ) -> Dict[str, Any]:
        """Save a human owner's resolution into persistent memory."""
        decisions = self.load_decisions()
        entry = {
            "blocker_id": blocker_id,
            "task_title": task_title,
            "query_summary": question_or_details.lower().strip(),
            "decision": human_decision,
            "resolved_by": resolved_by,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        decisions.append(entry)
        self.filepath.write_text(json.dumps(decisions, indent=2), encoding="utf-8")
        return entry

    def find_existing_decision(self, task_title: str, details: str) -> Optional[Dict[str, Any]]:
        """Check if an identical or near-identical question was previously decided."""
        decisions = self.load_decisions()
        norm_title = task_title.lower().strip()
        norm_details = details.lower().strip()

        for d in decisions:
            # Exact or substring match on task and key approval query
            if d.get("task_title", "").lower() == norm_title:
                return d
            if norm_details and norm_details in d.get("query_summary", ""):
                return d
        return None
