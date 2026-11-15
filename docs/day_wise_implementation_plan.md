# AI Research & Report Agent — 28-Day Master Implementation Plan
**Production-Grade Multi-Agent AI System Architecture & Engineering Roadmap**

---

## 1. Executive Summary & Architectural Vision

The **AI Research & Report Agent** is an enterprise-grade autonomous research platform. Unlike toy RAG or demonstration-tier LangChain scripts, this system is engineered from the ground up as a resilient, observable, cost-optimized, and secure multi-agent platform capable of deep web and document investigation.

### Core Capabilities
1. **Intelligent Query Decomposition**: Breaks open-ended research topics into prioritized, structured sub-questions with clear evidence requirements.
2. **Hybrid Multi-Source Retrieval**: Fuses dense semantic vector search (ChromaDB) with sparse lexical search (BM25) via Reciprocal Rank Fusion (RRF), followed by Cross-Encoder neural reranking.
3. **Multi-Agent Orchestration via LangGraph**: Coordinated stateful workflow featuring Planner, Search, Analyst, Writer, and Critic agents with conditional cyclic routing, checkpointing, and human-in-the-loop readiness.
4. **Source Provenance & Citation Validation**: Every factual claim is programmatically traced to evidence IDs and verifiable sources. Claims lacking evidence or exhibiting contradictions are flagged and sent for targeted re-retrieval.
5. **Production Backend & Asynchronous Execution**: FastAPI REST API decoupled from execution via Celery background workers and Redis queues, backed by PostgreSQL for state, documents, metadata, and reports.
6. **Enterprise Security & Guardrails**: Defenses against prompt injection, SSRF, path traversal, malicious uploads, and untrusted web content.
7. **Empirical Evaluation**: Systematic benchmarking using RAGAS, custom ground-truth datasets, and LangSmith observability.
8. **Cloud-Native Deployment**: Containerized with Docker Compose, automated via GitHub Actions CI/CD, and ready for deployment on AWS EC2 with Nginx and SSL.

---

## 2. System Architecture & Tech Stack

### High-Level Architecture Diagram

```mermaid
flowchart TD
    User([User / Browser]) <--> UI[Streamlit UI / Frontend]
    UI <--> API[FastAPI REST API / Reverse Proxy]
    API <--> Postgres[(PostgreSQL Primary DB)]
    API <--> RedisQueue[(Redis Queue / Cache)]
    
    subgraph Background Workers [Celery Distributed Execution]
        Worker[Celery Research Worker]
        LangGraphCore[LangGraph Workflow Engine]
        Worker --> LangGraphCore
    end
    
    RedisQueue <--> Worker
    
    subgraph Multi-Agent Subsystem [LangGraph Orchestration]
        Planner[Planner Agent] --> Search[Search Agent]
        Search --> Analyst[Analyst Agent]
        Analyst --> Writer[Writer Agent]
        Writer --> Critic[Critic Agent]
        Critic -- "Unsupported Claims / Low Quality" --> Writer
        Critic -- "Missing Evidence / Gaps" --> Search
        Critic -- "Approved" --> Complete([Final Report Output])
    end
    
    LangGraphCore --> Multi-Agent Subsystem
    
    subgraph Knowledge & Retrieval Engine [Hybrid RAG & Web Engine]
        Search <--> WebSearch[Tavily Search + Webpage Reader]
        Search <--> HybridRetriever[Hybrid Retriever: BM25 + Dense RRF]
        HybridRetriever --> Chroma[(ChromaDB Vector Store)]
        HybridRetriever --> CrossEncoder[Cross-Encoder Reranker]
    end
    
    Complete --> ReportSvc[Report Service: PDF / Markdown Export]
    ReportSvc --> Postgres
    LangGraphCore -. Checkpoints .-> Postgres
```

### Technology Matrix

| Layer | Component | Version / Specification | Justification |
| :--- | :--- | :--- | :--- |
| **Language** | Python | `>=3.11, <3.13` | Modern typing, performance gains, `asyncio` task groups. |
| **Orchestration** | LangGraph | `>=0.2.0` | Cyclic graphs, persistence, state transitions, fault-tolerant retries. |
| **API Backend** | FastAPI + Pydantic v2 | FastAPI `>=0.115`, Pydantic `>=2.9` | High performance, async REST, automatic OpenAPI schema generation. |
| **Primary Database** | PostgreSQL + SQLAlchemy 2.0 | PostgreSQL 16, asyncpg | Persistent relational storage for jobs, users, reports, evidence, provenance. |
| **Migrations** | Alembic | `>=1.13` | Versioned schema migrations for production reliability. |
| **Vector Database** | ChromaDB | `>=0.5.0` | Embeddings persistence, metadata filtering, local/container deployment. |
| **Lexical Retrieval** | `rank-bm25` | `>=0.2.2` | Sparse keyword matching for technical terms, entities, and IDs. |
| **Reranking** | Sentence Transformers | `cross-encoder/ms-marco-MiniLM-L-6-v2` | High-precision passage reranking over hybrid candidate pools. |
| **Queue & Cache** | Celery + Redis | Celery 5.4+, Redis 7+ | Decoupled long-running research jobs from HTTP request lifecycle. |
| **Web Research** | Tavily API + BeautifulSoup4 | Tavily Python SDK + BS4 / Readability | Clean web search and SSRF-hardened main-article scraping. |
| **Document Processing**| PyMuPDF, python-docx | PyMuPDF (fitz), python-docx | High-fidelity PDF/DOCX page-level extraction with layout awareness. |
| **Frontend** | Streamlit | `>=1.38.0` | Fast, reactive dashboard for research visualization and reports. |
| **Evaluation** | RAGAS + LangSmith | RAGAS `>=0.1.15`, LangSmith | Ground-truth benchmarking and deep distributed trace telemetry. |
| **Containerization** | Docker & Compose | Docker Engine 26+, Compose v2 | Reproducible multi-service local and server deployment. |
| **CI/CD** | GitHub Actions | Ubuntu Latest Runner | Automated linting, type-checking, unit testing, and Docker builds. |

---

