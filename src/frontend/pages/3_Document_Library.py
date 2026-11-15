"""Document Library Page."""
import streamlit as st
from src.backend.api.app import document_service

st.set_page_config(page_title="Document Library | AI Research Agent", page_icon="📚", layout="wide")
st.title("📚 Document Knowledge Base")
st.caption("Inspect and manage documents indexed into the Hybrid RAG engine.")

docs = document_service.list_documents()

if not docs:
    st.info("Knowledge base is currently empty. Upload PDF, DOCX, TXT, or Markdown documents via the sidebar.")
else:
    for doc in docs:
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.write(f"📄 **{doc.get('filename')}**")
        with col2:
            st.write(f"Chunks: `{doc.get('chunks_count')}`")
        with col3:
            st.write(f"Size: `{doc.get('size_bytes', 0) / 1024:.1f} KB`")
        st.divider()
