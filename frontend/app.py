"""Streamlit Frontend: Autonomous AI Company Cockpit & Live Control Center.
Implements the dashboard requirements from Section 2, 6, & 7 of the Build Report:
- Live Task Board (Todo, Doing, Review, Done, Blocked)
- Agent Health & Org Chart with live heartbeats and reward points
- Human Liaison Blocker & Approval Inbox with 1-click unblock
- Financial Budget Ledger and spend tracking
- Emergency Kill Switch
- Live Deliverable Sandbox Preview (rendered HTML/CSS)
"""
from __future__ import annotations

import json
from pathlib import Path
import streamlit as st

# Configure page layout
st.set_page_config(
    page_title="Autonomous AI Company | Operations Cockpit",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

from backend.company.monitor import CompanyMonitor
from backend.company.orchestrator import CompanyOrchestrator
from backend.db.company_database import SessionLocal, init_db
from backend.db.company_models import (
    AgentModel,
    BlockerModel,
    BudgetLedgerModel,
    ProjectModel,
    ReviewModel,
    RewardModel,
    TaskModel,
)

# Custom Styling
st.markdown(
    """
    <style>
    .main-header { font-size: 2.2rem; font-weight: 700; color: #0F172A; margin-bottom: 0.2rem; }
    .sub-header { font-size: 1.05rem; color: #475569; margin-bottom: 1.5rem; }
    .status-badge-alive { background-color: #10B981; color: white; padding: 3px 8px; border-radius: 10px; font-weight: 600; font-size: 0.8rem; }
    .status-badge-busy { background-color: #3B82F6; color: white; padding: 3px 8px; border-radius: 10px; font-weight: 600; font-size: 0.8rem; }
    .status-badge-dead { background-color: #EF4444; color: white; padding: 3px 8px; border-radius: 10px; font-weight: 600; font-size: 0.8rem; }
    .status-badge-blocked { background-color: #F59E0B; color: white; padding: 3px 8px; border-radius: 10px; font-weight: 600; font-size: 0.8rem; }
    .card-task { background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 12px; margin-bottom: 10px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# Initialize database
init_db()
db = SessionLocal()
orch = CompanyOrchestrator(db)

# Header
st.markdown('<div class="main-header">🏢 Autonomous AI Company Cockpit</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Human-Supervised Multi-Agent Organization with Autonomous Execution, Health Monitoring & Reward Scoring.</div>',
    unsafe_allow_html=True,
)

# Sidebar: Controls & Financials
with st.sidebar:
    st.header("⚡ Master Controls")

    # Emergency Kill Switch
    is_halted = CompanyMonitor.is_kill_switch_active()
    if is_halted:
        st.error("🚨 EMERGENCY KILL SWITCH ACTIVE: ALL LOOPS PAUSED")
        if st.button("🟢 Reset Kill Switch & Resume", use_container_width=True):
            CompanyMonitor.reset_kill_switch()
            st.rerun()
    else:
        st.success("🟢 System Status: Active & Operational")
        if st.button("🛑 TRIP KILL SWITCH", type="primary", use_container_width=True):
            CompanyMonitor.trip_kill_switch("Human Owner Emergency Pause")
            st.rerun()

    st.markdown("---")
    st.header("📊 Financial Ledger")
    total_tokens = sum(row.tokens for row in db.query(BudgetLedgerModel).all())
    total_spend = sum(row.cost for row in db.query(BudgetLedgerModel).all())
    budget_cap = 50.0

    st.metric("Total Tokens Used", f"{total_tokens:,}")
    st.metric("Total Company Spend", f"${total_spend:.4f}", f"Cap: ${budget_cap:.2f}")
    st.progress(min(1.0, total_spend / budget_cap))

    st.markdown("---")
    st.header("🎯 Launch New Project")
    biz_choice = st.selectbox(
        "Select Business Model:",
        ["Website & Landing Page Agency", "B2B Lead Research Service", "SEO Content & Copywriting Agency"],
    )
    biz_type_map = {
        "Website & Landing Page Agency": "website",
        "B2B Lead Research Service": "lead_research",
        "SEO Content & Copywriting Agency": "seo_content",
    }
    default_goals = {
        "Website & Landing Page Agency": "Build a responsive landing page for VerdeBrew eco-friendly coffee",
        "B2B Lead Research Service": "Generate 50 qualified B2B leads for CleanTech sustainable packaging",
        "SEO Content & Copywriting Agency": "Write an in-depth SEO pillar article on Carbon-Negative Specialty Coffee",
    }
    new_goal = st.text_area(
        "Business Objective for CEO:",
        value=default_goals[biz_choice],
        height=80,
    )
    if st.button("Submit to CEO Agent", use_container_width=True):
        orch.start_project(
            goal=new_goal,
            project_name=f"{biz_choice.split()[0]} Campaign",
            business_type=biz_type_map[biz_choice],
        )
        st.success(f"CEO registered project for {biz_choice} and Manager created task board!")
        st.rerun()

# Top Action Bar: Simulation Steppers
c_act1, c_act2, c_act3 = st.columns([2, 2, 4])
with c_act1:
    if st.button("▶️ Step Company Cycle", type="primary", use_container_width=True):
        step_res = orch.step()
        st.toast(f"Step executed: {len(step_res.get('executed_tasks', []))} tasks worked, {len(step_res.get('reviews_done', []))} reviewed.")
        st.rerun()

with c_act2:
    if st.button("⚡ Run Full Auto-Pilot", use_container_width=True):
        with st.spinner("Company executing autonomous loops..."):
            for _ in range(6):
                orch.step()
        st.rerun()

with c_act3:
    projects = db.query(ProjectModel).all()
    active_proj = projects[-1] if projects else None
    if active_proj:
        st.info(f"**Active Project**: `{active_proj.name}` (ID: `{active_proj.id}`) | Goal: {active_proj.goal[:65]}...")

st.markdown("---")

# Main View Tabs
tab_board, tab_blockers, tab_agents, tab_preview = st.tabs([
    "📋 Live Task Board (Kanban)",
    "🚨 Human Liaison & Blockers",
    "👥 Agent Org Chart & Health",
    "🌐 Live Deliverable Preview",
])

# -------------------------------------------------------------
# TAB 1: Live Task Board (Kanban)
# -------------------------------------------------------------
with tab_board:
    all_tasks = db.query(TaskModel).all()
    col_todo, col_doing, col_review, col_done, col_blocked = st.columns(5)

    with col_todo:
        st.subheader("📝 TODO")
        for t in [t for t in all_tasks if t.status == "todo"]:
            with st.container():
                st.markdown(f"**{t.title}**")
                st.caption(f"Team: `{t.team_id}` | Attempts: {t.attempts}")
                if t.depends_on:
                    st.caption(f"Depends on: {', '.join(t.depends_on)}")
                st.divider()

    with col_doing:
        st.subheader("⚙️ DOING")
        for t in [t for t in all_tasks if t.status == "doing"]:
            with st.container():
                st.markdown(f"**{t.title}**")
                st.caption(f"Worker: `{t.owner_agent_id}`")
                st.markdown('<span class="status-badge-busy">IN PROGRESS</span>', unsafe_allow_html=True)
                st.divider()

    with col_review:
        st.subheader("🔍 REVIEW")
        for t in [t for t in all_tasks if t.status == "review"]:
            with st.container():
                st.markdown(f"**{t.title}**")
                st.caption(f"Submitted by: `{t.owner_agent_id}`")
                st.markdown('<span class="status-badge-busy">PENDING REVIEW</span>', unsafe_allow_html=True)
                st.divider()

    with col_done:
        st.subheader("✅ DONE")
        for t in [t for t in all_tasks if t.status == "done"]:
            with st.container():
                st.markdown(f"**{t.title}**")
                st.caption(f"Owner: `{t.owner_agent_id or 'Complete'}`")
                st.markdown('<span class="status-badge-alive">APPROVED</span>', unsafe_allow_html=True)
                st.divider()

    with col_blocked:
        st.subheader("🚨 BLOCKED")
        for t in [t for t in all_tasks if t.status == "blocked"]:
            with st.container():
                st.markdown(f"**{t.title}**")
                st.markdown('<span class="status-badge-blocked">WAITING APPROVAL</span>', unsafe_allow_html=True)
                st.divider()

# -------------------------------------------------------------
# TAB 2: Human Liaison & Approval Inbox
# -------------------------------------------------------------
with tab_blockers:
    st.subheader("🚨 Escalation Inbox (Human Decision Required)")
    blockers = db.query(BlockerModel).all()

    pending_blockers = [b for b in blockers if b.status == "pending"]
    if not pending_blockers:
        st.success("✅ Zero active blockers. The company is operating smoothly without human intervention.")
    else:
        for b in pending_blockers:
            with st.expander(f"⚠️ Blocker #{b.id} | Priority: {b.priority.upper()} | Type: {b.type.upper()}", expanded=True):
                st.write(f"**Details**: {b.details}")
                st.caption(f"Associated Task ID: `{b.task_id}` | Escalated By: `{b.agent_id}`")

                cols = st.columns(len(b.options) or 1)
                for i, opt in enumerate(b.options):
                    with cols[i]:
                        if st.button(f"👉 {opt}", key=f"btn_blk_{b.id}_{i}"):
                            orch.resolve_blocker(b.id, action=opt)
                            st.toast(f"Blocker #{b.id} resolved with action '{opt}'!")
                            st.rerun()

    st.markdown("---")
    st.subheader("📜 Resolved Blocker History")
    resolved = [b for b in blockers if b.status == "resolved"]
    for rb in resolved:
        st.write(f"✔️ **Blocker #{rb.id}**: {rb.details} — Resolved at `{rb.resolved_at}`")

# -------------------------------------------------------------
# TAB 3: Agent Org Chart & Health
# -------------------------------------------------------------
with tab_agents:
    st.subheader("👥 Active Agent Workforce")
    agents = db.query(AgentModel).all()

    col_a1, col_a2 = st.columns(2)
    for idx, agent in enumerate(agents):
        target_col = col_a1 if idx % 2 == 0 else col_a2
        with target_col:
            badge_class = f"status-badge-{agent.status}"
            with st.container():
                st.markdown(
                    f"**{agent.role.upper()}** (`{agent.id}`) &nbsp; <span class='{badge_class}'>{agent.status.upper()}</span>",
                    unsafe_allow_html=True,
                )
                st.write(f"Department: `{agent.team_id}` | Reward Points: **{agent.score:.1f} pts**")
                st.caption(f"Last Heartbeat: `{agent.last_heartbeat}`")
                if agent.replaced_by:
                    st.caption(f"🔄 Replaced by: `{agent.replaced_by}`")
                st.divider()

# -------------------------------------------------------------
# TAB 4: Live Deliverable Preview
# -------------------------------------------------------------
with tab_preview:
    st.subheader("📦 Deliverable Sandbox Outputs")
    sandbox_html = Path("./sandbox/index.html")
    sandbox_css = Path("./sandbox/styles.css")
    sandbox_csv = Path("./sandbox/leads.csv")
    sandbox_md = Path("./sandbox/article.md")
    sandbox_pdf = Path("./sandbox/article_report.pdf")
    sandbox_outreach = Path("./sandbox/outreach_campaign.txt")

    p_tab1, p_tab2, p_tab3, p_tab4, p_tab5 = st.tabs([
        "🌐 Website Preview",
        "📊 Lead List (CSV)",
        "📝 SEO Article (MD)",
        "📄 Exported PDF Report",
        "✉️ Cold Outreach Emails"
    ])

    with p_tab1:
        if not sandbox_html.exists():
            st.info("Website deliverable not yet created. Launch a Website Agency project to generate.")
        else:
            html_code = sandbox_html.read_text(encoding="utf-8")
            css_code = sandbox_css.read_text(encoding="utf-8") if sandbox_css.exists() else ""
            full_preview = f"<style>{css_code}</style>\n{html_code}"
            st.components.v1.html(full_preview, height=500, scrolling=True)
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                st.download_button("📥 Download index.html", data=html_code, file_name="index.html", mime="text/html")
            with col_d2:
                st.download_button("📥 Download styles.css", data=css_code, file_name="styles.css", mime="text/css")

    with p_tab2:
        if not sandbox_csv.exists():
            st.info("Lead list deliverable not yet created. Launch a Lead Research project to generate.")
        else:
            csv_text = sandbox_csv.read_text(encoding="utf-8")
            st.code(csv_text, language="csv")
            st.download_button("📥 Download leads.csv", data=csv_text, file_name="leads.csv", mime="text/csv")

    with p_tab3:
        if not sandbox_md.exists():
            st.info("SEO article deliverable not yet created. Launch an SEO Content project to generate.")
        else:
            md_text = sandbox_md.read_text(encoding="utf-8")
            st.markdown(md_text)
            st.download_button("📥 Download article.md", data=md_text, file_name="article.md", mime="text/markdown")

    with p_tab4:
        if not sandbox_pdf.exists():
            st.info("PDF report deliverable not yet created. Runs automatically during SEO Content projects.")
        else:
            pdf_bytes = sandbox_pdf.read_bytes()
            st.success(f"📄 Publication-ready PDF Report generated ({len(pdf_bytes):,} bytes).")
            st.download_button("📥 Download article_report.pdf", data=pdf_bytes, file_name="article_report.pdf", mime="application/pdf")

    with p_tab5:
        if not sandbox_outreach.exists():
            st.info("Cold outreach campaign sequence not yet created. Runs automatically during Lead Research projects.")
        else:
            outreach_text = sandbox_outreach.read_text(encoding="utf-8")
            st.text_area("Cold Outreach Email Sequence", value=outreach_text, height=350)
            st.download_button("📥 Download outreach_campaign.txt", data=outreach_text, file_name="outreach_campaign.txt", mime="text/plain")

db.close()
