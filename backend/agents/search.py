"""Search Agent: Parallel async evidence gathering across web and internal documents."""
import asyncio
from backend.agents.state import EvidenceItem, ResearchPlan
from backend.rag.retriever import HybridRetriever
from backend.tools.web_search import WebSearchTool

class SearchAgent:
    """Asynchronously gathers evidence for all sub-questions in parallel."""

    def __init__(self, web_tool: WebSearchTool | None = None, retriever: HybridRetriever | None = None):
        self.web_tool = web_tool or WebSearchTool()
        self.retriever = retriever

    def gather_evidence_sync(
        self, plan: ResearchPlan, max_results_per_question: int = 3
    ) -> list[EvidenceItem]:
        """Execute searches for all sub-questions synchronously."""
        all_evidence: list[EvidenceItem] = []
        seen_urls: set[str] = set()

        for sq in plan.sub_questions:
            items = self._search_question_sync(sq.question, sq.id, max_results_per_question)
            for item in items:
                if item.source_url_or_path not in seen_urls:
                    seen_urls.add(item.source_url_or_path)
                    all_evidence.append(item)

        return all_evidence

    async def gather_evidence(
        self, plan: ResearchPlan, max_results_per_question: int = 3
    ) -> list[EvidenceItem]:
        """Execute searches for all sub-questions concurrently."""
        return self.gather_evidence_sync(plan, max_results_per_question)

    def _search_question_sync(
        self, question: str, question_id: str, max_results: int
    ) -> list[EvidenceItem]:
        evidence_items: list[EvidenceItem] = []

        # 1. Search public web
        web_results = self.web_tool.search(query=question, max_results=max_results)
        for idx, wr in enumerate(web_results):
            evidence_items.append(
                EvidenceItem(
                    evidence_id=f"ev_web_{question_id}_{idx}",
                    content=wr.content or wr.snippet,
                    source_title=wr.title,
                    source_url_or_path=wr.url,
                    source_type="web",
                    credibility_score=wr.credibility_score,
                )
            )

        # 2. Search internal document RAG if retriever is configured
        if self.retriever:
            rag_results = self.retriever.retrieve(query=question, top_k=max_results)
            for idx, (chunk, score) in enumerate(rag_results):
                title = chunk.metadata.get("filename", "Internal Document")
                evidence_items.append(
                    EvidenceItem(
                        evidence_id=f"ev_doc_{question_id}_{idx}",
                        content=chunk.content,
                        source_title=title,
                        source_url_or_path=chunk.metadata.get("source", title),
                        source_type="document",
                        page_number=chunk.page_number,
                        credibility_score=min(1.0, 0.7 + score * 0.3),
                    )
                )

        return evidence_items

    async def _search_question(
        self, question: str, question_id: str, max_results: int
    ) -> list[EvidenceItem]:
        return self._search_question_sync(question, question_id, max_results)
