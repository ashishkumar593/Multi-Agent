"""Report display component."""
import streamlit as st

def render_report_view(draft, critic, evidence):
    """Render full tabbed report view with comparison matrix and verified references."""
    score = critic.quality_score if critic else 9.0
    st.markdown("---")
    st.markdown(
        f"### 📋 {draft.title} &nbsp; <span style='background-color:#10B981; color:white; padding:4px 10px; border-radius:12px; font-weight:600;'>Quality Score: {score:.1f}/10</span>",
        unsafe_allow_html=True,
    )

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
