"""Embedding and reranking models. Both run in-process on CPU via ONNX (fastembed),
so no GPU, PyTorch or paid API is needed."""

import hashlib
import re
from functools import lru_cache
from typing import Protocol

import numpy as np

from app.config import get_settings


class Embedder(Protocol):
    dim: int

    def embed_documents(self, texts: list[str]) -> list[np.ndarray]: ...

    def embed_query(self, text: str) -> np.ndarray: ...


class Reranker(Protocol):
    def score(self, query: str, documents: list[str]) -> list[float]: ...


class FastEmbedEmbedder:
    def __init__(self, model_name: str, dim: int, query_instruction: str = "", cache_dir: str | None = None):
        from fastembed import TextEmbedding

        self.model = TextEmbedding(model_name=model_name, cache_dir=cache_dir)
        self.dim = dim
        self.query_instruction = query_instruction

    def embed_documents(self, texts: list[str]) -> list[np.ndarray]:
        return list(self.model.embed(texts, batch_size=32))

    def embed_query(self, text: str) -> np.ndarray:
        return next(iter(self.model.embed([self.query_instruction + text])))


class FastEmbedReranker:
    def __init__(self, model_name: str, cache_dir: str | None = None):
        from fastembed.rerank.cross_encoder import TextCrossEncoder

        self.model = TextCrossEncoder(model_name=model_name, cache_dir=cache_dir)

    def score(self, query: str, documents: list[str]) -> list[float]:
        return [float(s) for s in self.model.rerank(query, documents, batch_size=16)]


class HashingEmbedder:
    """Deterministic bag-of-words embedder used in tests and CI (no model download)."""

    def __init__(self, dim: int = 768):
        self.dim = dim

    def _vector(self, text: str) -> np.ndarray:
        vec = np.zeros(self.dim, dtype=np.float32)
        for token in re.findall(r"[a-z0-9]+", text.lower()):
            bucket = int(hashlib.md5(token.encode()).hexdigest(), 16) % self.dim
            vec[bucket] += 1.0
        norm = np.linalg.norm(vec)
        return vec / norm if norm else vec

    def embed_documents(self, texts: list[str]) -> list[np.ndarray]:
        return [self._vector(t) for t in texts]

    def embed_query(self, text: str) -> np.ndarray:
        return self._vector(text)


class OverlapReranker:
    """Token-overlap reranker used in tests."""

    def score(self, query: str, documents: list[str]) -> list[float]:
        q = set(re.findall(r"[a-z0-9]+", query.lower()))
        return [float(len(q & set(re.findall(r"[a-z0-9]+", d.lower())))) for d in documents]


@lru_cache
def get_embedder() -> Embedder:
    s = get_settings()
    return FastEmbedEmbedder(s.embedding_model, s.embedding_dim, s.query_instruction, s.model_cache_dir)


@lru_cache
def get_reranker() -> Reranker:
    s = get_settings()
    return FastEmbedReranker(s.reranker_model, s.model_cache_dir)
