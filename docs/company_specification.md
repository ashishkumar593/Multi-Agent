# Autonomous AI Company: Build Report

Nov 15, 2026 · @Ashish

## 1. Overview

This project builds a human-supervised AI company: role-based agents (CEO, HR, Managers, Workers, Reviewer, Human Liaison) run projects from a shared task board, replace failed agents automatically, hire when a team is short, and earn reward points for reviewed work.

**Division of work**

| Owner | Responsibility |
| --- | --- |
| You (human owner) | Legal ownership, payments, customers, platform accounts, logins and API keys, approvals |
| Agents | Planning, execution, review, hiring and replacement, status reporting, asking you for what they need |

**Design principles**

- Agents are data, not code: every agent is a spec (role, prompt, tools, limits) run by one generic runner.
- Agents only use whitelisted tools and never see raw passwords.
- Hard caps on headcount, tokens, cost, and retries, plus a kill switch.
- Reward points come from independent review (tests or a Reviewer agent), never from the agent's own claim.
- Build one working end-to-end loop first, then add departments.

## 2. MVP and business choice

The MVP is one business, one project, and one complete loop: the CEO creates a project, a Manager splits it into tasks, workers finish them, the Reviewer scores them, and you approve the delivery.

**Pick one starting business** (the agents need concrete deliverables):

| Option | Deliverable | Why it suits agents |
| --- | --- | --- |
| Website/landing page agency | HTML/CSS sites for small businesses | Output is testable and easy to demo |
| Content and SEO agency | Articles, keyword plans | Fast to produce, easy to review |
| Lead research service | Company lists with contact context | Uses your search and RAG skills |
| Data report service | Analysis reports with charts | Reuses the research pipeline |

Recommended default: website/landing page agency, because tests and screenshots give an objective Reviewer signal.

**MVP done means:**

1. CEO agent turns your goal into a project with 5 to 10 tasks.
2. At least 3 worker roles complete tasks from the board.
3. A killed worker is replaced by HR within 60 seconds and the task resumes.
4. A blocker reaches you through the Liaison and your reply unblocks the task.
5. Reward points update from Reviewer results.
6. A dashboard shows tasks, agents, spend, and a kill switch.

## 3. Architecture

You approve actions and unblock agents through the Human Liaison; the CEO directs the teams, which all work from one shared board, with the Monitor and shared infrastructure underneath.

## 4. Tech stack and accounts

| Layer | Choice | Cost |
| --- | --- | --- |
| Language | Python 3.11+ | Free |
| Orchestration | LangGraph (state graph, parallel fan-out, checkpoints) | Free |
| LLM | OpenAI-compatible base_url + key with offline deterministic fallback | Free |
| Database | SQLite / PostgreSQL (11 tables) | Free |
| Queue and events | Redis / in-memory event bus | Free |
| Memory / knowledge base | Chroma + local embeddings | Free |
| API and dashboard | FastAPI + Streamlit | Free |
| Sandbox for code | Isolated environment with resource limits | Free |
| Secrets | Vault / credential registry | Free |
| Notifications | Telegram bot & dashboard webhook for blockers | Free |
| Tracing | Structured event logs & budget ledger | Free |
| CI | GitHub Actions | Free |
| Hosting | Local first, then Docker | Free |

## 5. Database schema

Eleven tables:
1. `agents`: id, role, team_id, spec_json, status, score, last_heartbeat, created_at, replaced_by
2. `role_specs`: role, system_prompt, tools, model_tier, max_steps, token_budget
3. `teams`: id, name, manager_agent_id, min_headcount, max_headcount
4. `projects`: id, name, goal, status, budget_limit, owner_agent_id
5. `tasks`: id, project_id, team_id, title, spec, status, owner_agent_id, attempts, result, depends_on
6. `events`: id, ts, agent_id, task_id, type, payload
7. `budget_ledger`: id, ts, agent_id, project_id, tokens, cost, tool_calls
8. `reviews`: id, task_id, reviewer_id, verdict, quality_score, notes
9. `rewards`: id, agent_id, task_id, points, reason, ts
10. `blockers`: id, agent_id, task_id, type, priority, status, details, created_at, resolved_at
11. `credentials_registry`: name, scope, allowed_roles, vault_ref, last_used

## 6. Agent roles and specs (9 roles)
- CEO
- Manager
- HR
- Human Liaison
- Developer
- Content/Marketing
- Researcher
- Reviewer
- Monitor (system daemon)

## 7. Core loops (5 loops)
1. Task loop
2. Health & auto-replacement loop
3. Hiring loop
4. Reward & review loop
5. Blocker & approval loop
