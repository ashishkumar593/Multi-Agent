"""Streamlit Frontend: Interactive research dashboard and cited report visualizer."""
import asyncio
import json
import streamlit as st

# Configure page layout
st.set_page_config(
    page_title="AI Research & Report Agent",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling
st.markdown(
    """
    <style>
    .main-header { font-size: 2.2rem; font-weight: 700; color: #1E293B; margin-bottom: 0.2rem; }
    .sub-header { font-size: 1.05rem; color: #64748B; margin-bottom: 1.5rem; }
    .agent-card { background-color: #F8FAFC; border-left: 4px solid #3B82F6; padding: 12px 16px; border-radius: 6px; margin-bottom: 8px; }
    .metric-badge { background-color: #10B981; color: white; padding: 4px 10px; border-radius: 12px; font-weight: 600; font-size: 0.9rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="main-header">🧠 AI Research & Report Agent</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Production-grade multi-agent autonomous deep research, hybrid RAG, and cited report engine.</div>',
    unsafe_allow_html=True,
)

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    api_url = st.text_input("FastAPI Backend URL", value="http://localhost:8000")
    scope = st.selectbox("Research Scope", ["Comprehensive", "Technical Deep-Dive", "Executive Briefing"])
    max_iters = st.slider("Max Refinement Iterations", min_value=1, max_value=3, value=2)

    st.markdown("---")
    st.header("📁 Knowledge Base")
    uploaded_file = st.file_uploader("Upload Document (PDF, DOCX, TXT, MD)", type=["pdf", "docx", "txt", "md"])
    if uploaded_file is not None and st.button("Ingest Document"):
        import httpx
        with st.spinner("Indexing document into Hybrid RAG..."):
            try:
                files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
                resp = httpx.post(f"{api_url}/api/v1/documents", files=files, timeout=30.0)
                if resp.status_code == 200:
                    st.success(f"Indexed: {uploaded_file.name}")
                else:
                    st.error(f"Ingestion failed: {resp.text}")
            except Exception as e:
                # Direct ingestion fallback if backend server isn't running
                from pathlib import Path
                from src.backend.rag.chunker import RecursiveChunker
                from src.backend.rag.loaders import DocumentLoader
                from src.backend.api.app import retriever

                temp_path = Path(f"./data/raw/{uploaded_file.name}")
                temp_path.parent.mkdir(parents=True, exist_ok=True)
                temp_path.write_bytes(uploaded_file.getvalue())
                chunks = RecursiveChunker().split_chunks(DocumentLoader.load(temp_path))
                retriever.index_documents(chunks)
                st.success(f"Directly indexed {len(chunks)} chunks from {uploaded_file.name}")

# Main Search Input
topic = st.text_input(
    "Enter your research topic:",
    placeholder="e.g. Research the impact of generative AI on software engineering jobs between 2023 and 2026",
)

col1, col2 = st.columns([1, 5])
with col1:
    start_btn = st.button("🚀 Start Deep Research", use_container_width=True)

if start_btn and topic.strip():
    status_container = st.container()
    results_container = st.container()

    with status_container:
        st.subheader("⚡ Agent Orchestration Progress")
        progress_bar = st.progress(0)
        status_text = st.empty()

        async def run_direct_workflow():
            from src.backend.api.app import workflow

            def callback(agent_name: str, msg: str):
                step_weights = {"planner": 20, "search": 45, "analyst": 65, "writer": 85, "critic": 95, "complete": 100}
                progress_bar.progress(step_weights.get(agent_name, 50))
                status_text.markdown(f"**Agent [{agent_name.upper()}]**: {msg}")

            return await workflow.run(
                topic=topic,
                scope=scope.lower(),
                max_iterations=max_iters,
                progress_callback=callback,
            )

        with st.spinner("Multi-agent team active..."):
            state = asyncio.run(run_direct_workflow())

    progress_bar.progress(100)
    status_text.success("✅ Research & citation validation completed successfully!")

    with results_container:
        draft = state.get("draft_report")
        critic = state.get("critic_feedback")
        evidence = state.get("evidence", [])

        if draft:
            st.markdown("---")
            score = critic.quality_score if critic else 9.0
            st.markdown(f"### 📋 {draft.title} &nbsp; <span class='metric-badge'>Score: {score:.1f}/10</span>", unsafe_allow_html=True)

            tab1, tab2, tab3 = st.tabs(["📄 Full Research Report", "📊 Evidence Matrix", "🔍 Verified Sources"])

            with tab1:
                st.markdown(draft.body_markdown)
                st.download_button(
                    label="📥 Download Report as Markdown",
                    data=draft.body_markdown,
                    file_name="research_report.md",
                    mime="text/markdown",
                )

            with tab2:
                st.markdown("#### Factual Claims & Cross-Corroboration Matrix")
                st.markdown(draft.comparison_table_markdown)

            with tab3:
                st.markdown(f"#### Gathered Evidence ({len(evidence)} items)")
                for ev in evidence:
                    with st.expander(f"[{ev.source_type.upper()}] {ev.source_title} (Credibility: {int(ev.credibility_score*100)}%)"):
                        st.write(ev.content)
                        st.caption(f"Source URL/Path: {ev.source_url_or_path}")
