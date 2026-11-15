"""End-to-end full pipeline smoke test."""
from src.backend.api.app import research_service
from src.backend.rag.loaders import DocumentChunk

def test_e2e_research_service():
    research_service.retriever.index_documents([
        DocumentChunk(
            chunk_id="kb_1",
            doc_id="kb_doc",
            content="Enterprise software systems increasingly incorporate autonomous multi-agent pipelines for automated testing and synthesis.",
            page_number=1,
            metadata={"filename": "enterprise_ai.pdf", "source": "https://corp.internal/enterprise_ai.pdf"},
        )
    ])

    res = research_service.execute_research_sync(
        topic="Autonomous Multi-Agent Pipelines",
        scope="comprehensive",
        max_iterations=1,
    )

    assert res["research_id"].startswith("job_")
    assert res["status"] in ("completed", "completed_with_limitations")
    assert len(res["report_markdown"]) > 50
    assert res["quality_score"] > 0.0
