# 🧠 AI Research & Report Agent — Production Edition

Autonomous multi-agent research platform that accepts open-ended research topics, decomposes them into prioritized sub-questions, retrieves information concurrently across public web indices and internal documents using Hybrid RAG, cross-corroborates evidence to detect contradictions, and synthesizes publication-grade reports with verifiable inline citations.

---

## 🏗️ Architecture & Project Structure

The codebase is split into dedicated **backend** and **frontend** directories under `src/`:

```
Multi-Agent/
├── docs/                        # Complete 28-day roadmap, architecture specs & ADRs
├── src/
│   ├── backend/                 # Core AI, RAG, multi-agent orchestration & API
│   │   ├── core/                # Centralized Pydantic settings, logging, SSRF defenses
│   │   ├── rag/                 # Ingestion (PDF/DOCX/TXT/MD), chunker, BM25, Chroma store, RRF, citations
│   │   ├── tools/               # Tavily search, article scraper, source validator
│   │   ├── agents/              # Planner, Search, Analyst, Writer, Critic
│   │   ├── graph/               # Multi-agent LangGraph workflow with feedback loops
│   │   ├── api/                 # FastAPI REST API endpoints
│   │   └── main.py              # Backend entrypoint (uvicorn launcher)
│   └── frontend/                # Interactive Streamlit dashboard & live visualizer
│       └── app.py               # Streamlit application with live agent stepper & cited report viewer
├── data/
│   ├── raw/                     # Uploaded documents directory
│   └── evaluation/              # Ground-truth evaluation datasets
├── tests/                       # Comprehensive unit and integration test suite
│   ├── unit/                    # Config, loaders, chunker, BM25, citations, security tests
│   └── integration/             # End-to-end multi-agent workflow tests
├── pyproject.toml               # Tooling & dependencies configuration
├── .env.example                 # Environment configuration template
└── .gitignore                   # Ignore rules for models, chroma persistence, caches
```

---

## 🚀 Key AI & Engineering Features

1. **Multi-Agent Orchestration**:
   - **Planner Agent**: Decomposes complex topics into MECE sub-questions.
   - **Search Agent**: Parallel asynchronous retrieval across Tavily Web Search and internal Hybrid RAG.
   - **Analyst Agent**: Factual claim extraction, contradiction detection, and confidence scoring.
   - **Writer Agent**: Synthesis of executive reports with Markdown comparison tables and evidence citation mapping.
   - **Critic Agent**: Adversarial fact-checker auditing claims and citations against retrieved evidence.
2. **Hybrid RAG & Neural Reranking**:
   - **Sparse Lexical Search**: BM25 keyword matching for domain entities and acronyms.
   - **Dense Semantic Search**: Vector embeddings stored in ChromaDB.
   - **Reciprocal Rank Fusion (RRF)**: Merges dense and sparse ranks via $RRF(d) = \sum \frac{1}{60 + rank}$.
   - **Cross-Encoder Reranker**: Fine-grained passage scoring with `ms-marco-MiniLM-L-6-v2`.
3. **Deterministic Citation Verification**:
   - Numbered citation tokens `[1]`, `[2]` are validated against the source registry to eliminate hallucinated references.
4. **Security Hardening**:
   - SSRF protection: Blocks localhost, loopback (`127.0.0.0/8`), private RFC1918 subnets, and cloud metadata (`169.254.169.254`).
   - Path traversal prevention for file uploads.

---

## ⚡ Quickstart

### 1. Run Tests
```bash
py -3.13 -m pytest -v
```

### 2. Launch FastAPI Backend
```bash
py -3.13 src/backend/main.py
# Or with uvicorn:
uvicorn src.backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Launch Streamlit UI
```bash
streamlit run src/frontend/app.py
```
Open `http://localhost:8501` in your browser.