## 3. Target Repository Structure

```
ai-research-agent/
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── cd.yml
├── data/
│   ├── raw/
│   ├── processed/
│   └── evaluation/
│       ├── questions.jsonl
│       └── README.md
├── docs/
│   ├── day_wise_implementation_plan.md
│   ├── architecture.md
│   ├── agent-workflow.md
│   ├── decisions.md
│   ├── api.md
│   ├── week-1-review.md
│   ├── week-2-review.md
│   ├── week-3-review.md
│   └── deployment.md
├── infrastructure/
│   ├── docker/
│   │   ├── Dockerfile.api
│   │   ├── Dockerfile.worker
│   │   └── Dockerfile.ui
│   └── aws/
│       ├── nginx.conf
│       └── user-data.sh
├── scripts/
│   ├── ingest_sample.py
│   ├── run_evaluation.py
│   ├── benchmark_retrieval.py
│   └── seed_db.py
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── logging.py
│   │   ├── exceptions.py
│   │   ├── security.py
│   │   ├── middleware.py
│   │   └── dependencies.py
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── planner.py
│   │   ├── search.py
│   │   ├── analyst.py
│   │   ├── writer.py
│   │   ├── critic.py
│   │   ├── state.py
│   │   ├── prompts/
│   │   │   ├── __init__.py
│   │   │   ├── planner_prompts.py
│   │   │   ├── analyst_prompts.py
│   │   │   ├── writer_prompts.py
│   │   │   └── critic_prompts.py
│   │   └── schemas/
│   │       ├── __init__.py
│   │       ├── plan.py
│   │       ├── evidence.py
│   │       ├── analysis.py
│   │       └── report.py
│   ├── graph/
│   │   ├── __init__.py
│   │   ├── state.py
│   │   ├── nodes.py
│   │   ├── edges.py
│   │   ├── workflow.py
│   │   └── checkpoint.py
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── loaders.py
│   │   ├── chunker.py
│   │   ├── embeddings.py
│   │   ├── store.py
│   │   ├── bm25.py
│   │   ├── retriever.py
│   │   ├── reranker.py
│   │   ├── citations.py
│   │   └── pipeline.py
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── web_search.py
│   │   ├── webpage_reader.py
│   │   ├── document_search.py
│   │   ├── pdf_export.py
│   │   └── source_validator.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── research_service.py
│   │   ├── document_service.py
│   │   ├── report_service.py
│   │   └── evaluation_service.py
│   ├── db/
│   │   ├── __init__.py
│   │   ├── database.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── research.py
│   │   │   ├── document.py
│   │   │   ├── evidence.py
│   │   │   └── report.py
│   │   ├── repositories/
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── research_repo.py
│   │   │   └── document_repo.py
│   │   └── migrations/
│   ├── workers/
│   │   ├── __init__.py
│   │   ├── queue.py
│   │   └── tasks.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── health.py
│   │   │   ├── research.py
│   │   │   ├── documents.py
│   │   │   └── reports.py
│   │   └── schemas/
│   │       ├── __init__.py
│   │       ├── api_requests.py
│   │       └── api_responses.py
│   ├── eval/
│   │   ├── __init__.py
│   │   ├── dataset.py
│   │   ├── run_eval.py
│   │   ├── metrics.py
│   │   └── experiments.py
│   └── ui/
│       ├── app.py
│       ├── components/
│       │   ├── sidebar.py
│       │   ├── progress_bar.py
│       │   └── report_view.py
│       └── pages/
│           ├── 1_New_Research.py
│           ├── 2_Research_History.py
│           ├── 3_Document_Library.py
│           └── 4_Settings.py
├── tests/
│   ├── conftest.py
│   ├── unit/
│   │   ├── test_config.py
│   │   ├── test_chunker.py
│   │   ├── test_loaders.py
│   │   └── test_bm25.py
│   ├── integration/
│   │   ├── test_chroma.py
│   │   ├── test_hybrid_retriever.py
│   │   └── test_database.py
│   ├── agents/
│   │   ├── test_planner.py
│   │   ├── test_analyst.py
│   │   └── test_writer.py
│   ├── rag/
│   │   └── test_rag_pipeline.py
│   ├── security/
│   │   ├── test_ssrf.py
│   │   └── test_injection.py
│   └── e2e/
│       └── test_full_workflow.py
├── .dockerignore
├── .env.example
├── .gitignore
├── docker-compose.yml
├── Dockerfile
├── Makefile
├── pyproject.toml
└── README.md
```

---

## 4. 28-Day Granular Implementation Plan

---

### WEEK 1: Foundation and Production RAG Engine (Days 1–7)

#### Day 1 — Project Foundation, Tooling, Config & Logging
- **Primary Goal**: Initialize the modular repository, virtual environment, type system, centralized Pydantic settings, exception hierarchy, and structured logging.
- **Tasks**:
  1. Initialize Git repository and create directory structure.
  2. Setup `pyproject.toml` with strict dependencies, Ruff (linter/formatter), Mypy (strict typing), and Pytest configurations.
  3. Implement `src/core/config.py` using `pydantic-settings` with distinct development, testing, and production profiles.
  4. Create `src/core/logging.py` featuring JSON structured logging with contextual `request_id` and agent tracking.
  5. Implement `src/core/exceptions.py` establishing the application-wide error hierarchy.
  6. Create `.env.example`, `.gitignore`, `docs/architecture.md`, and `docs/decisions.md`.
  7. Add baseline unit tests in `tests/unit/test_config.py`.
- **Target Deliverables**:
  - `pyproject.toml`, `.env.example`, `.gitignore`
  - `src/core/config.py`, `src/core/logging.py`, `src/core/exceptions.py`
  - `docs/architecture.md`, `docs/decisions.md`
  - `tests/unit/test_config.py`
- **Acceptance Criteria**:
  - `ruff check .` returns 0 errors.
  - `mypy src` passes with no type errors.
  - `pytest tests/` passes.
- **Git Commit**: `chore: initialize production project architecture`

---

