# Architecture Decision Records (ADR)
**AI Research & Report Agent**

---

## ADR 001: Separation of Primary Relational DB and Vector DB
- **Status**: Accepted
- **Context**: RAG applications often mistakenly attempt to use vector databases (such as ChromaDB or Pinecone) as their primary database for user records, application state, and job tracking.
- **Decision**: We strictly separate concerns:
  - **PostgreSQL 16**: Primary source of truth for users, jobs, execution history, evidence provenance, and reports.
  - **ChromaDB**: Dedicated solely to vector embeddings, nearest-neighbor searches, and chunk ID lookups.
  - **Redis**: Dedicated to asynchronous task queues (via Celery) and transient query caching.
- **Consequences**: Ensures ACID compliance for critical application data, simplifies disaster recovery, and prevents vendor lock-in with vector storage engines.

---

## ADR 002: Orchestration Framework Selection (LangGraph over LangChain Sequential Chains)
- **Status**: Accepted
- **Context**: Deep research requires cycles, feedback loops (critic rejecting reports, search expanding queries), and fault-tolerant resumption if a process is terminated mid-execution.
- **Decision**: Use **LangGraph** with a custom `StateGraph` rather than legacy LangChain linear chains or autonomous loops without explicit state.
- **Consequences**: Enables cyclic routing, explicit state schemas (TypedDict / Pydantic), and database-backed checkpointing for long-running workflows.

---

## ADR 003: Hybrid Retrieval Architecture (BM25 + ChromaDB + Cross-Encoder)
- **Status**: Accepted
- **Context**: Dense vector retrieval frequently struggles with rare keywords, exact identifiers, acronyms, and version numbers. Sparse retrieval (BM25) excels at keyword matching but misses semantic paraphrases.
- **Decision**: Combine dense vector retrieval (ChromaDB) and sparse lexical retrieval (BM25) via Reciprocal Rank Fusion (RRF), followed by neural reranking using `cross-encoder/ms-marco-MiniLM-L-6-v2`.
- **Consequences**: Greatly improves Recall@K and MRR across both technical documents and natural language web articles at the cost of a slight latency increase during the reranking stage.

---

## ADR 004: Asynchronous Execution Engine (Celery + Redis over FastAPI BackgroundTasks)
- **Status**: Accepted
- **Context**: Deep research queries take anywhere from 45 seconds to several minutes to execute due to multiple web searches, document retrievals, and LLM reasoning steps. FastAPI `BackgroundTasks` run within the web server process and are vulnerable to server restarts, lack prioritization, and fail to scale horizontally.
- **Decision**: Adopt **Celery** with **Redis** as the message broker. FastAPI endpoints enqueue tasks and immediately return `202 Accepted` with a `job_id`. Workers process tasks out-of-process.
- **Consequences**: The web tier remains lightweight and responsive; worker nodes can be scaled independently on compute-optimized instances.

---

## ADR 005: Deterministic Citation Mapping vs Pure LLM Generation
- **Status**: Accepted
- **Context**: LLMs routinely fabricate or transpose inline citation numbers when tasked with both writing complex prose and maintaining exact citation bibliographies simultaneously.
- **Decision**: Agents output explicit evidence token placeholders (e.g. `[evidence_id]`). A post-processing step deterministically maps these tokens to sequential numbers `[1]`, `[2]`, validates their presence in the evidence registry, and compiles the final references section.
- **Consequences**: Completely eliminates hallucinated citation references and out-of-sync bibliographies.
