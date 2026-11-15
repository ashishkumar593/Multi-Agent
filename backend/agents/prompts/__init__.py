"""Prompt templates for all agents."""
from backend.agents.prompts.planner_prompts import PLANNER_SYSTEM_PROMPT
from backend.agents.prompts.analyst_prompts import ANALYST_SYSTEM_PROMPT
from backend.agents.prompts.writer_prompts import WRITER_SYSTEM_PROMPT
from backend.agents.prompts.critic_prompts import CRITIC_SYSTEM_PROMPT

__all__ = [
    "PLANNER_SYSTEM_PROMPT",
    "ANALYST_SYSTEM_PROMPT",
    "WRITER_SYSTEM_PROMPT",
    "CRITIC_SYSTEM_PROMPT",
]