#### Day 2 — Production Document Ingestion Pipeline
- **Primary Goal**: Build a resilient, secure document ingestion engine that extracts text and metadata from PDF, DOCX, TXT, and Markdown files with chunking and deduplication.
- **Tasks**:
  1. Implement `src/rag/loaders.py` using PyMuPDF and python-docx. Extract page numbers, titles, and creation timestamps.
  2. Add file security validation: check MIME types via magic bytes, enforce 25MB file limits, and prevent directory traversal.
  3. Implement `src/rag/chunker.py`: Recursive token/character splitting with an 800-token target, 100-token overlap, preserving paragraph boundaries.
  4. Implement `src/rag/ingest.py`: Deduplicate files using SHA-256 hashes, generate deterministic UUID5s for documents and chunks, and track ingestion state.
  5. Build CLI script `scripts/ingest_sample.py` and write unit tests in `tests/unit/test_loaders.py` and `test_chunker.py`.
- **Target Deliverables**:
  - `src/rag/loaders.py`, `src/rag/chunker.py`, `src/rag/ingest.py`
  - `tests/unit/test_loaders.py`, `tests/unit/test_chunker.py`
  - `scripts/ingest_sample.py`
- **Acceptance Criteria**:
  - Ingestion successfully parses multi-page PDFs with accurate page metadata.
  - Corrupted files and unsupported extensions fail gracefully with structured error messages.
  - Duplicate ingestion of the same file is idempotent and generates identical content hashes.
- **Git Commit**: `feat: implement document ingestion pipeline`

---

#### Day 3 — Embeddings & ChromaDB Persistence
- **Primary Goal**: Construct an embedding abstraction layer with batching, rate-limit resilience, and persistent ChromaDB storage.
- **Tasks**:
  1. Implement `src/rag/embeddings.py`: Abstract `BaseEmbeddingProvider` with concrete `OpenAIEmbeddingProvider` (`text-embedding-3-small` / `large`) and retry/exponential backoff.
  2. Implement `src/rag/store.py`: `ChromaVectorStore` wrapper managing persistent collections, incremental upserts, metadata filtering, and ID-based retrieval.
  3. Ensure idempotency: avoid inserting duplicate chunks using SHA-256 chunk IDs.
  4. Update `scripts/ingest_sample.py` to embed documents and save to disk.
  5. Write integration tests in `tests/integration/test_chroma.py`.
- **Target Deliverables**:
  - `src/rag/embeddings.py`, `src/rag/store.py`
  - `tests/integration/test_chroma.py`
  - Updated `scripts/ingest_sample.py`
- **Acceptance Criteria**:
  - Chunks are successfully vectorized and stored in a persistent directory.
  - Similarity queries return relevant chunks with similarity distances and complete metadata.
  - Rate limits are retried smoothly using tenacity.
- **Git Commit**: `feat: integrate embeddings and ChromaDB`

---

#### Day 4 — Advanced Hybrid Retrieval & Reranking
- **Primary Goal**: Implement a 4-stage retrieval pipeline combining dense semantic retrieval, sparse BM25 retrieval, Reciprocal Rank Fusion (RRF), and Cross-Encoder reranking.
- **Tasks**:
  1. Implement `src/rag/bm25.py`: Tokenized BM25 index with serialization/deserialization for persistence.
  2. Implement `src/rag/reranker.py`: Cross-Encoder wrapper utilizing `ms-marco-MiniLM-L-6-v2` with batch scoring and fallback handling.
  3. Implement `src/rag/retriever.py`: Hybrid search executing dense and sparse queries, merging with RRF (`score = 1 / (60 + rank)`), and reranking top candidates.
  4. Create evaluation comparison script `scripts/benchmark_retrieval.py` testing vector-only vs BM25 vs hybrid vs reranked.
  5. Write tests in `tests/integration/test_hybrid_retriever.py`.
- **Target Deliverables**:
  - `src/rag/bm25.py`, `src/rag/reranker.py`, `src/rag/retriever.py`
  - `scripts/benchmark_retrieval.py`
  - `tests/integration/test_hybrid_retriever.py`
- **Acceptance Criteria**:
  - Hybrid RRF correctly surfaces keyword-specific technical terms missed by pure vector search.
  - Cross-Encoder ranks the most relevant passage at rank 1 on evaluation queries.
  - Empty search results or missing models trigger graceful fallbacks without raising 500 errors.
- **Git Commit**: `feat: implement hybrid retrieval and reranking`

---

#### Day 5 — Production Grounded RAG Pipeline with Citation Validation
- **Primary Goal**: Complete the document RAG generation pipeline with structured output, context token budgeting, and strict inline citation validation.
- **Tasks**:
  1. Implement `src/rag/citations.py`: Registry mapping source chunks to bracketed references (`[1]`, `[2]`), validating claim-to-source integrity.
  2. Implement `src/rag/pipeline.py`: Assembles context with strict token bounds, formats prompt with evidence, invokes LLM with Pydantic output schema, and verifies citations.
  3. Add insufficient-context detection: when retrieved context does not answer the question, output an explicit grounded disclaimer instead of hallucinating.
  4. Add unit and integration tests in `tests/rag/test_rag_pipeline.py`.
- **Target Deliverables**:
  - `src/rag/citations.py`, `src/rag/pipeline.py`
  - `tests/rag/test_rag_pipeline.py`
- **Acceptance Criteria**:
  - Generated answers include exact numbered citations resolving to real retrieved chunks.
  - Queries with zero matching context return "I don't know based on the provided documents".
  - Hallucinated or non-existent citation numbers are automatically rejected.
- **Git Commit**: `feat: implement cited RAG pipeline`

---

#### Day 6 — Production Web Research Toolkit
- **Primary Goal**: Develop a secure, rate-limited web search and webpage scraping toolkit with SSRF protection and source credibility analysis.
- **Tasks**:
  1. Implement `src/tools/web_search.py`: Tavily search integration with search depth control, rate limiting, and output normalization into `WebSearchResult`.
  2. Implement `src/tools/webpage_reader.py`: Scraper using BeautifulSoup4 and readability algorithms, stripping scripts, ads, navigation, and extracting clean markdown.
  3. Implement `src/tools/source_validator.py`: SSRF filter blocking private IP ranges (`127.0.0.1`, `10.0.0.0/8`, `192.168.0.0/16`, AWS metadata `169.254.169.254`), validating domains and scoring credibility.
  4. Build CLI research test script `scripts/test_web_tools.py`.
  5. Add unit and security tests in `tests/security/test_ssrf.py`.
