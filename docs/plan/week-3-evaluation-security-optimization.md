# Week 3: Evaluation, Security & Optimization (Days 15–21)
**Detailed Day-by-Day Implementation Specifications**

---

## Day 15 — Research & RAG Evaluation Dataset

### 1. Objective
Build a reproducible, version-controlled ground-truth evaluation dataset covering diverse query types, difficulty tiers, and contradiction scenarios.

### 2. Architecture & File Layout
```
data/evaluation/
├── questions.jsonl
└── README.md
src/eval/
├── __init__.py
└── dataset.py
tests/unit/
└── test_eval_dataset.py
```

### 3. Step-by-Step Implementation Tasks
1. **Dataset Schema (`src/eval/dataset.py`)**:
   - Define `EvaluationSample(BaseModel)`:
     ```python
     class EvaluationSample(BaseModel):
         id: str
         question: str
         ground_truth: str
         expected_sources: list[str]
         difficulty: Literal["easy", "medium", "hard"]
         question_type: Literal["direct_factual", "multi_doc_synthesis", "comparative", "contradiction", "unanswerable"]
         expected_claims: list[str]
         is_answerable: bool
     ```
2. **Dataset Creation (`data/evaluation/questions.jsonl`)**:
   - Curate 50 production-grade evaluation samples based on sample technical documents and known web topics.
   - Include 10 unanswerable queries to test refusal/grounding guardrails.
   - Include 10 contradiction queries where different sources disagree.
3. **Validation & Verification Protocol (`data/evaluation/README.md`)**:
   - Document the manual verification protocol ensuring ground truth answers are human-verified against source texts.

### 4. Verification & Testing Commands
```bash
pytest tests/unit/test_eval_dataset.py -v
```

### 5. Git Commit
```bash
git commit -m "feat: create evaluation dataset and validation framework"
```

---

## Day 16 — RAGAS Automated Evaluation Framework

### 1. Objective
Integrate the RAGAS evaluation framework to programmatically calculate Faithfulness, Answer Relevancy, Context Precision, and Context Recall.

### 2. Architecture & File Layout
```
src/eval/
├── run_eval.py
└── metrics.py
reports/
├── evaluation_baseline.csv
└── evaluation_baseline.md
```

### 3. Step-by-Step Implementation Tasks
1. **Evaluation Runner (`src/eval/run_eval.py`)**:
   - Load `questions.jsonl`.
   - Run queries through RAG pipeline, capturing retrieved context passages and generated answers.
   - Evaluate against ground truth using RAGAS metrics:
     - `faithfulness`: Checks if answer claims are grounded in retrieved context.
     - `answer_relevancy`: Evaluates semantic alignment with question.
     - `context_precision`: Evaluates whether relevant chunks are ranked first.
     - `context_recall`: Measures if all facts in ground truth were retrieved.
2. **Custom Domain Metrics (`src/eval/metrics.py`)**:
   - `citation_precision`: Ratio of valid citations to total citations.
   - `grounded_refusal_accuracy`: Verifies unanswerable questions correctly return "I don't know".
3. **Reporting Automation**:
   - Export results to CSV and generate Markdown executive summary.

### 4. Verification & Testing Commands
```bash
python -m src.eval.run_eval --dataset data/evaluation/questions.jsonl --output reports/evaluation_baseline.md
```

### 5. Git Commit
```bash
git commit -m "feat: implement RAGAS evaluation pipeline"
```

---

## Day 17 — Retrieval Optimization Experiments

### 1. Objective
Run controlled grid-search experiments to optimize chunk size, retrieval fusion, and reranking parameters.

### 2. Architecture & File Layout
```
src/eval/
└── experiments.py
reports/
└── retrieval_experiments.csv
```

### 3. Step-by-Step Implementation Tasks
1. **Experiment Matrix (`src/eval/experiments.py`)**:
   - Grid dimensions:
     - Chunk sizes: 500, 800, 1200 tokens.
     - Overlap: 50, 100, 150 tokens.
     - Retrieval configurations:
       1. Dense Vector Search Only (ChromaDB).
       2. Sparse BM25 Search Only.
       3. Hybrid RRF Search.
       4. Hybrid RRF Search + Cross-Encoder Reranker (`ms-marco-MiniLM-L-6-v2`).
2. **Metric Computation**:
   - Calculate Recall@5, Recall@10, MRR (Mean Reciprocal Rank), nDCG, and average latency (ms).
3. **Analysis & Decision Record**:
   - Generate comparative tables.
   - Record winning configuration in `docs/decisions.md`.

### 4. Verification & Testing Commands
```bash
python -m src.eval.experiments --iterations 3
```

### 5. Git Commit
```bash
git commit -m "feat: conduct retrieval optimization experiments"
```

---

## Day 18 — Production Security & AI Guardrails

### 1. Objective
Fortify the platform against prompt injections, SSRF, path traversal, malicious documents, PII leakage, and unauthorized tool invocation.

### 2. Architecture & File Layout
```
src/core/
└── security.py
tests/security/
└── test_security_suite.py
```

