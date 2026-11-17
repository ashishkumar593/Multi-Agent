# Autonomous AI Company: Architectural Blueprint

## 1. System Vision & Architecture

The **Autonomous AI Company** is a human-supervised multi-agent enterprise simulation where autonomous agents execute projects from a shared task board, monitor their own health, automatically replace failed workers, scale headcount based on workload, and receive objective reward points.

```mermaid
flowchart TD
    subgraph Human Layer [1. Human Owner Oversight]
        Human([Human Owner]) <--> Telegram[Telegram Bot / Mobile Push]
        Human <--> Dashboard[Streamlit Cockpit UI]
    end

    subgraph Management Layer [2. Executive Leadership & Shared Board]
        Liaison[Human Liaison Agent] <--> Human
        CEO[CEO Agent: Goals -> Projects] --> Manager[Project Manager Agent: Tasks & Deps]
        Manager <--> TaskBoard[(Shared Task Board: tasks table)]
    end

    subgraph Execution Layer [3. Cross-Functional Teams & Sandbox]
        TaskBoard <--> Dev[Developer Agent: HTML/CSS]
        TaskBoard <--> Mktg[Marketing & Copywriting Agent]
        TaskBoard <--> Res[Market Research Agent]
        Dev --> Sandbox[(Isolated Sandbox: sandbox/)]
        Sandbox --> Reviewer[Quality Reviewer Agent: Automated Tests]
        Reviewer -- Approved / Rejected --> TaskBoard
        Reviewer -- Scores & Rewards --> RewardsTable[(Rewards & Standings)]
    end

    subgraph Infrastructure Layer [4. Health, Scaling & Safety Daemon]
        Monitor[System Monitor Daemon: Heartbeats & Caps] --> Reaping[Worker Death Reaping]
        Reaping --> HR[HR Agent: Auto-Replacement & Hiring]
        HR --> Dev
        HR --> Mktg
        HR --> Res
        Monitor --> KillSwitch[Emergency Global Kill Switch]
    end
```

---

## 2. The 11 Database Tables

| Table | Primary Columns | Purpose |
| :--- | :--- | :--- |
| **`agents`** | `id, role, team_id, status, score, last_heartbeat, replaced_by` | Registry of every agent, its health, reward score, and lineage. |
| **`role_specs`** | `role, system_prompt, tools_json, model_tier, max_steps, token_budget` | Templates cloned by HR to hire new agents. |
| **`teams`** | `id, name, manager_agent_id, min_headcount, max_headcount` | Department boundaries and staffing caps. |
| **`projects`** | `id, name, goal, status, budget_limit, owner_agent_id` | High-level projects created by the CEO. |
| **`tasks`** | `id, project_id, team_id, title, spec, status, owner_agent_id, attempts, depends_on` | Shared board enforcing `todo` ➔ `doing` ➔ `review` ➔ `done`. |
| **`events`** | `id, ts, agent_id, task_id, type, payload_json` | Append-only audit log for tracing and observability. |
| **`budget_ledger`**| `id, ts, agent_id, project_id, tokens, cost, tool_calls` | Financial ledger tracking token usage and cost against caps. |
| **`reviews`** | `id, task_id, reviewer_id, verdict, quality_score, notes` | Independent quality reviews and test results (0.0 to 10.0). |
| **`rewards`** | `id, agent_id, task_id, points, reason, ts` | Point history: bonuses for quality and penalties for rework. |
| **`blockers`** | `id, agent_id, task_id, type, priority, status, details, options` | Escalations requiring human sign-off. |
| **`credentials_registry`**| `name, scope, allowed_roles, vault_ref, last_used` | Secret permissions. Secrets stay vaulted; models never see passwords. |

---

## 3. The 5 Core Autonomous Loops

```mermaid
sequenceDiagram
    autonumber
    actor Human as Human Owner
    participant Liaison as Human Liaison
    participant Manager as Manager Agent
    participant Board as Task Board
    participant Worker as Worker (Dev/Mktg)
    participant Reviewer as Quality Reviewer
    participant Monitor as System Monitor
    participant HR as HR Agent

    Note over Manager,Board: Loop 1: Task Execution Loop
    Manager->>Board: Create task with dependencies
    Worker->>Board: Claim task atomically (todo -> doing)
    Worker->>Worker: Execute in sandbox
    Worker->>Board: Submit for review (doing -> review)

    Note over Reviewer,Board: Loop 4: Reward & Review Loop
    Reviewer->>Reviewer: Run automated tests in sandbox
    Reviewer->>Board: Approve task (review -> done)
    Reviewer->>Worker: Award reward points to agent score

    Note over Worker,HR: Loop 2: Health & Auto-Replacement Loop
    Worker-xWorker: Worker crashes / loses heartbeat (>30s)
    Monitor->>Board: Detect timeout, reap dead worker, reset task to todo
    Monitor->>HR: Trigger replacement request
    HR->>Worker: Spawn replacement agent from role_spec
    Worker->>Board: Replacement resumes task to completion

    Note over Liaison,Human: Loop 5: Blocker & Approval Gate Loop
    Worker->>Liaison: Flag sensitive action (public deployment)
    Liaison->>Human: Push Telegram blocker with action options
    Human->>Liaison: Approve & Publish
    Liaison->>Board: Unblock task (blocked -> done)
```

---

## 4. Security & Credential Vault Architecture
1. **Zero Secret Exposure**: LLM prompts and chat logs never receive raw API keys or passwords.
2. **Credential RBAC**: Tools check `credentials_registry` and inject secrets from the vault at invocation time only if the caller's role is permitted.
3. **Isolated Sandbox Execution**: File operations and code builds are restricted to `./sandbox/` with path traversal protections.
4. **Approval Gates**: Sensitive actions (spending funds, emailing customers, public deployments, credential rotation) require human sign-off via the Liaison.
