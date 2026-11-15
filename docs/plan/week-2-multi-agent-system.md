# Week 2: Multi-Agent AI System via LangGraph (Days 8–14)
**Detailed Day-by-Day Implementation Specifications**

---

## Day 8 — LangGraph State Management & System Architecture

### 1. Objective
Establish the strongly-typed state schema, data contracts, and cyclic graph design governing the collaborative multi-agent research workflow.

### 2. Architecture & File Layout
```
src/agents/
├── state.py
└── schemas/
    ├── __init__.py
    ├── plan.py
    ├── evidence.py
    ├── analysis.py
    └── report.py
src/graph/
├── __init__.py
└── state.py
docs/
└── agent-workflow.md
tests/agents/
└── test_state.py
```

### 3. Step-by-Step Implementation Tasks
1. **Shared Workflow State (`src/graph/state.py` & `src/agents/state.py`)**:
   - Define `ResearchState(TypedDict)`:
     ```python
     class ResearchState(TypedDict):
         research_id: str
         user_id: str
         topic: str
         scope: str
         plan: Optional[ResearchPlan]
         evidence_items: list[EvidenceItem]
         analysis: Optional[AnalysisReport]
         draft_report: Optional[ReportDraft]
         critic_feedback: Optional[CriticFeedback]
         iteration_count: int
         max_iterations: int
         status: Literal["planning", "searching", "analyzing", "writing", "reviewing", "complete", "failed"]
         errors: list[str]
     ```
2. **Pydantic Data Contracts (`src/agents/schemas/`)**:
   - `plan.py`: `SubQuestion`, `ResearchPlan` (questions, evidence requirements, search priority).
   - `evidence.py`: `EvidenceItem` (`evidence_id`, `claim_or_excerpt`, `source_type`, `url`, `doc_id`, `page`, `confidence`).
   - `analysis.py`: `ClaimSynthesis` (`claim_id`, `text`, `supporting_evidence_ids`, `contradicting_evidence_ids`, `confidence`, `limitations`).
   - `report.py`: `ReportDraft` (sections, tables, citations, bibliography).
3. **Architecture Documentation (`docs/agent-workflow.md`)**:
   - Mermaid diagram specifying nodes: `planner_node`, `search_node`, `analyst_node`, `writer_node`, `critic_node`.
   - Conditional routing rules:
     - If critic identifies missing evidence $\rightarrow$ return to `search_node` (max 2 times).
     - If critic rejects report quality/citations $\rightarrow$ return to `writer_node` (max 1 time).
     - If approved or max iterations reached $\rightarrow$ proceed to `END`.

### 4. Verification & Testing Commands
```bash
pytest tests/agents/test_state.py -v
```

### 5. Git Commit
```bash
git commit -m "feat: implement LangGraph state and schema architecture"
```

---

## Day 9 — Planner Agent Implementation

### 1. Objective
Implement the Planner Agent to decompose an arbitrary research topic into 4–8 structured, non-overlapping research sub-questions and formulate an execution plan.

### 2. Architecture & File Layout
```
src/agents/
├── planner.py
└── prompts/
    └── planner_prompts.py
tests/agents/
└── test_planner.py
```

### 3. Step-by-Step Implementation Tasks
1. **Prompt Engineering (`src/agents/prompts/planner_prompts.py`)**:
   - System prompt emphasizing MECE (Mutually Exclusive, Collectively Exhaustive) query breakdown.
   - Instruct the model to assess whether the topic requires academic studies, industry benchmark data, market statistics, or internal proprietary docs.