### 3. Step-by-Step Implementation Tasks
1. **Adversarial Input & Prompt Defense (`src/core/security.py`)**:
   - Strict input length validation (topics <= 500 chars).
   - Demarcate all external content with XML tags (`<untrusted_document_context>`) with prompt instructions to treat context as data, never instructions.
   - Regex-based and heuristic scanner for injection markers (e.g. "Ignore previous instructions", "SYSTEM OVERRIDE").
2. **Network & Tool Security**:
   - Enforce SSRF blocking for all web fetchers (block `0.0.0.0/8`, `127.0.0.0/8`, `169.254.0.0/16`, IPv6 loopbacks).
   - Strict tool call allowlisting.
3. **File Upload Security**:
   - Sanitize file names; reject path traversal attempts (`../../etc/passwd`).
   - Validate magic bytes against allowed MIME types (`application/pdf`, `text/plain`, etc.).
4. **Adversarial Test Suite (`tests/security/test_security_suite.py`)**:
   - 20 distinct security test cases testing prompt injection, SSRF, zip bombs, and path traversal.

### 4. Verification & Testing Commands
```bash
pytest tests/security/test_security_suite.py -v
```

### 5. Git Commit
```bash
git commit -m "feat: implement production security and AI guardrails"
```

---

## Day 19 — Observability & Tracing via LangSmith

### 1. Objective
Implement end-to-end distributed tracing, token accounting, latency metrics, and operational monitoring via LangSmith and structured telemetry.

### 2. Architecture & File Layout
```
src/core/
├── middleware.py
└── monitoring.py
scripts/
└── profile_research.py
```

### 3. Step-by-Step Implementation Tasks
1. **LangSmith Integration**:
   - Configure LangChain/LangGraph environment hooks: `LANGCHAIN_TRACING_V2=true`, `LANGCHAIN_PROJECT="ai-research-agent"`.
   - Add custom run tags: `job_id`, `user_id`, `environment`.
2. **Token & Latency Accounting (`src/core/monitoring.py`)**:
   - Track prompt tokens, completion tokens, and model costs ($/1k tokens) per agent node.
   - Calculate latency for retrieval, web scraping, and LLM synthesis.
3. **Profiling Script (`scripts/profile_research.py`)**:
   - Execute 10 representative research runs; output P50, P90, and P95 latency and average cost per report.

### 4. Verification & Testing Commands
```bash
python scripts/profile_research.py --runs 5
```

### 5. Git Commit
```bash
git commit -m "feat: integrate observability tracing and cost monitoring"
```

---

## Day 20 — Cost Optimization & Hallucination Reduction

### 1. Objective
Reduce operational token costs by >=40% through intelligent model routing, Redis query caching, and context compression while preserving citation accuracy.

### 2. Architecture & File Layout
```
src/core/
└── router.py
src/rag/
└── cache.py
```

### 3. Step-by-Step Implementation Tasks
1. **Model Routing (`src/core/router.py`)**:
   - Route query decomposition (Planner) and initial classification to fast, low-cost models (`gpt-4o-mini`).
   - Route complex synthesis (Analyst, Writer, Critic) to frontier models (`gpt-4o` / `claude-3-5-sonnet`).
2. **Redis Semantic & Query Cache (`src/rag/cache.py`)**:
   - Cache identical search queries and embeddings with configurable TTL (e.g. 24 hours).
   - Invalidate cache when underlying documents are modified.
3. **Context Compression**:
   - Strip redundant whitespace and extract only relevant sentences from retrieved chunks prior to prompt assembly.
4. **Before/After Evaluation**:
   - Verify that faithfulness remains >= 90% while token cost drops significantly.

### 4. Verification & Testing Commands
```bash
pytest tests/ -v
```

### 5. Git Commit
```bash
git commit -m "feat: optimize costs with model routing and Redis caching"
```

---

## Day 21 — Week 3 Production Readiness Audit & Chaos Testing

### 1. Objective
Subject the platform to failure injection and chaos testing, ensuring high resilience under third-party API outages and database disconnects.

### 2. Architecture & File Layout
```
tests/integration/
└── test_chaos_resilience.py
docs/
└── week-3-review.md
```

### 3. Step-by-Step Implementation Tasks
1. **Chaos Simulation (`tests/integration/test_chaos_resilience.py`)**:
   - Test behavior when OpenAI API returns 429 (Rate Limit) and 500 (Internal Error).
   - Test behavior when Tavily search is down or unreachable.
   - Test behavior when Redis cache drops connection mid-workflow.
   - Verify that research jobs fail gracefully with persisted error logs rather than crashing the worker.
2. **Audit Report (`docs/week-3-review.md`)**:
   - Summarize evaluation metrics, security test outcomes, cost savings, and architectural resilience.

### 4. Verification & Testing Commands
```bash
pytest tests/integration/test_chaos_resilience.py -v
```

### 5. Git Commit
```bash
git commit -m "test: complete week three production audit and chaos testing"
```
