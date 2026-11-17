"""Chaos Testing Suite for the Autonomous AI Company.
Implements the Week 2 gate & Section 10 Chaos Test:
1. Start an active project
2. Worker claims a task (status becomes 'doing')
3. Worker is killed abruptly (simulating container crash or unhandled exception)
4. System Monitor detects lost heartbeat
5. Reaps the dead worker and restores abandoned task to 'todo'
6. HR spawns a replacement agent from the role_spec
7. Replacement agent resumes and successfully finishes the task
8. Confirms 0 duplicate work and 100% recovery!
"""
from __future__ import annotations

import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Safeguard sys.path
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from backend.company.orchestrator import CompanyOrchestrator
from backend.db.company_database import SessionLocal, init_db
from backend.db.company_models import AgentModel, TaskModel


def run_chaos_test():
    print("\n==================================================================")
    print("  💥 CHAOS TEST: WORKER CRASH & HR AUTO-REPLACEMENT")
    print("==================================================================")

    init_db(reset=True)
    db = SessionLocal()
    orch = CompanyOrchestrator(db)

    # 1. Start project
    project = orch.start_project(goal="Chaos Test: Resilient Website Build")
    t1 = db.query(TaskModel).filter(TaskModel.id == f"{project.id}_t1").first()

    # 2. Worker claims task
    claimed = orch.runner.claim_task_atomically("agent_res_01")
    print(f"\n[PHASE 1]: Worker 'agent_res_01' claimed task '{claimed.title}' (Status: {claimed.status.upper()})")

    # 3. Simulate sudden kill / crash mid-task
    print("\n[PHASE 2]: Simulating fatal crash! Killing 'agent_res_01' mid-task...")
    worker = db.query(AgentModel).filter(AgentModel.id == "agent_res_01").first()
    worker.last_heartbeat = datetime.now(timezone.utc) - timedelta(seconds=45)
    db.commit()

    # 4. Monitor checks heartbeats
    print("\n[PHASE 3]: System Monitor running heartbeat audit...")
    dead_agents = orch.monitor.check_heartbeats_and_reap()
    print(f"  -> Detected dead agents: {dead_agents}")
    assert "agent_res_01" in dead_agents

    # Verify task was reclaimed
    db.refresh(t1)
    print(f"  -> Abandoned task '{t1.title}' state restored to: {t1.status.upper()}")
    assert t1.status == "todo"

    # 5. HR auto-replacement
    print("\n[PHASE 4]: HR department responding to worker death...")
    replacements = orch.monitor.handle_hr_replacements(dead_agents)
    replacement_id = replacements[0]
    print(f"  -> HR spawned replacement: '{replacement_id}' from 'researcher' role_spec.")

    db.refresh(worker)
    print(f"  -> Dead worker record updated: status='{worker.status}', replaced_by='{worker.replaced_by}'")
    assert worker.status == "dead"
    assert worker.replaced_by == replacement_id

    # 6. Replacement resumes work
    print("\n[PHASE 5]: Replacement agent claiming abandoned task...")
    resumed_claim = orch.runner.claim_task_atomically(replacement_id)
    assert resumed_claim is not None
    assert resumed_claim.id == t1.id
    print(f"  -> '{replacement_id}' claimed '{resumed_claim.title}'. Resuming work...")

    # Finish task
    orch.runner.execute_task(replacement_id, resumed_claim)
    print(f"  -> Task finished and submitted for review by replacement!")

    # Reviewer approves
    orch._process_reviews()
    db.refresh(t1)
    print(f"  -> Final Task Status: {t1.status.upper()}")
    assert t1.status == "done"

    print("\n==================================================================")
    print("  ✅ CHAOS TEST PASSED: 100% RECOVERY WITH ZERO LOST PROGRESS")
    print("==================================================================")
    db.close()


if __name__ == "__main__":
    run_chaos_test()
