"""Cross-Encoder neural reranker for high-precision passage scoring."""
from typing import Any
from backend.rag.loaders import DocumentChunk

class CrossEncoderReranker:
    """Reranker using cross-encoder models with graceful fallback."""

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2", lazy_load: bool = True):
        self.model_name = model_name
        self.model: Any = None
        self._load_attempted = False
        if not lazy_load:
            self._load_model()

    def _load_model(self) -> None:
        if self._load_attempted:
            return
        self._load_attempted = True
        try:
            import os
            from pathlib import Path
            # shortcut: only load heavy cross-encoder weights if locally cached or explicitly enabled; prevents network hangs
            hf_cache = Path.home() / ".cache" / "huggingface" / "hub" / f"models--{self.model_name.replace('/', '--')}"
            if not hf_cache.exists() and os.environ.get("ENABLE_CROSS_ENCODER") != "true":
                self.model = None
                return

            from sentence_transformers import CrossEncoder
            self.model = CrossEncoder(self.model_name, local_files_only=True)
        except Exception:
            self.model = None

    def rerank(
        self, query: str, candidates: list[tuple[DocumentChunk, float]], top_n: int = 5
    ) -> list[tuple[DocumentChunk, float]]:
        """Rerank candidate passages against query. Returns top_n re-scored chunks."""
        if not candidates:
            return []

        if self.model is None and not self._load_attempted:
            self._load_model()

        if self.model is None:
            # Fallback to existing fusion scores
            sorted_candidates = sorted(candidates, key=lambda x: x[1], reverse=True)
            return sorted_candidates[:top_n]

        try:
            pairs = [(query, chunk.content) for chunk, _ in candidates]
            scores = self.model.predict(pairs)
            scored = [(chunk, float(score)) for (chunk, _), score in zip(candidates, scores)]
            scored.sort(key=lambda x: x[1], reverse=True)
            return scored[:top_n]
        except Exception:
            sorted_candidates = sorted(candidates, key=lambda x: x[1], reverse=True)
            return sorted_candidates[:top_n]