- **Target Deliverables**:
  - `src/tools/web_search.py`, `src/tools/webpage_reader.py`, `src/tools/source_validator.py`
  - `tests/security/test_ssrf.py`, `scripts/test_web_tools.py`
- **Acceptance Criteria**:
  - Web searches return normalized results with title, URL, published date, and clean text.
  - SSRF test verifies that queries to `localhost`, internal IPs, and metadata endpoints are blocked.
  - Inaccessible or timed-out webpages fail gracefully without crashing the scraper.
- **Git Commit**: `feat: add web research tools`

---

#### Day 7 — Week 1 Engineering Audit & Quality Gate
- **Primary Goal**: Perform a rigorous audit of the Week 1 codebase, verifying test coverage, fixing security flaws, and auditing performance.
- **Tasks**:
  1. Run Ruff and Mypy across all Week 1 files (`src/core`, `src/rag`, `src/tools`).
  2. Run `pytest --cov=src` and verify coverage exceeds 80%.
  3. Audit memory leaks in ChromaDB and Cross-Encoder model loading.
  4. Fix the top 5 identified architectural and code quality issues.
  5. Compile `docs/week-1-review.md` summarizing benchmarks, test results, and decisions.
- **Target Deliverables**:
  - `docs/week-1-review.md`
  - Code fixes and refactors across `src/rag/` and `src/tools/`
- **Acceptance Criteria**:
  - All unit and integration tests pass with 0 failures.
  - Zero Mypy type-checking errors under strict mode.
  - Audit report documented with reproducible commands and performance benchmarks.
- **Git Commit**: `test: complete week one engineering audit`

---

### WEEK 2: Multi-Agent AI System via LangGraph (Days 8–14)

#### Day 8 — LangGraph State Management & System Architecture
- **Primary Goal**: Design and implement the strongly-typed shared state schema, agent input/output contracts, and workflow graphs.
- **Tasks**:
  1. Implement `src/agents/state.py` and `src/graph/state.py` defining `ResearchState` (TypedDict and Pydantic models).
  2. Define schemas in `src/agents/schemas/`: `ResearchPlan`, `SubQuestion`, `EvidenceItem`, `AnalysisReport`, `ReportDraft`, and `CriticFeedback`.
  3. Formulate graph transition rules, iteration caps (max 2 search refinement loops), and error recovery contracts.
  4. Generate Mermaid workflow diagram and document architecture in `docs/agent-workflow.md`.
  5. Write state validation tests in `tests/agents/test_state.py`.
- **Target Deliverables**:
  - `src/agents/state.py`, `src/graph/state.py`
  - `src/agents/schemas/` (`plan.py`, `evidence.py`, `analysis.py`, `report.py`)
  - `docs/agent-workflow.md`, `tests/agents/test_state.py`
- **Acceptance Criteria**:
  - State transitions are immutable and type-checked via Pydantic v2.
  - Schemas validate complex nested research payloads without data loss.
- **Git Commit**: `feat: implement LangGraph state and schema architecture`

---

#### Day 9 — Planner Agent Implementation
- **Primary Goal**: Build the Planner Agent that analyzes open-ended research topics, deduces objectives, and decomposes them into 4–8 prioritized sub-questions.
- **Tasks**:
  1. Implement `src/agents/prompts/planner_prompts.py` with structured reasoning instructions and few-shot examples.
  2. Implement `src/agents/planner.py` using LLM structured outputs (via Pydantic).
  3. Define query categorization: identify required evidence types (academic, industry, news, internal docs).
  4. Add resilience: fallback strategies for ambiguous queries, retries on invalid JSON schemas.
  5. Write unit tests in `tests/agents/test_planner.py` covering broad, technical, and ambiguous topics.
- **Target Deliverables**:
  - `src/agents/planner.py`, `src/agents/prompts/planner_prompts.py`
  - `tests/agents/test_planner.py`
- **Acceptance Criteria**:
  - Generates 4–8 distinct, non-overlapping, prioritized sub-questions for complex topics.
  - Correctly flags whether internal document RAG, web search, or both are required.
- **Git Commit**: `feat: implement planner agent`

---

#### Day 10 — Search Agent Implementation
- **Primary Goal**: Build the Search Agent to asynchronously execute web and document searches for all sub-questions in parallel with deduplication.
- **Tasks**:
  1. Implement `src/agents/search.py`: Asynchronous dispatch across Tavily Web Search and internal Hybrid RAG retriever.
  2. Implement concurrency limits (`asyncio.Semaphore`) to avoid provider rate limiting.
  3. Unify external and internal results into a standardized `EvidenceItem` schema with unique `evidence_id`, source URL/document, page, and timestamp.
  4. Add deduplication of overlapping URLs and identical content chunks.
  5. Write tests in `tests/agents/test_search.py` with mocked web and vector search responses.
- **Target Deliverables**:
  - `src/agents/search.py`
  - `tests/agents/test_search.py`
- **Acceptance Criteria**:
  - Queries execute concurrently without blocking the main event loop.
  - Partial tool failure (e.g., one web search fails) does not crash the overall search process.
  - All returned evidence records maintain exact provenance.
- **Git Commit**: `feat: implement search agent`

---

#### Day 11 — Analyst Agent Implementation
- **Primary Goal**: Implement the Analyst Agent to synthesize retrieved evidence, detect factual contradictions, extract claims, and score evidence confidence.
- **Tasks**:
  1. Implement `src/agents/prompts/analyst_prompts.py` directing critical synthesis, claim extraction, and bias identification.
  2. Implement `src/agents/analyst.py`: Group evidence by sub-question, extract concrete claims with supporting and contradicting evidence IDs.
  3. Assign confidence ratings (`High`, `Medium`, `Low`) based on source authority and corroboration.
  4. Highlight missing evidence or unverified assertions for potential refinement loops.
  5. Write tests in `tests/agents/test_analyst.py` testing contradictory inputs and consensus synthesis.
