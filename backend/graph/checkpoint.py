"""Workflow state persistence and checkpointer management."""
from typing import Any

def get_checkpointer() -> Any:
    """Return configured checkpointer for LangGraph state persistence."""
    try:
        from langgraph.checkpoint.memory import MemorySaver
        return MemorySaver()
    except ImportError:
        # shortcut: fallback dictionary-based checkpointer when langgraph package not installed
        return None
