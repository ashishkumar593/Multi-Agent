"""Conditional edge routing for LangGraph multi-agent research workflow."""
from typing import Literal
from src.backend.agents.state import ResearchState

def should_continue_after_critic(state: ResearchState) -> Literal["search", "writer", "end"]:
    """Determine next workflow transition based on Critic feedback and iteration caps."""
    feedback = state.get("critic_feedback")
    iteration = state.get("iteration_count", 0)
    max_iters = state.get("max_iterations", 2)

    if feedback and feedback.approved:
        return "end"

    if iteration >= max_iters:
        return "end"

    # If unsupported claims or missing evidence queries exist, perform additional targeted search
    if feedback and feedback.unsupported_claims:
        return "search"

    return "writer"