- **Target Deliverables**:
  - `src/agents/analyst.py`, `src/agents/prompts/analyst_prompts.py`
  - `tests/agents/test_analyst.py`
- **Acceptance Criteria**:
  - Disparate sources reporting conflicting numbers (e.g., market growth estimates) are explicitly identified as contradictory.
  - Every extracted claim references at least one valid `evidence_id`.
- **Git Commit**: `feat: implement analyst agent`

---

#### Day 12 — Writer Agent & Report Generation
- **Primary Goal**: Implement the Writer Agent to generate structured research reports with inline citations, comparison tables, and complete references.
- **Tasks**:
  1. Implement `src/agents/prompts/writer_prompts.py` establishing formal academic/executive prose style and markdown formatting standards.
  2. Implement `src/agents/writer.py`: Generates Executive Summary, Methodology, Detailed Findings, Comparison Tables, Limitations, and References.
  3. Integrate deterministic citation formatting: maps evidence IDs to numbered brackets `[1]`, `[2]` and builds a final bibliography.
  4. Add Markdown and structured JSON export validation.
  5. Write tests in `tests/agents/test_writer.py` verifying citation coverage and section completeness.
- **Target Deliverables**:
  - `src/agents/writer.py`, `src/agents/prompts/writer_prompts.py`
  - `tests/agents/test_writer.py`
- **Acceptance Criteria**:
  - The generated report contains all required sections without placeholders.
  - 100% of factual assertions cite an evidence reference listed in the bibliography.
- **Git Commit**: `feat: implement writer agent and report generation`

---

#### Day 13 — Complete Multi-Agent LangGraph Orchestration
- **Primary Goal**: Wire all agents into an executable LangGraph workflow with conditional routing, PostgreSQL/memory checkpointing, and CLI execution.
- **Tasks**:
  1. Implement `src/graph/nodes.py`: Wraps Planner, Search, Analyst, Writer, and Critic into callable graph nodes.
  2. Implement `src/graph/edges.py`: Conditional routing logic checking for missing evidence or critic rejections.
  3. Implement `src/graph/checkpoint.py`: Checkpointer for session persistence and workflow recovery.
  4. Implement `src/graph/workflow.py`: Compiles the `StateGraph` into a runnable application.
  5. Create CLI runner `scripts/run_research.py` displaying live status, agent transitions, and saving reports.
  6. Write integration tests in `tests/agents/test_graph_workflow.py`.
- **Target Deliverables**:
  - `src/graph/nodes.py`, `src/graph/edges.py`, `src/graph/checkpoint.py`, `src/graph/workflow.py`
  - `scripts/run_research.py`
  - `tests/agents/test_graph_workflow.py`
- **Acceptance Criteria**:
  - State flows through Planner -> Search -> Analyst -> Writer -> Critic -> End.
  - If evidence is flagged as insufficient, the workflow cycles back to Search (capped at 2 iterations).
  - Interrupted runs can be resumed from saved checkpoints.
- **Git Commit**: `feat: wire full multi-agent LangGraph workflow`

---

#### Day 14 — Critic Agent & Week 2 Review
- **Primary Goal**: Implement the Critic Agent for adversarial fact-checking and perform a comprehensive Week 2 system audit.
- **Tasks**:
  1. Implement `src/agents/critic.py`: Evaluates reports for unsupported claims, hallucinated citations, missing context, and logical consistency.
  2. Integrate Critic decision into LangGraph: `approved` routes to End; `rejected` triggers one targeted revision by Writer or Search.
  3. Enforce loop termination: prevent infinite loops by capping total iterations.
  4. Audit Days 8–13: run unit and integration test suites, check type hints, and benchmark end-to-end execution.
  5. Write `docs/week-2-review.md`.
- **Target Deliverables**:
  - `src/agents/critic.py`, `src/agents/prompts/critic_prompts.py`
  - `docs/week-2-review.md`
- **Acceptance Criteria**:
  - Critic detects deliberately injected unsupported claims and requests revisions.
  - End-to-end workflow produces verified reports from raw topics.
  - Week 2 audit passes with zero critical failures.
- **Git Commit**: `feat: implement critic agent and complete week two review`

---

### WEEK 3: Evaluation, Security and Optimization (Days 15–21)

#### Day 15 — Research & RAG Evaluation Dataset
- **Primary Goal**: Create a gold-standard evaluation dataset with verified ground truth to benchmark retrieval and generation performance.
- **Tasks**:
  1. Implement `src/eval/dataset.py`: Generator and validator for evaluation records.
  2. Curate 50 multi-faceted questions in `data/evaluation/questions.jsonl` categorized by difficulty (Easy, Medium, Hard).
  3. Include query archetypes: direct factual, comparative across documents, unanswerable queries, and queries with contradictory evidence.
  4. Create `data/evaluation/README.md` defining ground-truth verification guidelines.
  5. Add test in `tests/unit/test_eval_dataset.py` to validate dataset schema integrity.
- **Target Deliverables**:
  - `src/eval/dataset.py`
  - `data/evaluation/questions.jsonl`, `data/evaluation/README.md`
  - `tests/unit/test_eval_dataset.py`
- **Acceptance Criteria**:
  - 50 validated evaluation questions with verified ground-truth answers and citations.
  - Dataset schema adheres strictly to Pydantic evaluation models.
- **Git Commit**: `feat: create evaluation dataset and validation framework`

---

#### Day 16 — RAGAS Automated Evaluation Framework
- **Primary Goal**: Implement an automated evaluation pipeline measuring Faithfulness, Answer Relevancy, Context Precision, and Context Recall using RAGAS.
- **Tasks**:
  1. Implement `src/eval/run_eval.py`: Executes RAGAS metrics over `data/evaluation/questions.jsonl`.
  2. Implement `src/eval/metrics.py`: Custom metrics for Citation Precision (percentage of citations that resolve correctly) and Hallucination Rate.
  3. Implement results exporter saving raw JSON, aggregate CSV, and a summary Markdown report.
  4. Run baseline evaluation and document initial scores.