2. **Planner Agent Implementation (`src/agents/planner.py`)**:
   - Use structured outputs (`client.beta.chat.completions.parse` or LangChain's `with_structured_output(ResearchPlan)`).
   - Validate that each sub-question has an assigned priority (1 to 5) and designated search queries.
   - Add resilience against vague or adversarial inputs: generate clarification sub-questions or fail safely.
3. **Unit Tests (`tests/agents/test_planner.py`)**:
   - Test broad topics (e.g. "Generative AI in healthcare").
   - Test narrow technical topics (e.g. "PostgreSQL vs ChromaDB for vector retrieval").
   - Test edge cases (blank or single-word inputs).

### 4. Verification & Testing Commands
```bash
pytest tests/agents/test_planner.py -v
```

### 5. Git Commit
```bash
git commit -m "feat: implement planner agent"
```

---

## Day 10 — Search Agent Implementation

### 1. Objective
Build the Search Agent to execute asynchronous, parallel retrievals across external web search (Tavily) and internal document RAG, standardizing and deduplicating results.

### 2. Architecture & File Layout
```
src/agents/
└── search.py
tests/agents/
└── test_search.py
```

### 3. Step-by-Step Implementation Tasks
1. **Asynchronous Parallel Search Orchestration (`src/agents/search.py`)**:
   - Receive `ResearchPlan` from state.
   - For each sub-question, trigger concurrent tasks:
     - Web Search: Query Tavily, fetch top URLs, scrape content.
     - Document RAG: Query hybrid retriever (ChromaDB + BM25 + Cross-Encoder).
   - Use `asyncio.Semaphore(5)` to bound concurrency and prevent rate limits.
2. **Standardization & Deduplication**:
   - Convert all retrieved passages into `EvidenceItem` instances.
   - Deduplicate by exact URL, chunk ID, and semantic embedding similarity (>0.92 cosine similarity).
   - Retain full source attribution (author, title, URL, retrieval timestamp, page number).
3. **Fault Tolerance**:
   - If Tavily fails or hits rate limits, gracefully continue with document RAG results and record warning in `state["errors"]`.
4. **Integration Testing (`tests/agents/test_search.py`)**:
   - Mock external HTTP calls and vector store queries to test parallel gathering and error isolation.

### 4. Verification & Testing Commands
```bash
pytest tests/agents/test_search.py -v
```

### 5. Git Commit
```bash
git commit -m "feat: implement search agent"
```

---

## Day 11 — Analyst Agent Implementation

### 1. Objective
Build the Analyst Agent to synthesize gathered evidence, identify factual contradictions across sources, evaluate credibility, and produce structured analytical findings.

### 2. Architecture & File Layout
```
src/agents/
├── analyst.py
└── prompts/
    └── analyst_prompts.py
tests/agents/
└── test_analyst.py
```

### 3. Step-by-Step Implementation Tasks
1. **Analytical Prompts (`src/agents/prompts/analyst_prompts.py`)**:
   - Instruct LLM to act as a rigorous research analyst: detect conflicting data points, question source authority, and evaluate methodology.
2. **Analyst Agent Implementation (`src/agents/analyst.py`)**:
   - Group evidence by sub-question.
   - Extract atomic factual claims:
     ```python
     class FactualClaim(BaseModel):
         claim_id: str
         statement: str
         supporting_evidence_ids: list[str]
         contradicting_evidence_ids: list[str]
         confidence: Literal["high", "medium", "low"]
         reasoning: str
     ```
   - Highlight knowledge gaps: specify if any sub-question lacks adequate evidence.
3. **Unit Tests (`tests/agents/test_analyst.py`)**:
   - Verify contradiction detection by feeding opposing reports (e.g. Source A says "GDP grew 2%", Source B says "GDP fell 1%").
   - Ensure claims properly cite valid `evidence_id`s.

### 4. Verification & Testing Commands
```bash
pytest tests/agents/test_analyst.py -v
```

### 5. Git Commit
```bash
git commit -m "feat: implement analyst agent"
```

---

## Day 12 — Writer Agent & Report Generation

### 1. Objective
Implement the Writer Agent to synthesize analytical findings into an executive-ready, publication-grade research report with structured sections, comparison tables, and verified citations.

### 2. Architecture & File Layout
```
src/agents/
├── writer.py
└── prompts/
    └── writer_prompts.py
tests/agents/
└── test_writer.py
```

### 3. Step-by-Step Implementation Tasks
1. **Writer Prompts (`src/agents/prompts/writer_prompts.py`)**:
   - Professional executive tone.
   - Strict citation requirement: Every single fact or statistic must include a citation token `[evidence_id]`.
2. **Writer Agent Implementation (`src/agents/writer.py`)**:
   - Generate structured report schema:
     - Executive Summary
     - Research Objective & Scope
     - Methodology
     - Key Findings & In-depth Analysis (organized by sub-question)
     - Comparative Analysis & Data Tables (Markdown tables)
     - Contradictory Evidence & Nuances
     - Limitations of Findings
     - Bibliography / Sources Registry
   - Deterministic Citation Pass: Replace `[evidence_id]` tokens with sequential numbered citations `[1]`, `[2]`, compiling a clean references list at the bottom.
3. **Unit Tests (`tests/agents/test_writer.py`)**:
   - Verify that all claims have matching references in the generated bibliography.

### 4. Verification & Testing Commands
```bash
pytest tests/agents/test_writer.py -v
```

### 5. Git Commit
```bash
git commit -m "feat: implement writer agent and report generation"
```

---

## Day 13 — Complete Multi-Agent LangGraph Orchestration

### 1. Objective
Assemble the complete multi-agent workflow using LangGraph `StateGraph`, implementing conditional edge logic, persistence checkpointing, and CLI execution.

### 2. Architecture & File Layout
```
src/graph/
├── nodes.py
├── edges.py
├── checkpoint.py
└── workflow.py
scripts/
└── run_research.py
tests/agents/
└── test_graph_workflow.py
```

### 3. Step-by-Step Implementation Tasks
1. **Graph Nodes (`src/graph/nodes.py`)**:
   - Define async node functions: `plan_node`, `search_node`, `analyst_node`, `writer_node`, `critic_node`.
   - Update `state["status"]` and log agent execution metrics.
2. **Conditional Edges (`src/graph/edges.py`)**:
   - `route_after_critic`:
     - If `critic.approved == True` $\rightarrow$ `END`.
     - If `critic.has_missing_evidence == True` and `iteration_count < max_iterations` $\rightarrow$ `search_node`.
     - If `critic.needs_revision == True` and `iteration_count < max_iterations` $\rightarrow$ `writer_node`.
     - Else $\rightarrow$ `END` (append limitations section).
3. **Checkpointing & Persistence (`src/graph/checkpoint.py`)**:
   - Configure `MemorySaver` for testing and `PostgresSaver` interface for production.
4. **Workflow Compilation (`src/graph/workflow.py`)**:
   - Assemble `StateGraph`, add nodes, conditional edges, and compile runnable app.
5. **CLI Runner (`scripts/run_research.py`)**:
   - Stream graph execution events, printing real-time progress to console.

### 4. Verification & Testing Commands
```bash
pytest tests/agents/test_graph_workflow.py -v
python scripts/run_research.py --topic "Impact of Generative AI on Software Engineering 2023-2026"
```

### 5. Git Commit
```bash
git commit -m "feat: wire full multi-agent LangGraph workflow"
```

---

## Day 14 — Critic Agent & Week 2 Review

### 1. Objective
Implement the Critic Agent to independently verify report assertions, check for hallucinations and citation fidelity, and perform the Week 2 system audit.

### 2. Architecture & File Layout
```
src/agents/
├── critic.py
└── prompts/
    └── critic_prompts.py
docs/
└── week-2-review.md
tests/agents/
└── test_critic.py
```

### 3. Step-by-Step Implementation Tasks
1. **Critic Prompts & Logic (`src/agents/critic.py`)**:
   - Verify that all claims in `draft_report` are strictly supported by `evidence_items`.
   - Check for unreferenced statistics, exaggerated conclusions, or missed sub-questions.
   - Output `CriticFeedback`:
     - `approved: bool`
     - `quality_score: float` (0.0 to 10.0)
     - `unsupported_claims: list[str]`
     - `missing_evidence_queries: list[str]`
     - `critique_summary: str`
2. **Adversarial Testing (`tests/agents/test_critic.py`)**:
   - Test critic with reports containing deliberate hallucinations (e.g. "Quantum AI replaced 99% of coders in 2024") and verify rejection.
3. **Week 2 Audit**:
   - Execute full agent pipeline test suite.
   - Verify checkpoint resumption on paused workflows.
   - Author `docs/week-2-review.md`.

### 4. Verification & Testing Commands
```bash
pytest tests/agents/ -v
```

### 5. Git Commit
```bash
git commit -m "feat: implement critic agent and complete week two review"
```
