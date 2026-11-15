"""Agent progress visualization component."""
import streamlit as st

def create_agent_stepper():
    """Create live progress tracker container for multi-agent workflow."""
    st.subheader("⚡ Agent Orchestration Progress")
    progress_bar = st.progress(0)
    status_text = st.empty()

    def update_progress(agent_name: str, message: str):
        step_weights = {
            "planner": 20,
            "search": 45,
            "analyst": 65,
            "writer": 85,
            "critic": 95,
            "complete": 100,
        }
        progress_bar.progress(step_weights.get(agent_name, 50))
        status_text.markdown(f"**Agent [{agent_name.upper()}]**: {message}")

    return update_progress