- **Target Deliverables**:
  - `src/eval/run_eval.py`, `src/eval/metrics.py`
  - `reports/evaluation_baseline.csv`, `reports/evaluation_baseline.md`
- **Acceptance Criteria**:
  - Pipeline executes without manual intervention and outputs measurable benchmark scores.
  - Citation precision and context recall metrics are quantified.
- **Git Commit**: `feat: implement RAGAS evaluation pipeline`

---

#### Day 17 — Retrieval Optimization Experiments
- **Primary Goal**: Run controlled empirical experiments across chunk sizes, retrieval strategies, and reranking parameters.
- **Tasks**:
  1. Implement `src/eval/experiments.py`: Grid-search runner testing:
     - Chunk sizes: 500, 800, 1200 tokens.
     - Strategies: Dense-only, BM25-only, Hybrid RRF, Hybrid RRF + Cross-Encoder.
  2. Measure Recall@5, Recall@10, Mean Reciprocal Rank (MRR), nDCG, and query latency.
  3. Generate comparative markdown tables and export CSV data.
  4. Document the optimal production configuration in `docs/decisions.md`.
- **Target Deliverables**:
  - `src/eval/experiments.py`
  - `reports/retrieval_experiments.csv`
  - Updated `docs/decisions.md`
- **Acceptance Criteria**:
  - Measurable comparison proving Hybrid RRF + Reranking outperforms vector-only search.
  - Optimal chunk size and reranker top-k selected based on empirical data.
- **Git Commit**: `feat: conduct retrieval optimization experiments`

---

#### Day 18 — Production Security & AI Guardrails
- **Primary Goal**: Harden the system against prompt injections, SSRF, malicious file uploads, PII exposure, and unsafe tool invocations.
- **Tasks**:
  1. Implement `src/core/security.py`: File upload sanitization, path traversal prevention, and input length constraints.
  2. Implement prompt isolation: demarcate untrusted web and document content with XML tags (`<untrusted_content>`) in prompts.
  3. Enforce strict tool permissions and domain allowlists/denylists.
  4. Write 20 adversarial tests in `tests/security/test_security_suite.py` (indirect prompt injection, SSRF, malicious PDF bombs, path traversal).
- **Target Deliverables**:
  - `src/core/security.py`
  - `tests/security/test_security_suite.py`
- **Acceptance Criteria**:
  - All 20 adversarial attack payloads are successfully mitigated or rejected.
  - Untrusted documents containing instructions like "ignore previous instructions" fail to hijack agent behavior.
- **Git Commit**: `feat: implement production security and AI guardrails`

---

#### Day 19 — Observability & Tracing via LangSmith
- **Primary Goal**: Integrate deep telemetry, distributed tracing, token counting, cost tracking, and structured metrics.
- **Tasks**:
  1. Configure LangSmith integration across all LangGraph nodes and RAG pipelines.
  2. Implement latency and token profiling middleware in `src/core/middleware.py`.
  3. Add Prometheus-compatible metrics endpoint in `src/core/monitoring.py`.
  4. Create benchmark script `scripts/profile_research.py` to run 10 queries and compute P50/P95 latency and token costs.
- **Target Deliverables**:
  - `src/core/middleware.py`, `src/core/monitoring.py`
  - `scripts/profile_research.py`
- **Acceptance Criteria**:
  - Every agent step generates traceable spans with token usage, latency, and status in LangSmith.
  - Metrics accurately calculate execution cost per research job.
- **Git Commit**: `feat: integrate observability tracing and cost monitoring`

---

#### Day 20 — Cost Optimization & Hallucination Reduction
- **Primary Goal**: Optimize operational cost and reduce hallucinations through model routing, Redis response caching, and context compression.
- **Tasks**:
  1. Implement model routing: route planning and classification to lightweight models (e.g., `gpt-4o-mini`), and synthesis/criticism to frontier models (e.g., `gpt-4o` or `claude-3-5-sonnet`).
  2. Implement Redis semantic/query caching for repeated web searches and document retrievals.
  3. Implement context token budgeting: compress and deduplicate retrieved snippets prior to LLM submission.
  4. Rerun evaluation suite to quantify cost reduction without degrading report quality.
- **Target Deliverables**:
  - `src/rag/cache.py`, `src/core/router.py`
  - Updated `src/rag/pipeline.py` and `src/agents/search.py`
- **Acceptance Criteria**:
  - Cost per research run reduced by >= 40% with no statistically significant decline in faithfulness.
  - Cached search queries return in under 20ms.
- **Git Commit**: `feat: optimize costs with model routing and Redis caching`

---

#### Day 21 — Week 3 Production Readiness Audit & Chaos Testing
- **Primary Goal**: Perform chaos and fault-injection testing under adverse network and service failure conditions.
- **Tasks**:
  1. Test external API failures: mock timeouts and 5xx errors from OpenAI, Anthropic, and Tavily.
  2. Test database and cache disconnects: simulate PostgreSQL and Redis dropouts and verify retry/recovery mechanisms.
  3. Verify transaction rollback and resource cleanup on aborted research runs.
  4. Compile `docs/week-3-review.md` addressing identified bottlenecks and resilience measures.
- **Target Deliverables**:
  - `tests/integration/test_chaos_resilience.py`
  - `docs/week-3-review.md`
- **Acceptance Criteria**:
  - Zero unhandled exceptions or zombie processes during simulated third-party outages.
  - Incomplete research jobs transition to `FAILED` status with descriptive error context.
- **Git Commit**: `test: complete week three production audit and chaos testing`

---

### WEEK 4: Backend, UI, Docker and Cloud Deployment (Days 22–28)

