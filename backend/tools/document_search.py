"""Document search tool for internal Hybrid RAG retrieval."""
from dataclasses import dataclass
from backend.rag.retriever import HybridRetriever

@dataclass
class DocumentSearchResult:
    chunk_id: str
    doc_id: str
    content: str
    source_title: str
    source_path: str
    page_number: int
    score: float

class DocumentSearchTool:
    """Tool enabling agents to query internal corporate documents."""

    def __init__(self, retriever: HybridRetriever):
        self.retriever = retriever

    def search(self, query: str, top_k: int = 5) -> list[DocumentSearchResult]:
        """Query hybrid index and return formatted document search results."""
        scored_chunks = self.retriever.retrieve(query=query, top_k=top_k)
        results: list[DocumentSearchResult] = []
        for chunk, score in scored_chunks:
            title = str(chunk.metadata.get("filename", "Internal Document"))
            source = str(chunk.metadata.get("source", title))
            results.append(
                DocumentSearchResult(
                    chunk_id=chunk.chunk_id,
                    doc_id=chunk.doc_id,
                    content=chunk.content,
                    source_title=title,
                    source_path=source,
                    page_number=chunk.page_number,
                    score=score,
                )
            )
        return results
