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

# Custom Modern Glassmorphic & Ultra-Pro Styling
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }
    
    code, pre {
        font-family: 'JetBrains Mono', monospace !important;
    }

    /* Hero Header container */
    .hero-container {
        padding: 1.5rem 1.8rem;
        border-radius: 16px;
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(241, 245, 249, 0.85) 100%);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(226, 232, 240, 0.9);
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.05);
        margin-bottom: 1.8rem;
    }

    .main-header { 
        font-size: 2.3rem; 
        font-weight: 800; 
        background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 50%, #2563eb 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.03em;
        margin-bottom: 0.2rem; 
    }
    .sub-header { 
        font-size: 1.05rem; 
        color: #475569; 
        font-weight: 500;
        line-height: 1.5;
    }

    /* Glass Task Cards */
    .task-card-glass {
        background: rgba(255, 255, 255, 0.88);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(226, 232, 240, 0.85);
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 0.9rem;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.03);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .task-card-glass:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(0, 0, 0, 0.06);
    }
    
    /* Kanban Badges */
    .status-badge-alive { 
        background: linear-gradient(135deg, #10b981 0%, #059669 100%); 
        color: white; 
        padding: 4px 10px; 
        border-radius: 9999px; 
        font-weight: 700; 
        font-size: 0.72rem; 
        letter-spacing: 0.05em; 
        text-transform: uppercase; 
        box-shadow: 0 2px 6px rgba(16, 185, 129, 0.25);
    }
    .status-badge-busy { 
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); 
        color: white; 
        padding: 4px 10px; 
        border-radius: 9999px; 
        font-weight: 700; 
        font-size: 0.72rem; 
        letter-spacing: 0.05em; 
        text-transform: uppercase; 
        box-shadow: 0 2px 6px rgba(59, 130, 246, 0.25);
    }
    .status-badge-dead { 
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); 
        color: white; 
        padding: 4px 10px; 
        border-radius: 9999px; 
        font-weight: 700; 
        font-size: 0.72rem; 
        letter-spacing: 0.05em; 
        text-transform: uppercase; 
        box-shadow: 0 2px 6px rgba(239, 68, 68, 0.25);
    }
    .status-badge-blocked { 
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); 
        color: white; 
        padding: 4px 10px; 
        border-radius: 9999px; 
        font-weight: 700; 
        font-size: 0.72rem; 
        letter-spacing: 0.05em; 
        text-transform: uppercase; 
        box-shadow: 0 2px 6px rgba(245, 158, 11, 0.25);
    }
    .status-badge-retired { 
        background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%); 
        color: white; 
        padding: 4px 10px; 
        border-radius: 9999px; 
        font-weight: 700; 
        font-size: 0.72rem; 
        letter-spacing: 0.05em; 
        text-transform: uppercase; 
    }
    .status-badge-idle { 
        background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%); 
        color: white; 
        padding: 4px 10px; 
        border-radius: 9999px; 
        font-weight: 700; 
        font-size: 0.72rem; 
        letter-spacing: 0.05em; 
        text-transform: uppercase; 
        box-shadow: 0 2px 6px rgba(6, 182, 212, 0.25);
    }
    
    /* Modern Glass Metric Cards */
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.85) !important;
        backdrop-filter: blur(12px) !important;
        border: 1px solid rgba(226, 232, 240, 0.9) !important;
        box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.04) !important;
        border-radius: 14px !important;
        padding: 1rem 1.2rem !important;
    }
    div[data-testid="stMetricValue"] {
        font-weight: 800 !important;
        color: #0f172a !important;
        font-size: 1.8rem !important;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 0.82rem !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
        color: #64748b !important;
    }

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: rgba(241, 245, 249, 0.6);
        padding: 6px;
        border-radius: 12px;
        border: 1px solid rgba(226, 232, 240, 0.8);
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        font-weight: 600;
        font-size: 0.92rem;
        padding: 8px 16px;
        color: #475569;
        transition: all 0.2s ease;
    }
    .stTabs [aria-selected="true"] {
        background-color: #ffffff !important;
        color: #1e40af !important;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Initialize database
init_db()
db = SessionLocal()
orch = CompanyOrchestrator(db)

# Hero Header Container
st.markdown(
    """
    <div class="hero-container">
        <div class="main-header">🏢 Autonomous AI Company Cockpit</div>
        <div class="sub-header">Executive-Grade Multi-Agent Operating System with Autonomous Task Cycles, Self-Healing Daemons & Real-Time Quality Scoring.</div>
    </div>
    """,
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

    # Auto-Refresh Toggle
    st.markdown("---")
    st.subheader("🔄 Real-Time Polling")
    auto_refresh = st.toggle("Enable Live Auto-Poll (4s)", value=False)
    if auto_refresh:
        import time
        time.sleep(4)
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
        [
            "Website & Landing Page Agency",
            "B2B Lead Research Service",
            "SEO Content & Copywriting Agency",
            "Data & Market Report Service",
        ],
    )
    biz_type_map = {
        "Website & Landing Page Agency": "website",
        "B2B Lead Research Service": "lead_research",
        "SEO Content & Copywriting Agency": "seo_content",
        "Data & Market Report Service": "data_report",
    }
    default_goals = {
        "Website & Landing Page Agency": "Build a responsive landing page for VerdeBrew eco-friendly coffee",
        "B2B Lead Research Service": "Generate 50 qualified B2B leads for CleanTech sustainable packaging",
        "SEO Content & Copywriting Agency": "Write an in-depth SEO pillar article on Carbon-Negative Specialty Coffee",
        "Data & Market Report Service": "Compile Q4 Market & Operations Performance Report with KPIs and Charts",
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
tab_board, tab_blockers, tab_agents, tab_preview, tab_analytics, tab_factory = st.tabs([
    "📋 Live Task Board (Kanban)",
    "🚨 Human Liaison & Blockers",
    "👥 Agent Org Chart & Health",
    "🌐 Live Deliverable Preview",
    "📈 Performance & Analytics",
    "🏭 Agent Factory",
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
            deps = f"<br><span style='color:#64748b; font-size:0.75rem;'>🔗 Deps: {', '.join(t.depends_on)}</span>" if t.depends_on else ""
            st.markdown(
                f"""
                <div class="task-card-glass">
                    <div style="font-weight: 700; color: #1e293b; margin-bottom: 4px;">{t.title}</div>
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 6px;">
                        <span style="font-size: 0.78rem; color: #64748b; font-family: monospace;">Dept: {t.team_id}</span>
                        <span style="font-size: 0.75rem; background: #f1f5f9; padding: 2px 6px; border-radius: 4px; color: #475569;">Try #{t.attempts}</span>
                    </div>
                    {deps}
                </div>
                """,
                unsafe_allow_html=True,
            )

    with col_doing:
        st.subheader("⚙️ DOING")
        for t in [t for t in all_tasks if t.status == "doing"]:
            st.markdown(
                f"""
                <div class="task-card-glass" style="border-left: 3px solid #3b82f6;">
                    <div style="font-weight: 700; color: #1e293b; margin-bottom: 4px;">{t.title}</div>
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 8px;">
                        <span class="status-badge-busy">IN PROGRESS</span>
                        <span style="font-size: 0.78rem; color: #3b82f6; font-family: monospace; font-weight: 600;">{t.owner_agent_id}</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with col_review:
        st.subheader("🔍 REVIEW")
        for t in [t for t in all_tasks if t.status == "review"]:
            st.markdown(
                f"""
                <div class="task-card-glass" style="border-left: 3px solid #f59e0b;">
                    <div style="font-weight: 700; color: #1e293b; margin-bottom: 4px;">{t.title}</div>
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 8px;">
                        <span class="status-badge-idle">TESTING</span>
                        <span style="font-size: 0.78rem; color: #64748b; font-family: monospace;">{t.owner_agent_id}</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with col_done:
        st.subheader("✅ DONE")
        for t in [t for t in all_tasks if t.status == "done"]:
            st.markdown(
                f"""
                <div class="task-card-glass" style="border-left: 3px solid #10b981;">
                    <div style="font-weight: 700; color: #1e293b; margin-bottom: 4px;">{t.title}</div>
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 8px;">
                        <span class="status-badge-alive">APPROVED</span>
                        <span style="font-size: 0.78rem; color: #10b981; font-family: monospace; font-weight: 600;">✓ Verified</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with col_blocked:
        st.subheader("🚨 BLOCKED")
        for t in [t for t in all_tasks if t.status == "blocked"]:
            st.markdown(
                f"""
                <div class="task-card-glass" style="border-left: 3px solid #ef4444; background: rgba(254, 242, 242, 0.85);">
                    <div style="font-weight: 700; color: #991b1b; margin-bottom: 4px;">{t.title}</div>
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 8px;">
                        <span class="status-badge-blocked">WAITING HUMAN</span>
                        <span style="font-size: 0.78rem; color: #b91c1c; font-weight: 600;">Needs Sign-Off</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

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
    sandbox_metrics = Path("./sandbox/metrics.json")
    sandbox_data_report = Path("./sandbox/data_report.md")
    sandbox_data_pdf = Path("./sandbox/data_report.pdf")

    p_tab1, p_tab2, p_tab3, p_tab4, p_tab5, p_tab6 = st.tabs([
        "🌐 Website Preview",
        "📊 Lead List (CSV)",
        "📝 SEO Article (MD)",
        "📄 Exported Article PDF",
        "✉️ Cold Outreach Emails",
        "📈 Executive Data Report"
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

    with p_tab6:
        if not sandbox_data_report.exists():
            st.info("Executive data report not yet created. Launch a Data & Market Report project to generate.")
        else:
            if sandbox_metrics.exists():
                st.markdown("##### 📊 Statistical Metrics Summary (metrics.json)")
                try:
                    m_data = json.loads(sandbox_metrics.read_text(encoding="utf-8"))
                    kpis = m_data.get("kpis", {})
                    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                    kpi_items = list(kpis.items())
                    if len(kpi_items) >= 4:
                        col_m1.metric("Market Growth", kpi_items[0][1])
                        col_m2.metric("Retention", kpi_items[1][1])
                        col_m3.metric("Gross Margin", kpi_items[2][1])
                        col_m4.metric("Carbon Offset", f"{kpi_items[3][1]} T")
                except Exception:
                    pass

            st.markdown("---")
            dr_text = sandbox_data_report.read_text(encoding="utf-8")
            st.markdown(dr_text)

            col_dr1, col_dr2 = st.columns(2)
            with col_dr1:
                st.download_button("📥 Download data_report.md", data=dr_text, file_name="data_report.md", mime="text/markdown")
            with col_dr2:
                if sandbox_data_pdf.exists():
                    st.download_button("📥 Download data_report.pdf", data=sandbox_data_pdf.read_bytes(), file_name="data_report.pdf", mime="application/pdf")

# -------------------------------------------------------------
# TAB 5: Performance & Spend Analytics
# -------------------------------------------------------------
with tab_analytics:
    st.subheader("📈 Real-Time Performance & Spend Telemetry")

    ledger_entries = db.query(BudgetLedgerModel).all()
    tasks_all = db.query(TaskModel).all()
    reviews_all = db.query(ReviewModel).all()
    agents_all = db.query(AgentModel).all()

    # High-level KPIs
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
    with kpi_col1:
        st.metric("Total Tasks", len(tasks_all))
    with kpi_col2:
        completed = sum(1 for t in tasks_all if t.status == "done")
        st.metric("Completed Tasks", completed)
    with kpi_col3:
        pass_rate = round((completed / max(1, len(tasks_all))) * 100, 1)
        st.metric("Task Success Rate", f"{pass_rate}%")
    with kpi_col4:
        avg_score = round(sum(r.quality_score for r in reviews_all) / max(1, len(reviews_all)), 1)
        st.metric("Avg Quality Score", f"{avg_score} / 10.0")

    st.markdown("---")

    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.markdown("##### 💰 Spend by Agent")
        agent_spend: dict[str, float] = {}
        for row in ledger_entries:
            agent_spend[row.agent_id] = round(agent_spend.get(row.agent_id, 0.0) + float(row.cost or 0.0), 4)

        if agent_spend:
            st.bar_chart(agent_spend)
        else:
            st.info("No ledger entries recorded yet.")

    with col_chart2:
        st.markdown("##### 🏆 Reward Points Standings")
        agent_scores = {a.id: float(a.score or 0.0) for a in agents_all}
        if agent_scores:
            st.bar_chart(agent_scores)
        else:
            st.info("No agent scores available.")

    st.markdown("---")
    st.markdown("##### 📜 Recent Review Scorecards")
    for r in reviews_all[-5:]:
        st.write(f"• Task `{r.task_id}` by `{r.reviewer_id}`: **{r.verdict.upper()}** (Score: {r.quality_score}/10) — *{r.notes}*")

# -------------------------------------------------------------
# TAB 6: Dynamic Agent Factory (Runtime Role Creator)
# -------------------------------------------------------------
with tab_factory:
    st.subheader("🏭 Dynamic Agent Factory & Custom Role Registry")
    st.caption("CEO / HR can dynamically define and register new agent roles at runtime without code changes.")

    with st.form("form_create_role"):
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            new_role_name = st.text_input("Role Identifier (lowercase, e.g. 'finance_analyst')", value="finance_analyst")
            new_model_tier = st.selectbox("Model Tier", ["fast", "strong"])
            new_dept = st.selectbox("Target Department", ["team_exec", "team_eng", "team_mktg", "team_ops"])
        with f_col2:
            new_max_steps = st.number_input("Max Execution Steps", min_value=1, max_value=20, value=6)
            new_token_budget = st.number_input("Token Budget Per Task", min_value=1000, max_value=50000, value=12000, step=1000)

        new_sys_prompt = st.text_area(
            "System Prompt / Operational Persona",
            value="You are a Senior Financial Analyst responsible for unit economics and SaaS runway models.",
            height=90,
        )

        all_available_tools = [
            "write_file", "read_file", "run_sandbox", "web_search", "rag_retrieve",
            "export_pdf_report", "generate_email_sequence", "create_task", "read_board"
        ]
        selected_tools = st.multiselect(
            "Whitelisted Tool Permissions",
            options=all_available_tools,
            default=["read_file", "write_file", "export_pdf_report", "rag_retrieve"],
        )

        btn_register = st.form_submit_button("🚀 Register Role Spec & Spawn Initial Agent", use_container_width=True)

        if btn_register and new_role_name.strip():
            orch.runner.tools.register_role_spec(
                role=new_role_name.strip().lower(),
                system_prompt=new_sys_prompt,
                tools=selected_tools,
                model_tier=new_model_tier,
                max_steps=int(new_max_steps),
                token_budget=int(new_token_budget),
                agent_id="agent_ceo",
            )
            # Spawn initial worker into target department
            spawn_res = orch.runner.tools.spawn_agent(
                role=new_role_name.strip().lower(),
                team_id=new_dept,
                agent_id="agent_hr",
            )
            st.success(f"Role spec '{new_role_name}' registered! Spawned agent: `{spawn_res.get('agent_id')}`")
            st.rerun()

    st.markdown("---")
    st.markdown("##### 📚 Currently Registered Role Templates")
    from backend.db.company_models import RoleSpecModel
    registered_specs = db.query(RoleSpecModel).all()
    for spec in registered_specs:
        with st.expander(f"⚙️ Role: {spec.role.upper()} | Model Tier: {spec.model_tier.upper()}"):
            st.write(f"**Prompt**: {spec.system_prompt}")
            st.write(f"**Tools**: `{spec.tools}`")
            st.caption(f"Max Steps: {spec.max_steps} | Token Budget: {spec.token_budget:,}")

db.close()
