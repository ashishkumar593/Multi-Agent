"""End-to-end multi-agent research workflow test."""
import pytest
from backend.graph.workflow import ResearchWorkflow
from backend.rag.loaders import DocumentChunk
from backend.rag.retriever import HybridRetriever
from backend.rag.store import VectorStore

def test_full_research_workflow():
    vector_store = VectorStore()
    retriever = HybridRetriever(vector_store=vector_store)

    # Seed sample internal document knowledge
    retriever.index_documents([
        DocumentChunk(
            chunk_id="c_doc_1",
            doc_id="d1",
            content="Generative AI in software engineering increased code development velocity by 30% from 2023 to 2026.",
            page_number=1,
            metadata={"filename": "ai_benchmark.pdf", "source": "https://internal.corp/ai_benchmark.pdf"},
        )
    ])

    workflow = ResearchWorkflow(retriever=retriever)
    topic = "Generative AI in Software Engineering"
    state = workflow.run_sync(topic=topic, scope="comprehensive", max_iterations=1)

    assert state["status"] in ("completed", "completed_with_limitations")
    assert state["plan"] is not None
    assert len(state["plan"].sub_questions) >= 4
    assert len(state["evidence"]) > 0
    assert state["analysis"] is not None
    assert len(state["analysis"].claims) > 0
    assert state["draft_report"] is not None
    assert len(state["draft_report"].body_markdown) > 100
    assert "References" in state["draft_report"].body_markdown

if __name__ == "__main__":
    test_full_research_workflow()
    print("Workflow test passed successfully!")
