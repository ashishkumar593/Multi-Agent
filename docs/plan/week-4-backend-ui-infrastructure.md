# Week 4: Backend, UI, Docker & Cloud Deployment (Days 22–28)
**Detailed Day-by-Day Implementation Specifications**

---

## Day 22 — Production FastAPI Backend & Celery Worker

### 1. Objective
Develop the production-grade asynchronous REST API using FastAPI, SQLAlchemy 2.0, PostgreSQL persistence, Alembic migrations, and Celery background task processing.

### 2. Architecture & File Layout
```
src/db/
├── database.py
├── models/
│   ├── base.py
│   ├── user.py
│   ├── research.py
│   ├── document.py
│   └── report.py
└── migrations/
src/workers/
├── queue.py
└── tasks.py
src/api/
├── routes/
│   ├── health.py
│   ├── research.py
│   ├── documents.py
│   └── reports.py
└── schemas/
    ├── api_requests.py
    └── api_responses.py
tests/api/
└── test_api_endpoints.py
```

### 3. Step-by-Step Implementation Tasks
1. **SQLAlchemy Models (`src/db/models/`)**:
   - `User`: ID, email, hashed_password, created_at.
   - `ResearchJob`: ID, user_id, topic, status (`PENDING`, `RUNNING`, `COMPLETED`, `FAILED`), current_agent, progress_pct, error_message.
   - `Document`: ID, user_id, filename, file_hash, file_size, chunk_count, created_at.
   - `ResearchReport`: ID, job_id, title, markdown_content, json_metadata, created_at.
2. **Database Migrations (`src/db/migrations/`)**:
   - Initialize Alembic, configure `env.py` to auto-detect models, and generate baseline migration script.
3. **Celery Worker Setup (`src/workers/`)**:
   - `queue.py`: Celery instance connected to Redis broker (`settings.redis.url`).
   - `tasks.py`: Async task `execute_research_workflow(job_id, topic, scope, options)` that compiles LangGraph, runs the workflow, updates job status in PostgreSQL, and saves the final report.
4. **REST Endpoints (`src/api/routes/`)**:
   - `POST /api/v1/research`: Accepts research query, enqueues Celery task, returns `202 Accepted` with `job_id`.
   - `GET /api/v1/research/{job_id}`: Polls job status, progress percentage, active agent, and completion details.
   - `POST /api/v1/documents`: Uploads files, validates MIME types, triggers ingestion, and indexes chunks.
   - `GET /api/v1/documents`: Lists uploaded documents.
   - `GET /api/v1/reports/{report_id}`: Returns formatted research report.
   - `GET /health` & `GET /ready`: Health check probes.
5. **API Integration Tests (`tests/api/test_api_endpoints.py`)**:
   - Test full endpoint lifecycle using `httpx.AsyncClient`.

### 4. Verification & Testing Commands
```bash
alembic upgrade head
pytest tests/api/test_api_endpoints.py -v
```

### 5. Git Commit
```bash
git commit -m "feat: implement production FastAPI backend and Celery worker"
```

---

## Day 23 — Streamlit Research Dashboard & Live Visualizer

### 1. Objective
Build an interactive, intuitive Streamlit user interface communicating with the FastAPI backend, featuring real-time agent execution tracking and cited report inspection.

### 2. Architecture & File Layout
```
src/ui/
├── app.py
├── components/
│   ├── sidebar.py
│   ├── progress_bar.py
│   └── report_view.py
└── pages/
    ├── 1_New_Research.py
    ├── 2_Research_History.py
    ├── 3_Document_Library.py
    └── 4_Settings.py
src/tools/
└── pdf_export.py
```

### 3. Step-by-Step Implementation Tasks
1. **Application Shell (`src/ui/app.py`)**:
   - Configure page layout (wide mode, modern typography, custom CSS).
   - Display system overview, quick actions, and recent activity feed.
2. **New Research Page (`src/ui/pages/1_New_Research.py`)**:
   - Input forms for topic, scope, web search toggle, document RAG toggle, and depth settings.
   - Live Agent Progress Stepper: Visual indicators for Planner $\rightarrow$ Search $\rightarrow$ Analyst $\rightarrow$ Writer $\rightarrow$ Critic.
   - Real-time polling of backend `/api/v1/research/{job_id}`.
