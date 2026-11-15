"""Streamlit sidebar component."""
import streamlit as st

def render_sidebar():
    """Render unified sidebar settings and knowledge base manager."""
    with st.sidebar:
        st.header("⚙️ Configuration")
        api_url = st.text_input("FastAPI Backend URL", value="http://localhost:8000")
        scope = st.selectbox("Research Scope", ["Comprehensive", "Technical Deep-Dive", "Executive Briefing"])
        max_iters = st.slider("Max Refinement Iterations", min_value=1, max_value=3, value=2)

        st.markdown("---")
        st.header("📁 Knowledge Base")
        uploaded_file = st.file_uploader("Upload Document (PDF, DOCX, TXT, MD)", type=["pdf", "docx", "txt", "md"])
        if uploaded_file is not None and st.button("Ingest Document"):
            from pathlib import Path
            from src.backend.api.app import document_service

            temp_path = Path(f"./data/raw/{uploaded_file.name}")
            temp_path.parent.mkdir(parents=True, exist_ok=True)
            temp_path.write_bytes(uploaded_file.getvalue())

            record = document_service.process_file(temp_path)
            st.success(f"Indexed {record.get('chunks_count', 0)} chunks from {uploaded_file.name}")

        return {"api_url": api_url, "scope": scope.lower(), "max_iters": max_iters}
