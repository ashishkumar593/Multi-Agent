"""BM25 lexical retrieval engine for precise keyword, acronym, and entity matching."""
import math
import re
from collections import Counter
from dataclasses import dataclass

from src.backend.rag.loaders import DocumentChunk

@dataclass
class ScoredChunk:
    chunk: DocumentChunk
    score: float

class BM25Retriever:
    """Fast lexical BM25 engine for exact keyword queries."""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.chunks: list[DocumentChunk] = []
        self.corpus_size = 0
        self.avg_doc_len = 0.0
        self.doc_lengths: list[int] = []
        self.doc_freqs: dict[str, int] = {}
        self.term_freqs: list[Counter[str]] = []

    def _tokenize(self, text: str) -> list[str]:
        return re.findall(r"\b\w+\b", text.lower())

    def index(self, chunks: list[DocumentChunk]) -> None:
        """Index a list of document chunks."""
        self.chunks = chunks
        self.corpus_size = len(chunks)
        if self.corpus_size == 0:
            return

        self.term_freqs = []
        self.doc_lengths = []
        total_len = 0
        df: Counter[str] = Counter()

        for chunk in chunks:
            tokens = self._tokenize(chunk.content)
            self.term_freqs.append(Counter(tokens))
            length = len(tokens)
            self.doc_lengths.append(length)
            total_len += length
            df.update(set(tokens))

        self.doc_freqs = dict(df)
        self.avg_doc_len = total_len / self.corpus_size

    def search(self, query: str, top_k: int = 10) -> list[ScoredChunk]:
        """Search indexed chunks for keyword query using BM25Okapi scoring."""
        if self.corpus_size == 0:
            return []

        tokens = self._tokenize(query)
        scores = [0.0] * self.corpus_size

        for token in tokens:
            if token not in self.doc_freqs:
                continue
            df = self.doc_freqs[token]
            idf = math.log((self.corpus_size - df + 0.5) / (df + 0.5) + 1.0)

            for idx in range(self.corpus_size):
                tf = self.term_freqs[idx].get(token, 0)
                if tf == 0:
                    continue
                num = tf * (self.k1 + 1.0)
                denom = tf + self.k1 * (1.0 - self.b + self.b * (self.doc_lengths[idx] / self.avg_doc_len))
                scores[idx] += idf * (num / denom)

        ranked_indices = sorted(range(self.corpus_size), key=lambda i: scores[i], reverse=True)
        results: list[ScoredChunk] = []
        for i in ranked_indices[:top_k]:
            if scores[i] > 0.0:
                results.append(ScoredChunk(chunk=self.chunks[i], score=scores[i]))

        return results
