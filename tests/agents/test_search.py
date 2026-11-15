"""Unit tests for SearchAgent evidence gathering and deduplication."""
from backend.agents.schemas.plan import ResearchPlan, SubQuestion
from backend.agents.search import SearchAgent
from backend.rag.loaders import DocumentChunk
from backend.rag.retriever import HybridRetriever
from backend.rag.store import VectorStore
from backend.rag.bm25 import BM25Retriever
from backend.rag.reranker import CrossEncoderReranker


def test_search_agent_evidence_gathering_and_dedup():
    """Verify search agent collects evidence and deduplicates identical source URLs."""
    # Setup mock plan
    plan = ResearchPlan(
        topic="Generative AI in Software Development",
        objective="Assess developer productivity and labor market impact",
        sub_questions=[
            SubQuestion(
                id="sq1",
                question="How does generative AI impact software engineering productivity?",
                priority=1,
            ),
            SubQuestion(
                id="sq2",
                question="What are junior developer hiring trends with generative AI?",
                priority=2,
            ),
        ],
    )

    agent = SearchAgent()
    evidence = agent.gather_evidence_sync(plan, max_results_per_question=2)

    assert len(evidence) >= 1
    # Verify provenance fields
    for item in evidence:
        assert item.evidence_id.startswith("ev_web_")
        assert len(item.content) > 0
        assert item.source_url_or_path.startswith("http")
        assert item.credibility_score > 0.0

    # Verify no duplicate URLs
    urls = [item.source_url_or_path for item in evidence]
    assert len(urls) == len(set(urls))


def test_search_agent_with_rag_retriever():
    """Verify search agent combines web search and internal RAG retriever."""
    # Setup in-memory RAG
    store = VectorStore(collection_name="test_search_rag")
    chunk = DocumentChunk(
        chunk_id="chunk_test_1",
        doc_id="doc_internal_1",
        content="Internal enterprise survey: 42% engineers use Copilot daily.",
        page_number=3,
        metadata={"filename": "internal_dev_survey.pdf"},
    )
    store.add_chunks([chunk])

    bm25 = BM25Retriever()
    bm25.index([chunk])

    hybrid = HybridRetriever(vector_store=store, bm25_retriever=bm25, reranker=CrossEncoderReranker())
    agent = SearchAgent(retriever=hybrid)

    plan = ResearchPlan(
        topic="Internal developer tooling",
        objective="Verify internal developer survey statistics",
        sub_questions=[
            SubQuestion(
                id="sq_internal",
                question="How many engineers use Copilot daily in our internal survey?",
                priority=1,
                evidence_type="document",
            )
        ],
    )

    evidence = agent.gather_evidence_sync(plan, max_results_per_question=2)
    assert len(evidence) >= 1

    # Check for document source
    sources = [e.source_type for e in evidence]
    assert "document" in sources
