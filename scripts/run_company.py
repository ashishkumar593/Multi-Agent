"""CLI Demonstration of the Autonomous AI Company.
Runs the complete end-to-end business loop:
1. CEO creates project
2. Manager splits into tasks with dependencies
3. Workers (Researcher, Marketing, Developer) complete tasks in sandbox
4. Reviewer tests and scores deliverables independently
5. Reward points are calculated and credited
6. Human Liaison presents the final release approval gate
7. Human approves, project finishes successfully!
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

# Safeguard sys.path
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from backend.company.orchestrator import CompanyOrchestrator
from backend.db.company_database import SessionLocal, init_db
from backend.db.company_models import AgentModel, BlockerModel, TaskModel


def run_company_simulation(goal: str = "Build a responsive landing page for VerdeBrew eco-friendly coffee"):
    print("\n==================================================================")
    print("  🏢 AUTONOMOUS AI COMPANY: END-TO-END EXECUTION RUNNER")
    print("==================================================================")

    init_db(reset=True)
    db = SessionLocal()
    orch = CompanyOrchestrator(db)

    print(f"\n[HUMAN OWNER]: Goal submitted -> '{goal}'")
    time.sleep(0.3)

    # 1. CEO & Manager create project
    print("\n[CEO AGENT]: Evaluating business goal and initializing project...")
    project = orch.start_project(goal=goal, project_name="VerdeBrew Landing Page Project")
    print(f"  -> Project '{project.name}' (ID: {project.id}) registered with budget ${project.budget_limit:.2f}.")

    tasks = db.query(TaskModel).filter(TaskModel.project_id == project.id).all()
    print(f"\n[MANAGER AGENT]: Created {len(tasks)} dependent tasks on the shared board:")
    for t in tasks:
        deps = f"(depends on {', '.join(t.depends_on)})" if t.depends_on else "(no dependencies)"
        print(f"  - [{t.id}] {t.title} {deps}")

    # 2. Step the company until work needs review or blocker
    print("\n[COMPANY CORE]: Activating autonomous task, review, and health loops...")
    cycle = 1
    max_cycles = 10

    while cycle <= max_cycles:
        step_res = orch.step()
        executed = step_res.get("executed_tasks", [])
        reviews = step_res.get("reviews_done", [])

        if executed:
            for tid in executed:
                t = db.query(TaskModel).filter(TaskModel.id == tid).first()
                print(f"  [CYCLE {cycle} - WORKER]: Finished '{t.title}' -> Submitted for Review.")

        if reviews:
            for tid in reviews:
                t = db.query(TaskModel).filter(TaskModel.id == tid).first()
                print(f"  [CYCLE {cycle} - REVIEWER]: Verified deliverables for '{t.title}' -> Status: {t.status.upper()}")

        # Check for pending human blockers
        blocker = db.query(BlockerModel).filter(BlockerModel.status == "pending").first()
        if blocker:
            print("\n------------------------------------------------------------------")
            print("  🚨 HUMAN LIAISON ESCALATION RECEIVED")
            print("------------------------------------------------------------------")
            print(f"Blocker ID: #{blocker.id} | Priority: {blocker.priority.upper()} | Type: {blocker.type.upper()}")
            print(f"Details: {blocker.details}")
            print(f"Options: {', '.join(blocker.options)}")
            print("Action: Automatically approving deployment gate as human owner...")
            orch.resolve_blocker(blocker.id, action="Approve & Publish")
            print("  -> Blocker RESOLVED. Public deployment granted!")
            print("------------------------------------------------------------------\n")

        # Check if all tasks done
        all_tasks = db.query(TaskModel).filter(TaskModel.project_id == project.id).all()
        done_count = sum(1 for t in all_tasks if t.status == "done")
        if done_count == len(all_tasks):
            print("\n🎉 ALL PROJECT TASKS COMPLETED SUCCESSFULLY!")
            break

        cycle += 1
        time.sleep(0.2)

    # 3. Print Final Company Ledger & Deliverables
    print("\n==================================================================")
    print("  🏆 FINAL COMPANY PERFORMANCE & REWARD REPORT")
    print("==================================================================")
    agents = db.query(AgentModel).filter(AgentModel.status.in_(["alive", "idle", "busy"])).all()
    print("\nAgent Scores & Standings:")
    for a in agents:
        print(f"  - [{a.role.upper():12}] {a.id:16} | Performance Score: {a.score:.1f} pts | Status: {a.status}")

    sandbox_html = Path("./sandbox/index.html")
    sandbox_css = Path("./sandbox/styles.css")
    if sandbox_html.exists():
        print(f"\nDeliverable Output Generated:")
        print(f"  - HTML: {sandbox_html.resolve()} ({sandbox_html.stat().st_size} bytes)")
        print(f"  - CSS:  {sandbox_css.resolve()} ({sandbox_css.stat().st_size} bytes)")

    print("==================================================================\n")
    db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Autonomous AI Company simulation")
    parser.add_argument("--goal", default="Build a responsive landing page for VerdeBrew eco-friendly coffee", help="Goal text")
    args = parser.parse_args()
    run_company_simulation(args.goal)