3. **Report Viewer & Citations Component (`src/ui/components/report_view.py`)**:
   - Render report markdown with collapsible evidence callouts for every citation.
   - Generate formatted data comparison tables.
   - Export options: Download as Markdown or PDF (via ReportLab / WeasyPrint).
4. **Document Library Page (`src/ui/pages/3_Document_Library.py`)**:
   - Drag-and-drop file upload with progress bar.
   - Table of indexed documents with chunk count and delete buttons.

### 4. Verification & Testing Commands
```bash
streamlit run src/ui/app.py --server.headless=true
```

### 5. Git Commit
```bash
git commit -m "feat: build complete Streamlit research dashboard"
```

---

## Day 24 — Dockerization & Local Infrastructure

### 1. Objective
Containerize all components into production-grade multi-stage Docker images and orchestrate a 6-service local stack using Docker Compose and Makefile automation.

### 2. Architecture & File Layout
```
Dockerfile
docker-compose.yml
.dockerignore
Makefile
infrastructure/docker/
├── entrypoint.sh
└── supervisord.conf
```

### 3. Step-by-Step Implementation Tasks
1. **Multi-Stage Dockerfile (`Dockerfile`)**:
   - Base stage: Python 3.11-slim, compile dependencies, curl.
   - Builder stage: Wheels installation, poetry/pip caching.
   - Final stage: Minimal runtime image, non-root user (`appuser:10001`), security hardening.
2. **Docker Compose (`docker-compose.yml`)**:
   - Services:
     - `api`: FastAPI application on port 8000.
     - `worker`: Celery distributed worker.
     - `ui`: Streamlit frontend on port 8501.
     - `postgres`: PostgreSQL 16 on port 5432 with persistent volume.
     - `redis`: Redis 7 on port 6379 for queues and cache.
     - `chromadb`: Persistent vector storage volume.
   - Define network `research_net`, health checks, and `restart: unless-stopped`.
3. **Automation Makefile (`Makefile`)**:
   - Define commands: `make install`, `make test`, `make lint`, `make typecheck`, `make docker-up`, `make docker-down`.

### 4. Verification & Testing Commands
```bash
docker compose config
docker compose up --build -d
docker compose ps
docker compose down
```

### 5. Git Commit
```bash
git commit -m "feat: dockerize complete platform with Docker Compose"
```

---

## Day 25 — GitHub Actions CI/CD Pipeline

### 1. Objective
Implement automated continuous integration and delivery pipelines enforcing code quality gates, test coverage, and Docker image builds.

### 2. Architecture & File Layout
```
.github/
└── workflows/
    ├── ci.yml
    └── cd.yml
```

### 3. Step-by-Step Implementation Tasks
1. **Continuous Integration Workflow (`.github/workflows/ci.yml`)**:
   - Triggers: Pull requests and pushes to `main`.
   - Jobs:
     - `lint-and-typecheck`: Runs `ruff check .` and `mypy src`.
     - `test-suite`: Sets up PostgreSQL & Redis services, runs `pytest --cov=src` with coverage reporting.
     - `security-scan`: Runs `pip-audit` for CVE detection.
     - `docker-build`: Tests building Docker images.
2. **Continuous Deployment Workflow (`.github/workflows/cd.yml`)**:
   - Deploys automatically to staging/production on tag creation or merge to main.
3. **Status Badges**:
   - Add CI, Coverage, and License badges to `README.md`.

### 4. Verification & Testing Commands
```bash
git push origin feature/day-25
# Inspect GitHub Actions run
```

### 5. Git Commit
```bash
git commit -m "ci: configure GitHub Actions CI/CD pipeline"
```

---

## Day 26 — Cloud Deployment on AWS EC2 with Nginx & SSL

