# Master Prompts Catalog: Days 1–28
**Production-Grade Prompt Book for Cursor, OpenCode, Claude, and ChatGPT**

---

## Master Engineering Context Prompt (Prepend Before Every Daily Prompt)

```text
You are my Principal AI Engineer, Software Architect, and Technical Mentor.
PROJECT: AI Research & Report Agent

MISSION:
Build a production-grade multi-agent AI research platform that accepts a research topic, decomposes it into questions, retrieves information from the internet and private documents, analyzes evidence, identifies contradictions, and generates comprehensive research reports with verifiable citations.

TECHNOLOGY STACK:
- Backend: Python 3.11+, FastAPI, SQLAlchemy 2.0, PostgreSQL, Redis, Celery
- AI & Orchestration: LangGraph, OpenAI API, Anthropic API, Pydantic v2
- RAG & Retrieval: ChromaDB, BM25, Hybrid RRF, Cross-Encoder Reranker, PyMuPDF, python-docx
- Agents: Planner, Search, Analyst, Writer, Critic
- Frontend: Streamlit
- Evaluation & Tracing: RAGAS, LangSmith, Pytest
- Infrastructure: Docker, Docker Compose, AWS EC2, Nginx, GitHub Actions

ENGINEERING REQUIREMENTS:
1. Write production-quality, maintainable Python code with strict type hints and Pydantic validation.
2. Follow modular architecture and separation of concerns.
3. Implement structured JSON logging and robust custom exception handling.
4. Never hardcode credentials; use centralized Pydantic settings with environment variables.
5. Add unit, integration, and security tests for all modules.
6. Make long-running workflows resumable via checkpointing.
7. Preserve strict source provenance and citation integrity.
8. Never skip implementation details or use placeholder pseudocode.
```

---

## Day 1 — Project Foundation & Tooling Prompt

```text
DAY 1: PROJECT FOUNDATION AND INITIALIZATION
Your task is to initialize the complete project foundation.

Requirements:
1. Create the modular project structure covering:
   core, agents, graph, rag, tools, services, db, workers, api, eval, ui, tests, scripts, docs
2. Configure pyproject.toml with:
   - Python 3.11+
   - Pydantic v2, pydantic-settings
   - Ruff (linting and formatting)
   - Mypy (strict type-checking)
   - Pytest and pytest-cov
3. Implement centralized configuration in src/core/config.py:
   - Environment profiles: development, testing, production
   - LLM, Database, Redis, VectorDB, and Search settings with SecretStr validation
4. Implement:
   - src/core/exceptions.py: Application-wide exception hierarchy
   - src/core/logging.py: Structured JSON logging with request and agent correlation IDs
5. Create initial documentation:
   - README.md
   - docs/architecture.md
   - docs/decisions.md
6. Add unit tests for configuration and logging in tests/unit/test_config.py.

Verification: Run ruff check ., mypy src, and pytest tests/. Ensure exit code 0.
Deliverable: Working Python project structure, settings, logging, and initial commit.
```

---

## Day 2 — Production Document Ingestion Engine Prompt

```text
DAY 2: PRODUCTION DOCUMENT INGESTION PIPELINE
Implement a robust document ingestion system in src/rag/.

Requirements:
1. Implement src/rag/loaders.py:
   - Multi-format support: PDF (PyMuPDF), DOCX (python-docx), TXT, and Markdown.
   - Detect MIME types using magic bytes to prevent file spoofing.
   - Extract page-by-page text, preserving page numbers and file metadata.
   - Guard against path traversal attacks and enforce 25MB file size limits.
2. Implement src/rag/chunker.py:
   - Recursive token-aware text splitting (800-token target, 100-token overlap).
   - Preserve natural boundaries (paragraphs, sentences).
   - Attach chunk metadata: parent_doc_id, chunk_index, token_count, page_number.
3. Implement src/rag/ingest.py:
   - Deduplicate documents using SHA-256 content hashes.
   - Generate deterministic UUID5 document IDs.
   - Support idempotent ingestion.
4. Create CLI runner scripts/ingest_sample.py to process a directory and display summary metrics.
5. Add unit tests in tests/unit/test_loaders.py and test_chunker.py.

Verification: Run pytest tests/unit/ and execute ingestion CLI on sample documents.
Deliverable: Working ingestion CLI with reliable metadata and document-level error handling.
```

---

## Day 3 — Embeddings & ChromaDB Persistence Prompt

