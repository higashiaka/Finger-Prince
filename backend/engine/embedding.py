"""
Abstracted Embedding Layer
~~~~~~~~~~~~~~~~~~~~~~~~~~
Provides a unified ``EmbeddingProvider`` interface so the vector DB and
search pipeline are decoupled from any specific embedding model.

Supported providers
-------------------
- "openai"       — text-embedding-3-small via the OpenAI API (default)
- "huggingface"  — paraphrase-multilingual-MiniLM-L12-v2 via sentence-transformers

Select via environment variable:
    EMBEDDING_PROVIDER=huggingface  (default: openai)
    OPENAI_API_KEY=sk-...           (required for openai provider)
"""

from __future__ import annotations

import os
from typing import Protocol, runtime_checkable


# ── Protocol ──────────────────────────────────────────────────────────────────

@runtime_checkable
class EmbeddingProvider(Protocol):
    """Minimal interface every embedding backend must satisfy."""

    def embed(self, texts: list[str]) -> list[list[float]]:
        """
        Embed a batch of texts.

        Returns a list of float vectors, one per input text.
        All vectors must have the same dimensionality.
        """
        ...

    @property
    def dimension(self) -> int:
        """Embedding vector size (e.g. 1536 for text-embedding-3-small)."""
        ...


# ── OpenAI ────────────────────────────────────────────────────────────────────

class OpenAIEmbedding:
    """Wraps OpenAI's text-embedding-3-small model."""

    MODEL = "text-embedding-3-small"
    DIMENSION = 1536

    def __init__(self, api_key: str | None = None) -> None:
        import openai  # lazy import — only needed if this provider is used
        self._client = openai.OpenAI(api_key=api_key or os.environ.get("OPENAI_API_KEY", ""))

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        # Strip empty strings to avoid API errors
        sanitized = [t.strip() or " " for t in texts]
        response = self._client.embeddings.create(model=self.MODEL, input=sanitized)
        return [item.embedding for item in response.data]

    @property
    def dimension(self) -> int:
        return self.DIMENSION


# ── HuggingFace (local) ───────────────────────────────────────────────────────

class HuggingFaceEmbedding:
    """
    Uses sentence-transformers for fully offline, multilingual embedding.
    Default model handles Korean text well.
    """

    DEFAULT_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"

    def __init__(self, model_name: str | None = None) -> None:
        from sentence_transformers import SentenceTransformer  # lazy import
        self._model_name = model_name or self.DEFAULT_MODEL
        self._model = SentenceTransformer(self._model_name)

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        vectors = self._model.encode(texts, convert_to_numpy=True)
        return [v.tolist() for v in vectors]

    @property
    def dimension(self) -> int:
        return int(self._model.get_sentence_embedding_dimension())


# ── Factory ───────────────────────────────────────────────────────────────────

class EmbeddingFactory:
    """
    Creates an EmbeddingProvider based on the EMBEDDING_PROVIDER env variable.

    Usage:
        provider = EmbeddingFactory.create()           # uses env var
        provider = EmbeddingFactory.create("openai")   # explicit
    """

    _PROVIDERS: dict[str, type] = {
        "openai": OpenAIEmbedding,
        "huggingface": HuggingFaceEmbedding,
    }

    @staticmethod
    def create(provider: str | None = None) -> EmbeddingProvider:
        name = (provider or os.environ.get("EMBEDDING_PROVIDER", "huggingface")).lower()
        cls = EmbeddingFactory._PROVIDERS.get(name)
        if cls is None:
            raise ValueError(
                f"Unknown embedding provider: '{name}'. "
                f"Choose from: {list(EmbeddingFactory._PROVIDERS)}"
            )
        return cls()
