# Week 1: Foundation and Production RAG Engine (Days 1–7)
**Detailed Day-by-Day Implementation Specifications**

---

## Day 1 — Project Initialization, Architecture & Development Tooling

### 1. Objective
Establish the foundational structure of the enterprise AI Research Agent repository, including strict Python typing, linting, centralized environment configuration, custom exception hierarchy, and structured JSON logging.

### 2. Architecture & File Layout
```
ai-research-agent/
├── pyproject.toml
├── .env.example
├── .gitignore
├── README.md
├── src/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── logging.py
│   │   └── exceptions.py
└── tests/
    ├── __init__.py
    ├── conftest.py
    └── unit/
        ├── __init__.py
        └── test_config.py
```

### 3. Step-by-Step Implementation Tasks
1. **Tooling & Dependency Configuration (`pyproject.toml`)**:
   - Python version `>=3.11, <3.13`.
   - Core dependencies: `pydantic>=2.9.0`, `pydantic-settings>=2.5.0`, `loguru>=0.7.2` (or `structlog`), `python-dotenv>=1.0.1`.
   - Dev dependencies: `pytest>=8.3.0`, `pytest-asyncio>=0.24.0`, `pytest-cov>=5.0.0`, `ruff>=0.6.5`, `mypy>=1.11.2`.
   - Configure Ruff with rules: `E`, `F`, `W`, `C90`, `I`, `N`, `UP`, `B`, `A`, `SIM`, `TCH`.
   - Configure Mypy with `strict = true`, `disallow_untyped_defs = true`, `no_implicit_optional = true`.
2. **Centralized Configuration (`src/core/config.py`)**:
   - Create `Settings` inheriting from `pydantic_settings.BaseSettings`.
   - Sub-settings models:
     - `AppConfig`: `env: Literal["development", "testing", "production"]`, `app_name: str`, `debug: bool`, `api_prefix: str`.
     - `LLMConfig`: `openai_api_key: SecretStr`, `anthropic_api_key: SecretStr | None`, `default_model: str`, `fast_model: str`, `temperature: float`.
     - `VectorDBConfig`: `chroma_persist_directory: Path`, `collection_name: str`.
     - `PostgresConfig`: `db_host: str`, `db_port: int`, `db_name: str`, `db_user: str`, `db_password: SecretStr`.
     - `RedisConfig`: `redis_url: str`.
     - `SearchConfig`: `tavily_api_key: SecretStr | None`.
3. **Structured Logging (`src/core/logging.py`)**:
   - JSON-formatted log output in production, colorized console in development.
   - Context injection: `request_id`, `job_id`, `agent_name`.
4. **Exception Hierarchy (`src/core/exceptions.py`)**:
   - Base `AppException(Exception)`.
   - `ConfigurationError`, `IngestionError`, `RetrievalError`, `AgentExecutionError`, `SecurityError`, `LLMProviderError`.
5. **Initial Unit Tests (`tests/unit/test_config.py`)**:
   - Verify environment variable overrides, secret string masking, and validation error raising.

### 4. Verification & Testing Commands
```bash
ruff check .
mypy src
pytest tests/unit/test_config.py -v
```

### 5. Git Commit
```bash
git add .
git commit -m "chore: initialize production project architecture"
```

---

## Day 2 — Production Document Ingestion Pipeline

### 1. Objective
Build an enterprise document ingestion pipeline supporting PDF, DOCX, TXT, and Markdown files with file validation, recursive token-aware chunking, deterministic IDs, and SHA-256 deduplication.

### 2. Architecture & File Layout
```
src/rag/
├── __init__.py
├── loaders.py
├── chunker.py
└── ingest.py
tests/unit/
├── test_loaders.py
└── test_chunker.py
scripts/
└── ingest_sample.py
```

### 3. Step-by-Step Implementation Tasks
1. **Document Loaders (`src/rag/loaders.py`)**:
   - Detect MIME types using file signatures (magic bytes) to prevent extension spoofing.
   - Implement `PDFLoader` using `pymupdf` (fitz): extracts page-by-page text, preserving `page_number`, dimensions, and embedded metadata.
   - Implement `DocxLoader` using `python-docx`: extracts paragraphs, headings, and tables.
   - Implement `TextLoader` for `.txt` and `.md` with UTF-8 strictness and fallback decoding.
   - Guard against path traversal (`../`) and reject files exceeding 25MB.
