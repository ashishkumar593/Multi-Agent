"""System Settings Page."""
import streamlit as st
from backend.core.config import settings

st.set_page_config(page_title="Settings | AI Research Agent", page_icon="⚙️", layout="wide")
st.title("⚙️ System & Engine Settings")

st.markdown("### Active Configuration Profiles")
col1, col2 = st.columns(2)
with col1:
    st.text_input("Application Environment", value=settings.app_env, disabled=True)
    st.text_input("Default Frontier Model", value=settings.default_model, disabled=True)
    st.text_input("Fast / Routing Model", value=settings.fast_model, disabled=True)
with col2:
    st.text_input("Embedding Model", value=settings.embedding_model, disabled=True)
    st.text_input("RAG Target Chunk Size (tokens)", value=str(settings.chunk_size), disabled=True)
    st.text_input("RAG Chunk Overlap (tokens)", value=str(settings.chunk_overlap), disabled=True)

st.divider()
st.markdown("### API Keys Status")
col_k1, col_k2 = st.columns(2)
with col_k1:
    st.write(f"**OpenAI API Key**: {'✅ Configured' if settings.openai_api_key else '⚠️ Missing (using deterministic fallback)'}")
with col_k2:
    st.write(f"**Tavily Search Key**: {'✅ Configured' if settings.tavily_api_key else '⚠️ Missing (using deterministic fallback)'}")
