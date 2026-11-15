"""Embedding providers with OpenAI and deterministic local fallbacks."""
import hashlib
import math
from abc import ABC, abstractmethod
from typing import Any

from backend.core.config import settings

class BaseEmbeddingProvider(ABC):
    """Abstract interface for dense embedding generation."""

    @abstractmethod
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Generate embedding vectors for a list of texts."""

    @abstractmethod
    def embed_query(self, query: str) -> list[float]:
        """Generate embedding vector for a single query string."""

class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """OpenAI text-embedding-3-small provider."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or settings.openai_api_key
        self.model = model or settings.embedding_model

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not self.api_key:
            # Fall back to deterministic local embedding when key not set
            return LocalHashEmbeddingProvider().embed_texts(texts)

        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            response = client.embeddings.create(input=texts, model=self.model)
            return [data.embedding for data in response.data]
        except Exception:
            # Fallback on network/API failure
            return LocalHashEmbeddingProvider().embed_texts(texts)

    def embed_query(self, query: str) -> list[float]:
        return self.embed_texts([query])[0]

class LocalHashEmbeddingProvider(BaseEmbeddingProvider):
    """Deterministic hash-based pseudo-embedding provider for offline execution and tests."""

    def __init__(self, dimensions: int = 128):
        self.dimensions = dimensions

    def _hash_vector(self, text: str) -> list[float]:
        vec = [0.0] * self.dimensions
        for word in text.lower().split():
            h = int(hashlib.md5(word.encode()).hexdigest(), 16)
            idx = h % self.dimensions
            vec[idx] += 1.0

        # L2 normalize
        norm = math.sqrt(sum(x * x for x in vec)) or 1.0
        return [x / norm for x in vec]

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [self._hash_vector(t) for t in texts]

    def embed_query(self, query: str) -> list[float]:
        return self._hash_vector(query)