#### Day 22 — Production FastAPI Backend & Celery Worker
- **Primary Goal**: Build the asynchronous REST API layer backed by PostgreSQL, Alembic migrations, and Celery background workers.
- **Tasks**:
  1. Implement SQLAlchemy models in `src/db/models/` (`User`, `ResearchJob`, `Document`, `Evidence`, `Report`).
  2. Setup Alembic and generate initial migrations in `src/db/migrations/`.
  3. Implement Celery task worker in `src/workers/tasks.py` to execute LangGraph research workflows asynchronously.
  4. Build REST endpoints in `src/api/routes/`:
     - `POST /api/v1/research`: Launch research job (returns `job_id`).
     - `GET /api/v1/research/{job_id}`: Poll job status, progress, and agent log.
     - `POST /api/v1/documents`: Upload and trigger document ingestion.
     - `GET /api/v1/documents`: List uploaded documents.
     - `GET /api/v1/reports/{report_id}`: Fetch completed report.
     - `GET /health` & `GET /ready`: Health check probes.
  5. Add JWT authentication and rate limiting in `src/core/security.py`.
  6. Write API integration tests in `tests/api/test_api_endpoints.py`.
- **Target Deliverables**:
  - `src/db/models/`, `src/db/database.py`, `src/db/migrations/`
  - `src/workers/queue.py`, `src/workers/tasks.py`
  - `src/api/routes/`, `src/api/schemas/`
  - `tests/api/test_api_endpoints.py`
- **Acceptance Criteria**:
  - Research requests return `202 Accepted` immediately with a tracked `job_id`.
  - Background workers execute the research graph and persist results to PostgreSQL.
  - Endpoints are secured via JWT bearer tokens and rate-limited.
- **Git Commit**: `feat: implement production FastAPI backend and Celery worker`

---

#### Day 23 — Streamlit Research Dashboard & Live Visualizer
- **Primary Goal**: Build a responsive, interactive Streamlit frontend for launching research, inspecting real-time agent execution, and reviewing cited reports.
- **Tasks**:
  1. Implement `src/ui/app.py`: Streamlit entry point with custom theme and navigation.
  2. Implement `src/ui/pages/1_New_Research.py`: Topic input, scope selector, web/doc toggles, and live execution tracker (polling agent status).
  3. Implement `src/ui/pages/2_Research_History.py`: Table of past research jobs with statuses, costs, and runtimes.
  4. Implement `src/ui/pages/3_Document_Library.py`: File uploader, ingestion status tracker, and document deletion.
  5. Implement `src/ui/components/report_view.py`: Markdown renderer with clickable footnote citations, comparison tables, and PDF export.
- **Target Deliverables**:
  - `src/ui/app.py`
  - `src/ui/pages/` and `src/ui/components/`
  - `src/tools/pdf_export.py`
- **Acceptance Criteria**:
  - Live progress bar highlights which agent is active (Planner -> Search -> Analyst -> Writer -> Critic).
  - Reports render citations cleanly with expandable evidence cards.
  - One-click PDF and Markdown export works reliably.
- **Git Commit**: `feat: build complete Streamlit research dashboard`

---

#### Day 24 — Dockerization & Local Multi-Service Infrastructure
- **Primary Goal**: Containerize all services with multi-stage Docker builds, Docker Compose orchestration, and Makefile automation.
- **Tasks**:
  1. Create multi-stage `Dockerfile` optimizing build cache and running as non-root user.
  2. Implement `docker-compose.yml` orchestrating 6 services:
     - `api`: FastAPI backend.
     - `worker`: Celery background runner.
     - `ui`: Streamlit frontend.
     - `postgres`: Persistent database with health check.
     - `redis`: Queue and cache.
     - `chromadb`: Persistent vector storage volume.
  3. Implement `Makefile` with commands: `make install`, `make test`, `make lint`, `make docker-up`, `make docker-down`.
  4. Test full application lifecycle in Docker.
- **Target Deliverables**:
  - `Dockerfile`, `docker-compose.yml`, `.dockerignore`, `Makefile`
- **Acceptance Criteria**:
  - `docker compose up --build` brings all 6 services up cleanly.
  - Health checks pass and containers communicate over internal Docker network.
- **Git Commit**: `feat: dockerize complete platform with Docker Compose`

---

#### Day 25 — GitHub Actions CI/CD Pipeline
- **Primary Goal**: Build an automated CI/CD pipeline enforcing code quality, type safety, test execution, security scans, and Docker container builds.
- **Tasks**:
  1. Create `.github/workflows/ci.yml`:
     - Linting check via Ruff.
     - Strict type check via Mypy.
     - Automated test execution with Pytest across unit, integration, and security suites.
     - Dependency vulnerability audit (`pip-audit` / `safety`).
     - Docker build validation.
  2. Configure dependency caching to ensure pipeline runs under 4 minutes.
  3. Add coverage badge and status badges to `README.md`.
- **Target Deliverables**:
  - `.github/workflows/ci.yml`
- **Acceptance Criteria**:
  - Workflow triggers on all pull requests and pushes to `main`.
  - Any failing test, type error, or high-severity vulnerability halts the build.
- **Git Commit**: `ci: configure GitHub Actions CI/CD pipeline`

---