2. **Recursive Chunker (`src/rag/chunker.py`)**:
   - Implement `RecursiveTokenChunker` targeting 800 tokens with 100-token overlap.
   - Preserve natural boundaries: paragraphs (`\n\n`), sentences (`. `), words (` `).
   - Attach chunk metadata: `chunk_index`, `total_chunks`, `parent_doc_id`, `page_number`, `token_count`.
3. **Idempotent Ingestion Engine (`src/rag/ingest.py`)**:
   - Compute SHA-256 hash of file content.
   - Generate deterministic `doc_id = uuid5(NAMESPACE_URL, content_hash)`.
   - Track ingestion records to bypass re-ingesting identical files.
4. **CLI Runner (`scripts/ingest_sample.py`)**:
   - Scans directory, runs ingestion, and outputs a formatted summary table: total files, successful files, chunks created, duration.

### 4. Verification & Testing Commands
```bash
pytest tests/unit/test_loaders.py tests/unit/test_chunker.py -v
python scripts/ingest_sample.py --input-dir ./data/raw
```

### 5. Git Commit
```bash
git commit -m "feat: implement document ingestion pipeline"
```

---

## Day 3 — Embeddings & ChromaDB Persistence

### 1. Objective
Construct a modular embedding provider abstraction and integrate persistent ChromaDB storage with CRUD operations, batching, and metadata filtering.

### 2. Architecture & File Layout
```
src/rag/
├── embeddings.py
└── store.py
tests/integration/
└── test_chroma.py
```

### 3. Step-by-Step Implementation Tasks
1. **Embedding Provider Abstraction (`src/rag/embeddings.py`)**:
   - Define `BaseEmbeddingProvider(ABC)` with `async def embed_documents()` and `async def embed_query()`.
   - Implement `OpenAIEmbeddingProvider` using `openai.AsyncOpenAI` targeting `text-embedding-3-small` (1536 dims).
   - Implement batch chunking (max 512 texts per request) with exponential backoff via `tenacity` on rate limits (`RateLimitError`).
2. **ChromaDB Vector Store (`src/rag/store.py`)**:
   - Implement `ChromaVectorStore`:
     - Initializes persistent client at `settings.vector_db.chroma_persist_directory`.
     - Supports `add_chunks(chunks: list[DocumentChunk])`.
     - Supports `similarity_search(query_embedding, top_k, where_filter)`.
     - Supports `delete_by_doc_id(doc_id: str)`.
   - Store metadata: `doc_id`, `chunk_id`, `filename`, `page_number`, `source_type`.
3. **Integration Testing (`tests/integration/test_chroma.py`)**:
   - Test temporary directory isolation, vector upsert, metadata filtering, and deletion.

### 4. Verification & Testing Commands
```bash
pytest tests/integration/test_chroma.py -v
```

### 5. Git Commit
```bash
git commit -m "feat: integrate embeddings and ChromaDB"
```

---

## Day 4 — Advanced Hybrid Retrieval & Cross-Encoder Reranking

### 1. Objective
Build a hybrid retrieval engine combining dense vector search and sparse BM25 search via Reciprocal Rank Fusion (RRF), followed by neural reranking with a Cross-Encoder.

### 2. Architecture & File Layout
```
src/rag/
├── bm25.py
├── reranker.py
└── retriever.py
tests/integration/
└── test_hybrid_retriever.py
scripts/
└── benchmark_retrieval.py
```

### 3. Step-by-Step Implementation Tasks
1. **Sparse BM25 Index (`src/rag/bm25.py`)**:
   - Tokenize corpus using lowercased alphanumeric tokens with stopword filtering.
   - Build `BM25Okapi` index over chunk text; persist index state to disk using pickle/safetensors.
   - Provide `query(query_text: str, top_k: int) -> list[ScoredChunk]`.
2. **Cross-Encoder Reranker (`src/rag/reranker.py`)**:
   - Load `cross-encoder/ms-marco-MiniLM-L-6-v2` via `sentence-transformers`.
   - Score `(query, chunk_text)` pairs in batches.
   - Provide graceful fallback if GPU/CPU inference fails.
3. **Hybrid Retriever with RRF (`src/rag/retriever.py`)**:
   - Execute dense query (ChromaDB) and sparse query (BM25) concurrently.
   - Merge results using Reciprocal Rank Fusion:
     $$\text{RRF\_Score}(d) = \sum_{m \in \{\text{dense}, \text{sparse}\}} \frac{1}{60 + \text{rank}_m(d)}$$
   - Select top-$N$ candidates and pass to Cross-Encoder reranker.
   - Return final top-$K$ chunks with reranked relevance scores.