```text
DAY 3: EMBEDDING ENGINE AND CHROMADB INTEGRATION
Implement a production-ready vector storage system.

Files:
- src/rag/embeddings.py
- src/rag/store.py
- tests/integration/test_chroma.py

Requirements:
1. Create an abstract BaseEmbeddingProvider and implement OpenAIEmbeddingProvider:
   - Configurable model (text-embedding-3-small, text-embedding-3-large).
   - Batching support (up to 512 chunks per request).
   - Exponential backoff and retry policy using tenacity for rate limits.
2. Implement ChromaVectorStore in src/rag/store.py:
   - Persistent ChromaDB client with configurable storage path.
   - Collection lifecycle management (add, update, delete by document ID).
   - Vector similarity search with distance scores and metadata filtering.
3. Prevent duplicate chunk insertions using deterministic chunk IDs.
4. Write integration tests in tests/integration/test_chroma.py using temporary directories.
5. Update scripts/ingest_sample.py to embed chunks and persist to ChromaDB.

Verification: Run pytest tests/integration/test_chroma.py.
Deliverable: Persistent vector database with chunk CRUD and similarity retrieval.
```

---

## Day 4 — Advanced Hybrid Retrieval & Reranking Prompt

```text
DAY 4: ADVANCED HYBRID SEARCH AND RERANKING
Implement a production-quality hybrid retrieval engine.

Files:
- src/rag/bm25.py
- src/rag/reranker.py
- src/rag/retriever.py
- tests/integration/test_hybrid_retriever.py
- scripts/benchmark_retrieval.py

Requirements:
1. Implement BM25 lexical retriever in src/rag/bm25.py:
   - Tokenization with stopword filtering and normalization.
   - Corpus index persistence and loading.
2. Implement Cross-Encoder reranker in src/rag/reranker.py:
   - Model: cross-encoder/ms-marco-MiniLM-L-6-v2.
   - Batch scoring with graceful fallback to RRF scores on failure.
3. Implement HybridRetriever in src/rag/retriever.py:
   - Query ChromaDB (dense) and BM25 (sparse) concurrently.
   - Merge candidate pools using Reciprocal Rank Fusion (RRF): 1 / (60 + rank).
   - Neural reranking over top candidates, returning top-K results.
4. Create evaluation benchmark script scripts/benchmark_retrieval.py comparing:
   Vector-only vs BM25-only vs Hybrid RRF vs Hybrid + Reranking.
5. Write integration tests in tests/integration/test_hybrid_retriever.py.

Verification: Run pytest tests/integration/test_hybrid_retriever.py and run benchmark script.
Deliverable: High-precision hybrid RAG retrieval pipeline with benchmarked metrics.
```

---

## Day 5 — Production RAG Pipeline with Citation Validation Prompt

```text
DAY 5: PRODUCTION RAG PIPELINE WITH CITATION VALIDATION
Build the complete document RAG generation pipeline.

Files:
- src/rag/citations.py
- src/rag/pipeline.py
- tests/rag/test_rag_pipeline.py

Requirements:
1. Implement CitationRegistry in src/rag/citations.py:
   - Map retrieved source chunks to numbered bracket references [1], [2].
   - Validate that every citation in generated text corresponds to an actual chunk in context.
   - Reject or flag hallucinated citation tokens.
2. Implement RAGPipeline in src/rag/pipeline.py:
   - Query processing -> Hybrid retrieval -> Neural reranking -> Context assembly.
   - Context token budgeting to prevent context overflow.
   - Structured Pydantic answer schema: answer, citations, confidence, insufficient_context.
   - Grounded refusal: Return "I don't know based on the provided documents" when context is insufficient.
3. Add unit and edge-case tests in tests/rag/test_rag_pipeline.py:
   - Valid grounded answers, empty context, conflicting evidence, and invalid citation detection.

Verification: Run pytest tests/rag/test_rag_pipeline.py.
Deliverable: Grounded document RAG pipeline with strictly validated inline citations.
```

---

## Day 6 — Production Web Research Toolkit Prompt