#### Day 26 — Cloud Deployment on AWS EC2 with Nginx & SSL
- **Primary Goal**: Deploy the containerized application onto an AWS EC2 instance secured with Nginx, HTTPS (Let's Encrypt), and automated restart policies.
- **Tasks**:
  1. Create EC2 configuration scripts in `infrastructure/aws/user-data.sh`.
  2. Configure Nginx reverse proxy configuration in `infrastructure/aws/nginx.conf` routing `/api` to FastAPI and `/` to Streamlit.
  3. Document SSL provisioning instructions via Certbot (`certbot --nginx`).
  4. Formulate backup strategy for PostgreSQL volume and ChromaDB embeddings.
  5. Author comprehensive deployment guide in `docs/deployment.md`.
- **Target Deliverables**:
  - `infrastructure/aws/nginx.conf`, `infrastructure/aws/user-data.sh`
  - `docs/deployment.md`
- **Acceptance Criteria**:
  - Fully documented and reproducible single-command deployment steps.
  - Security group specifications isolate internal ports (Postgres, Redis, Celery) from the public internet.
- **Git Commit**: `feat: configure AWS EC2 deployment and Nginx reverse proxy`

---

#### Day 27 — Professional Recruiter-Ready Documentation & Architecture
- **Primary Goal**: Produce comprehensive, production-grade documentation, Mermaid diagrams, API references, and architecture write-ups.
- **Tasks**:
  1. Write top-tier `README.md` including badges, architecture diagrams, benchmark results, and quickstart commands.
  2. Author `docs/architecture.md`: In-depth breakdown of multi-agent state machines, hybrid RAG, and data flows.
  3. Author `docs/api.md`: Comprehensive OpenAPI endpoint reference with example request/response payloads.
  4. Author `docs/decisions.md`: Architecture Decision Records (ADRs) explaining technology choices.
- **Target Deliverables**:
  - `README.md`
  - `docs/architecture.md`, `docs/api.md`, `docs/decisions.md`
- **Acceptance Criteria**:
  - Documentation clearly demonstrates enterprise software engineering standards.
  - All commands and code snippets in the README are verified and functional.
- **Git Commit**: `docs: create comprehensive production documentation`

---

#### Day 28 — Final Portfolio Audit, Interview Prep & Demo Script
- **Primary Goal**: Conduct end-to-end verification, finalize portfolio artifacts, and prepare technical interview demonstrations.
- **Tasks**:
  1. Execute full end-to-end test suite (`tests/e2e/test_full_workflow.py`).
  2. Verify all 29 items on the Production Quality Checklist.
  3. Author technical portfolio assets:
     - 3 impactful resume bullet points with concrete metrics.
     - 60-second video demo walkthrough script.
     - Technical LinkedIn announcement post.
     - 8 in-depth AI engineering interview questions and answers.
  4. Author `docs/final_audit.md` summarizing overall test metrics and achievements.
- **Target Deliverables**:
  - `tests/e2e/test_full_workflow.py`
  - `docs/final_audit.md`, `docs/interview_guide.md`
- **Acceptance Criteria**:
  - 100% of end-to-end tests pass.
  - System operates smoothly across all interfaces (CLI, REST API, Streamlit UI).
- **Git Commit**: `chore: complete final project audit and portfolio preparation`

---

## 5. Master Prompts Catalog (Days 1–28)

To ensure reproducibility across development sessions, each day has a dedicated copy-paste master prompt prefixed with the **Master Engineering Context Prompt**:

```text
MASTER CONTEXT PREFIX:
You are my Principal AI Engineer, Software Architect, and Technical Mentor.
PROJECT: AI Research & Report Agent
MISSION: Build a production-grade multi-agent AI research platform that accepts a research topic, decomposes it into questions, retrieves information from the internet and private documents, analyzes evidence, identifies contradictions, and generates comprehensive research reports with verifiable citations.
```

The detailed day-by-day prompt specifications are cataloged in `docs/plan/master_prompts.md`.

---

## 6. Production Quality Checklist (0/29 Completed)

- [ ] **Architecture & Code**: Modular architecture established (`src/core`, `src/agents`, `src/rag`, `src/api`)
- [ ] **Architecture & Code**: Strict Python type hints and Mypy compliance
- [ ] **Architecture & Code**: Centralized Pydantic v2 settings management
- [ ] **Architecture & Code**: Structured JSON logging with request tracing
- [ ] **Architecture & Code**: Application-wide custom exception hierarchy
- [ ] **AI & RAG Engine**: Multi-format document ingestion (PDF, DOCX, TXT, MD)
- [ ] **AI & RAG Engine**: Recursive chunking with metadata preservation
- [ ] **AI & RAG Engine**: ChromaDB persistent vector storage with CRUD
- [ ] **AI & RAG Engine**: Sparse BM25 keyword retrieval
- [ ] **AI & RAG Engine**: Reciprocal Rank Fusion (RRF) hybrid search
- [ ] **AI & RAG Engine**: Cross-Encoder neural reranking
- [ ] **AI & RAG Engine**: Grounded RAG with strict citation verification
- [ ] **AI & RAG Engine**: SSRF-hardened web search and article scraper
- [ ] **Multi-Agent Orchestration**: LangGraph state machine with cyclic routing
- [ ] **Multi-Agent Orchestration**: Planner Agent sub-question decomposition
- [ ] **Multi-Agent Orchestration**: Search Agent parallel async retrieval
- [ ] **Multi-Agent Orchestration**: Analyst Agent contradiction detection & confidence scoring
- [ ] **Multi-Agent Orchestration**: Writer Agent cited report synthesis
- [ ] **Multi-Agent Orchestration**: Critic Agent adversarial verification & revision loop
- [ ] **Multi-Agent Orchestration**: Workflow checkpointing & resumability
- [ ] **Security & Guardrails**: File upload sanitization & MIME validation
- [ ] **Security & Guardrails**: Untrusted prompt content demarcation & injection defense
- [ ] **Security & Guardrails**: Network SSRF prevention & private IP blocking
- [ ] **Security & Guardrails**: JWT authentication & route rate limiting
- [ ] **Infrastructure & Backend**: PostgreSQL schema with Alembic migrations
- [ ] **Infrastructure & Backend**: Celery distributed task execution with Redis queue
- [ ] **Infrastructure & Backend**: FastAPI REST endpoints with OpenAPI schemas
- [ ] **Infrastructure & Backend**: Streamlit reactive dashboard with live progress
- [ ] **DevOps & Delivery**: Docker Compose multi-service local environment
- [ ] **DevOps & Delivery**: Automated GitHub Actions CI/CD pipeline
- [ ] **DevOps & Delivery**: AWS EC2 production deployment with Nginx & Let's Encrypt
- [ ] **Quality & Evaluation**: RAGAS automated evaluation with reproducible metrics
- [ ] **Quality & Evaluation**: LangSmith distributed tracing and cost monitoring

---

## 7. Execution Protocol

When advancing to implementation:
1. Always start each day by reviewing the corresponding day plan and acceptance criteria.
2. Implement files incrementally, running tests and linters immediately after each change.
3. Keep `docs/decisions.md` and `docs/progress.md` updated with technical tradeoffs and milestones.
4. Never advance to the next day until all tests and checks for the current day succeed.