### 1. Objective
Deploy the complete multi-service application to an AWS EC2 instance configured with Nginx reverse proxy, automated HTTPS (Let's Encrypt), and persistent volumes.

### 2. Architecture & File Layout
```
infrastructure/aws/
├── nginx.conf
└── user-data.sh
docs/
└── deployment.md
```

### 3. Step-by-Step Implementation Tasks
1. **EC2 Provisioning & Security Hardening (`infrastructure/aws/user-data.sh`)**:
   - Recommended instance: `t3.large` or `c6i.large` (2 vCPU, 4-8 GB RAM, 50 GB gp3 SSD).
   - Automated script installs Docker Engine, Docker Compose, Nginx, and UFW firewall.
   - UFW firewall rules: Allow SSH (22), HTTP (80), HTTPS (443); block all direct access to 5432, 6379, 8000, 8501.
2. **Nginx Reverse Proxy (`infrastructure/aws/nginx.conf`)**:
   - Route `/api` and `/docs` to FastAPI backend (`http://localhost:8000`).
   - Route `/` to Streamlit frontend (`http://localhost:8501`) with WebSocket proxy headers (`Upgrade $http_upgrade`).
3. **SSL Certificate Automation**:
   - Integrate Certbot for Let's Encrypt SSL certificates with automatic renewal cron.
4. **Operations & Backup Guide (`docs/deployment.md`)**:
   - S3 backup script for PostgreSQL database dumps and ChromaDB embeddings.
   - Cost estimates in USD and INR.

### 4. Verification & Testing Commands
```bash
# On server:
sudo nginx -t
sudo systemctl reload nginx
curl -k https://localhost/health
```

### 5. Git Commit
```bash
git commit -m "feat: configure AWS EC2 deployment and Nginx reverse proxy"
```

---

## Day 27 — Recruiter-Ready Documentation & Architecture

### 1. Objective
Create comprehensive, polished, recruiter-ready project documentation including architecture diagrams, API specifications, and design rationale.

### 2. Architecture & File Layout
```
README.md
docs/
├── architecture.md
├── api.md
├── decisions.md
└── deployment.md
```

### 3. Step-by-Step Implementation Tasks
1. **Root `README.md`**:
   - High-impact project summary, system overview, live demo links, key metrics.
   - Mermaid diagrams: System Architecture, LangGraph State Machine, Hybrid RAG Flow.
   - Quickstart guide: Single-command local launch via Docker Compose.
   - Technology selection rationale and benchmark performance.
2. **Technical Architecture (`docs/architecture.md`)**:
   - Deep dive into state transitions, error recovery mechanisms, and multi-agent coordination.
3. **API Reference (`docs/api.md`)**:
   - Complete endpoint documentation with sample JSON request and response payloads.
4. **Architecture Decision Records (`docs/decisions.md`)**:
   - Document ADRs for: LangGraph vs plain LangChain, ChromaDB vs pgvector, Celery vs FastAPI BackgroundTasks.

### 4. Verification & Testing Commands
```bash
# Verify markdown formatting and relative links
```

### 5. Git Commit
```bash
git commit -m "docs: create comprehensive production documentation"
```

---

## Day 28 — Final Portfolio Audit, Interview Prep & Demo Script

### 1. Objective
Perform final end-to-end verification across all components, finalize portfolio artifacts, and prepare technical interview demonstrations.

### 2. Architecture & File Layout
```
docs/
├── final_audit.md
└── interview_guide.md
tests/e2e/
└── test_full_workflow.py
```

### 3. Step-by-Step Implementation Tasks
1. **End-to-End System Testing (`tests/e2e/test_full_workflow.py`)**:
   - End-to-end simulation: User submits topic $\rightarrow$ API creates job $\rightarrow$ Celery worker executes graph $\rightarrow$ Planner decomposes $\rightarrow$ Search retrieves $\rightarrow$ Analyst synthesizes $\rightarrow$ Writer produces cited report $\rightarrow$ Critic verifies $\rightarrow$ Report is stored in PostgreSQL and retrieved via API.
2. **Portfolio & Resume Artifacts (`docs/interview_guide.md`)**:
   - **3 Resume Bullet Points**: Action-oriented, quantified impact bullet points highlighting multi-agent orchestration, hybrid RAG optimization, and asynchronous backend design.
   - **60-Second Video Demo Script**: High-tempo walkthrough showcasing topic submission, real-time agent progression, and verifiable report citations.
   - **Technical Interview Q&A**: 8 in-depth questions and answers addressing state management, hallucination mitigation, RRF math, and distributed job resilience.
3. **Final Audit Report (`docs/final_audit.md`)**:
   - Verification that all 29 items of the Production Quality Checklist are complete.

### 4. Verification & Testing Commands
```bash
pytest tests/e2e/test_full_workflow.py -v
```

### 5. Git Commit
```bash
git commit -m "chore: complete final project audit and portfolio preparation"
```