4. **Retrieval Benchmark Script (`scripts/benchmark_retrieval.py`)**:
   - Compare Vector-only vs BM25-only vs Hybrid vs Hybrid+Reranker.

### 4. Verification & Testing Commands
```bash
pytest tests/integration/test_hybrid_retriever.py -v
python scripts/benchmark_retrieval.py
```

### 5. Git Commit
```bash
git commit -m "feat: implement hybrid retrieval and reranking"
```

---

## Day 5 — Production Grounded RAG Pipeline with Citation Validation

### 1. Objective
Develop the end-to-end document question-answering pipeline featuring context budgeting, structured Pydantic outputs, and strict inline citation validation.

### 2. Architecture & File Layout
```
src/rag/
├── citations.py
└── pipeline.py
tests/rag/
└── test_rag_pipeline.py
```

### 3. Step-by-Step Implementation Tasks
1. **Citation Registry & Validator (`src/rag/citations.py`)**:
   - Map retrieved chunks to bracketed references: `[1]`, `[2]`.
   - Maintain `CitationRegistry`: verifies that every citation index used in the text points to an existing retrieved chunk in the prompt context.
   - Detect hallucinated citations or citations to non-retrieved sources.
2. **RAG Pipeline Engine (`src/rag/pipeline.py`)**:
   - Assemble context within strict token budgets (e.g. 4,000 tokens for context).
   - Format prompt instructing the model to cite sources directly inline using `[n]`.
   - Implement "insufficient context" guard: if context is inadequate, explicitly output "I don't know based on the provided documents".
   - Support structured answer schema:
     ```python
     class GroundedAnswer(BaseModel):
         answer: str
         citations: list[CitationRef]
         confidence_score: float
         insufficient_context: bool
     ```
3. **Unit & Failure Tests (`tests/rag/test_rag_pipeline.py`)**:
   - Test answer generation, missing context detection, invalid citation rejection, and LLM timeout handling.

### 4. Verification & Testing Commands
```bash
pytest tests/rag/test_rag_pipeline.py -v
```

### 5. Git Commit
```bash
git commit -m "feat: implement cited RAG pipeline"
```

---

## Day 6 — Production Web Research Toolkit

### 1. Objective
Develop a rate-limited web search client using Tavily, an article content extractor, and SSRF security validators.

### 2. Architecture & File Layout
```
src/tools/
├── __init__.py
├── web_search.py
├── webpage_reader.py
└── source_validator.py
tests/security/
└── test_ssrf.py
scripts/
└── test_web_tools.py
```

### 3. Step-by-Step Implementation Tasks
1. **Tavily Web Search Tool (`src/tools/web_search.py`)**:
   - Implement `TavilySearchTool`: query expansion, search depth ("basic" / "advanced"), max results.
   - Normalize output into `WebSearchResult(title, url, snippet, content, published_date, domain)`.
2. **Webpage Scraper (`src/tools/webpage_reader.py`)**:
   - Use `httpx` with timeout (10s) and redirect limits (max 3).
   - Extract primary readable text using `BeautifulSoup4`: strip `<script>`, `<style>`, `<nav>`, `<footer>`, `<aside>`.
   - Convert HTML headings and paragraphs into clean Markdown.
3. **SSRF & Security Validation (`src/tools/source_validator.py`)**:
   - Resolve DNS and block private/loopback IP ranges: `127.0.0.0/8`, `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `169.254.169.254` (cloud metadata).
   - Enforce domain allowlist/denylist capabilities.
   - Calculate source credibility score based on domain TLD (`.edu`, `.gov`, top-tier publications).

### 4. Verification & Testing Commands
```bash
pytest tests/security/test_ssrf.py -v
python scripts/test_web_tools.py --query "generative AI impact software engineering"
```

### 5. Git Commit
```bash
git commit -m "feat: add web research tools"
```

---

## Day 7 — Week 1 Engineering Audit & Quality Gate

### 1. Objective
Conduct a full code review and quality audit across all Week 1 components. Enforce typing, linting, test coverage (>80%), and fix top architectural issues.

### 2. Tasks & Deliverables
1. Run static analysis:
   ```bash
   ruff check . --fix
   mypy src
   pytest tests/ --cov=src --cov-report=term-missing
   ```
2. Verify:
   - Zero hardcoded secrets in code or git history.
   - All external API calls (OpenAI, Tavily) implement retries and timeouts.
   - Ingestion and vector stores handle concurrent reads cleanly.
3. Document audit findings and architecture decisions in `docs/week-1-review.md`.

### 3. Git Commit
```bash
git commit -m "test: complete week one engineering audit"
```