```text
DAY 6: PRODUCTION WEB RESEARCH TOOLKIT
Build the web research tools in src/tools/.

Files:
- src/tools/web_search.py
- src/tools/webpage_reader.py
- src/tools/source_validator.py
- tests/security/test_ssrf.py
- scripts/test_web_tools.py

Requirements:
1. Implement TavilySearchTool in src/tools/web_search.py:
   - Query execution with configurable search depth (basic/advanced) and max results.
   - Normalize output into WebSearchResult schema.
2. Implement WebpageReader in src/tools/webpage_reader.py:
   - Fetch URL with strict timeouts (10s) and redirect caps.
   - Extract primary readable article text using BeautifulSoup4.
   - Strip navigation, ads, scripts, and format into clean markdown.
3. Implement SourceValidator in src/tools/source_validator.py:
   - SSRF Defense: Block localhost, 127.0.0.1, private IPs (RFC 1918), and AWS metadata (169.254.169.254).
   - Calculate domain credibility scores.
4. Add security tests in tests/security/test_ssrf.py.
5. Create CLI test script scripts/test_web_tools.py.

Verification: Run pytest tests/security/test_ssrf.py and test web search CLI.
Deliverable: Secure, rate-limited web search and webpage scraping toolkit.
```

---

## Day 7 — Week 1 Engineering Audit Prompt

```text
DAY 7: WEEK 1 ENGINEERING AUDIT
Act as a Principal AI Engineer performing a production-readiness code review.

Audit everything implemented during Days 1–6:
- Architecture, modularity, and strict Python typing (Ruff & Mypy).
- Ingestion security (path traversal, file size limits, MIME validation).
- ChromaDB persistence, batching, and embedding consistency.
- Hybrid search fusion math and reranker fallback handling.
- Citation validation and grounded refusal correctness.
- Web scraper SSRF prevention and timeout handling.

Tasks:
1. Run ruff check ., mypy src, and pytest --cov=src.
2. Identify and fix the top 5 highest-priority technical debt or bug items.
3. Author docs/week-1-review.md with coverage statistics, benchmark summaries, and architectural decisions.

Verification: Ensure all test suites pass with >80% test coverage and 0 linting/typing errors.
Deliverable: Hardened Week 1 codebase and published week-1-review.md.
```

---

## Day 8 — LangGraph State Management Prompt

```text
DAY 8: LANGGRAPH STATE MANAGEMENT AND SYSTEM ARCHITECTURE
Design the complete LangGraph state machine and data schemas for the multi-agent system.

Files:
- src/agents/state.py
- src/agents/schemas/ (plan.py, evidence.py, analysis.py, report.py)
- src/graph/state.py
- docs/agent-workflow.md
- tests/agents/test_state.py

Requirements:
1. Define ResearchState(TypedDict) with immutable updates:
   topic, scope, plan, evidence_items, analysis, draft_report, critic_feedback, iteration_count, max_iterations, status, errors.
2. Define Pydantic schemas:
   - ResearchPlan & SubQuestion
   - EvidenceItem (claim, source_url, doc_id, page, timestamp, score)
   - AnalysisReport & FactualClaim (supporting/contradicting evidence IDs, confidence)
   - ReportDraft (sections, tables, citations, references)
   - CriticFeedback (approved, quality_score, unsupported_claims, revision_notes)
3. Create Mermaid diagram in docs/agent-workflow.md documenting nodes and conditional transitions.
4. Add state validation tests in tests/agents/test_state.py.

Verification: Run pytest tests/agents/test_state.py.
Deliverable: Type-safe state management architecture and complete data schemas.
```

---

## Day 9 — Planner Agent Prompt

```text
DAY 9: PLANNER AGENT IMPLEMENTATION
Implement the Planner Agent in src/agents/planner.py.

Requirements:
1. Receive research topic and scope from state.
2. Decompose topic into 4–8 MECE (Mutually Exclusive, Collectively Exhaustive) sub-questions.
3. For each sub-question, designate:
   - Required evidence type (academic, market stats, technical docs, news).
   - Target source channels (web search, internal RAG, or both).
   - Priority ranking (1 to 5).
4. Use structured LLM outputs with Pydantic validation (ResearchPlan).
5. Implement retry on invalid schema and fallback for ambiguous topics.
6. Write unit tests in tests/agents/test_planner.py testing simple, complex, and ambiguous queries.

Verification: Run pytest tests/agents/test_planner.py.
Deliverable: Production Planner Agent producing prioritized research plans.
```

---

## Day 10 — Search Agent Prompt

```text
DAY 10: SEARCH AGENT IMPLEMENTATION
Implement the Search Agent in src/agents/search.py.

Requirements:
1. Execute parallel asynchronous retrievals for all sub-questions:
   - Query Tavily Web Search.
   - Query Internal Hybrid RAG retriever.
2. Bound concurrency using asyncio.Semaphore to prevent rate limits.
3. Normalize all results into EvidenceItem schema with unique evidence_id, source attribution, and timestamps.
4. Deduplicate results across URLs and chunk IDs.
5. Provide graceful partial-failure handling (if one sub-query fails, continue with others).
6. Write integration tests in tests/agents/test_search.py with mocked search and retriever providers.

Verification: Run pytest tests/agents/test_search.py.
Deliverable: High-throughput parallel search agent preserving source provenance.
```

