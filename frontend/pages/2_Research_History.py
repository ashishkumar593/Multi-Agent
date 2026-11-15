"""Research History Page."""
import streamlit as st
from backend.api.app import research_service

st.set_page_config(page_title="Research History | AI Research Agent", page_icon="📜", layout="wide")
st.title("📜 Research Job History")

jobs = research_service.repository.list_all()

if not jobs:
    st.info("No research jobs recorded yet. Launch a research query from the 'New Research' page.")
else:
    for job in jobs:
        with st.expander(f"📌 {job.get('topic')} — Status: {job.get('status').upper()}"):
            st.write(f"**Job ID**: `{job.get('id')}`")
            st.write(f"**Scope**: {job.get('scope')}")
            st.write(f"**Quality Score**: {job.get('quality_score', 0.0):.1f}/10")
            if job.get("report_markdown"):
                st.download_button(
                    label="Download Report",
                    data=job.get("report_markdown", ""),
                    file_name=f"{job.get('id')}.md",
                    key=job.get("id"),
                )
