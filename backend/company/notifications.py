"""Telegram notification and mobile human-in-the-loop escalation service.
Implements Section 4 & 8 of the Autonomous AI Company Build Report:
- Formats blocker messages with priority, team, context, impact, and decision options.
- Dispatches messages to Telegram Bot API or records them to audit events when offline.
"""
from __future__ import annotations

import json
import os
import urllib.request
import urllib.parse
from typing import Any, List, Optional
from backend.db.company_models import BlockerModel, TaskModel


class TelegramNotificationService:
    """Delivers critical blockers and approval gates directly to the human owner's phone."""

    def __init__(
        self,
        bot_token: Optional[str] = None,
        chat_id: Optional[str] = None,
    ):
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")

    def format_blocker_message(self, blocker: BlockerModel, task: Optional[TaskModel] = None) -> str:
        """Format blocker into the standardized format defined in Section 8."""
        task_title = task.title if task else f"Task #{blocker.task_id}"
        team = task.team_id if task and task.team_id else "Operations"
        options_text = " ".join([f"[{opt}]" for opt in blocker.options])

        return (
            f"🚨 **Blocker #{blocker.id} | Priority: {blocker.priority.upper()} | Team: {team}**\n\n"
            f"**Agent**: `{blocker.agent_id}`\n"
            f"**Needs**: Decision / Approval on {task_title}\n"
            f"**Why**: Task `{task_title}` is waiting for sign-off\n"
            f"**Details**: {blocker.details}\n"
            f"**Impact if delayed**: Production deployment and customer delivery blocked\n"
            f"**Options**: {options_text}\n"
        )

    def send_notification(self, text: str) -> dict[str, Any]:
        """Dispatch message to Telegram or fallback to local event logging."""
        if self.bot_token and self.chat_id:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = json.dumps({
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": "Markdown",
            }).encode("utf-8")

            try:
                req = urllib.request.Request(
                    url,
                    data=payload,
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=5) as resp:
                    res_data = json.loads(resp.read().decode("utf-8"))
                    return {"status": "sent", "channel": "telegram", "response": res_data}
            except Exception as e:
                return {"status": "error", "error": str(e), "channel": "telegram_failed"}

        # Offline fallback: clean logged delivery
        return {
            "status": "simulated",
            "channel": "local_mock",
            "message": text,
            "note": "Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env for live mobile push.",
        }