---

## Day 11 — Analyst Agent Prompt

```text
DAY 11: ANALYST AGENT IMPLEMENTATION
Implement the Analyst Agent in src/agents/analyst.py.

Requirements:
1. Synthesize retrieved evidence items grouped by sub-question.
2. Extract atomic factual claims:
   - Statement of fact.
   - Supporting evidence IDs.
   - Contradicting evidence IDs.
   - Confidence score (High, Medium, Low).
   - Limitations and reasoning.
3. Explicitly detect contradictions between sources (e.g. conflicting metrics or dates).
4. Identify missing evidence and flag knowledge gaps for follow-up search loops.
5. Write unit tests in tests/agents/test_analyst.py covering consensus, contradiction, and gaps.

Verification: Run pytest tests/agents/test_analyst.py.
Deliverable: Structured analytical engine identifying evidence conflicts and confidence.
```

---

## Day 12 — Writer Agent Prompt

```text
DAY 12: WRITER AGENT AND REPORT GENERATION
Implement the Writer Agent in src/agents/writer.py.

Requirements:
1. Transform structured analysis into an executive-grade research report.
2. Required sections:
   Executive Summary, Objectives, Methodology, Detailed Findings, Comparison Tables, Contradictions, Limitations, References.
3. Strict citation mapping:
   - Map evidence IDs to bracketed citations [1], [2].
   - Compile sequential bibliography with exact URLs, titles, and publication dates.
   - Never invent source metadata or statistics.
4. Produce structured ReportDraft and formatted Markdown.
5. Add unit tests in tests/agents/test_writer.py verifying citation integrity and section completeness.

Verification: Run pytest tests/agents/test_writer.py.
Deliverable: High-fidelity report synthesis engine with verified citations and comparison tables.
```

---

## Day 13 — LangGraph Orchestration & Checkpointing Prompt

```text
DAY 13: COMPLETE MULTI-AGENT LANGGRAPH ORCHESTRATION
Wire all agents into a unified LangGraph workflow.

Files:
- src/graph/workflow.py
- src/graph/nodes.py
- src/graph/edges.py
- src/graph/checkpoint.py
- scripts/run_research.py
- tests/agents/test_graph_workflow.py

Requirements:
1. Build StateGraph connecting Planner -> Search -> Analyst -> Writer -> Critic.
2. Implement conditional routing in src/graph/edges.py:
   - If missing evidence flagged and iterations < 2 -> return to Search.
   - If citations invalid or claims rejected and iterations < 2 -> return to Writer.
   - If approved or max iterations reached -> END.
3. Configure persistent checkpointing (MemorySaver for dev, PostgresSaver for prod).
4. Build CLI execution script scripts/run_research.py streaming live agent progression.
5. Write end-to-end graph integration tests in tests/agents/test_graph_workflow.py.

Verification: Run pytest tests/agents/test_graph_workflow.py and run CLI runner on a test topic.
Deliverable: Executable, resumable multi-agent research workflow.
```

---

## Day 14 — Critic Agent & Week 2 Review Prompt

```text
DAY 14: CRITIC AGENT AND WEEK 2 REVIEW
Implement the Critic Agent in src/agents/critic.py and conduct the Week 2 system audit.

Requirements:
1. Implement Critic Agent:
   - Inspect draft report against evidence items.
   - Identify unsupported claims, hallucinated citations, and exaggerated conclusions.
   - Return structured CriticFeedback (approved, quality_score, issues, revision_guidelines).
2. Wire Critic into LangGraph conditional edges (single revision pass allowed).
3. Test critic with adversarial inputs containing injected hallucinations in tests/agents/test_critic.py.
4. Perform comprehensive Week 2 audit:
   - Run full agent test suite.
   - Validate state resumption from checkpoints.
   - Compile docs/week-2-review.md.

Verification: Run pytest tests/agents/ -v.
Deliverable: Fact-checking Critic Agent and published week-2-review.md.
```

---

## Days 15–28 Prompts Overview
*(See `docs/plan/week-3-evaluation-security-optimization.md` and `docs/plan/week-4-backend-ui-infrastructure.md` for complete daily step-by-step specifications for Days 15 to 28).*
