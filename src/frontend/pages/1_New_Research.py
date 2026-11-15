"""New Research Query Page."""
import streamlit as st
from src.frontend.components import create_agent_stepper, render_report_view, render_sidebar

st.set_page_config(page_title="New Research | AI Research Agent", page_icon="🚀", layout="wide")
st.title("🚀 Launch Deep Research")
st.caption("Submit an open-ended research question to activate the collaborative multi-agent engine.")

cfg = render_sidebar()

topic = st.text_input(
    "Enter your research topic:",
    placeholder="e.g. Research the impact of generative AI on software engineering jobs between 2023 and 2026",
)

if st.button("Start Research Job", type="primary", use_container_width=True) and topic.strip():
    progress_callback = create_agent_stepper()

    from src.backend.api.app import workflow

    with st.spinner("Multi-agent team active..."):
        state = workflow.run_sync(
            topic=topic,
            scope=cfg["scope"],
            max_iterations=cfg["max_iters"],
            progress_callback=progress_callback,
        )

    draft = state.get("draft_report")
    critic = state.get("critic_feedback")
    evidence = state.get("evidence", [])

    if draft:
        render_report_view(draft, critic, evidence)
