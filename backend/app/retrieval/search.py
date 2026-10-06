"""Three retrieval strategies over the same index:

* vector         — pgvector cosine similarity (HNSW)
* hybrid         — vector + PostgreSQL full-text search, fused with Reciprocal Rank Fusion
* hybrid_rerank  — hybrid candidates re-scored by a cross-encoder
"""

import time
from dataclasses import dataclass, field
from enum import StrEnum

import numpy as np
import psycopg

from app.config import Settings
from app.ingestion.chunker import embedding_text
from app.retrieval.models import Embedder, Reranker


class Mode(StrEnum):
    VECTOR = "vector"
    HYBRID = "hybrid"
    HYBRID_RERANK = "hybrid_rerank"


@dataclass
class RetrievedChunk:
    id: int
    document_id: str
    doc_short_name: str
    doc_title: str
    section_id: str
    section_title: str
    hierarchy: str
    chunk_index: int
    content: str
    score: float = 0.0
    vector_rank: int | None = None
    fulltext_rank: int | None = None
    rerank_score: float | None = None

    @property
    def citation(self) -> str:
        return f"{self.doc_short_name} {self.section_id}"

    @property
    def section_key(self) -> str:
        return f"{self.document_id}:{self.section_id}"


@dataclass
class RetrievalResult:
    chunks: list[RetrievedChunk]
    timings_ms: dict[str, float] = field(default_factory=dict)


def reciprocal_rank_fusion(rankings: list[list[int]], k: int = 60) -> dict[int, float]:
    scores: dict[int, float] = {}
    for ranking in rankings:
        for rank, item in enumerate(ranking, start=1):
            scores[item] = scores.get(item, 0.0) + 1.0 / (k + rank)
    return scores


def tsquery_from_lexemes(lexemes: list[str]) -> str:
    """OR together normalised lexemes; quoting makes the ::tsquery cast take them literally."""
    return " | ".join("'" + lex.replace("\\", "").replace("'", "''") + "'" for lex in lexemes)


class Retriever:
    def __init__(self, conn_factory, embedder: Embedder, reranker_factory, settings: Settings):
        self._connection = conn_factory
        self.embedder = embedder
        self._reranker_factory = reranker_factory
        self._reranker: Reranker | None = None
        self.settings = settings
        self._doc_freq: dict[str, int] | None = None
        self._n_chunks = 0

    @property
    def reranker(self) -> Reranker:
        if self._reranker is None:
            self._reranker = self._reranker_factory()
        return self._reranker

    def refresh_stats(self) -> None:
        self._doc_freq = None

    # ------------------------------------------------------------------ primitives

    def vector_search(self, conn: psycopg.Connection, query_vec: np.ndarray, limit: int) -> list[tuple[int, float]]:
        rows = conn.execute(
            "SELECT id, 1 - (embedding <=> %s) AS similarity FROM chunks ORDER BY embedding <=> %s LIMIT %s",
            (query_vec, query_vec, limit),
        ).fetchall()
        return [(r[0], float(r[1])) for r in rows]

    def _query_lexemes(self, conn: psycopg.Connection, query: str) -> list[str]:
        rows = conn.execute("SELECT lexeme FROM unnest(to_tsvector('english', %s))", (query,)).fetchall()
        lexemes = [r[0] for r in rows]
        max_df = self.settings.fts_max_df
        if max_df >= 1.0:
            return lexemes
        if self._doc_freq is None:
            stats = conn.execute("SELECT word, ndoc FROM ts_stat('SELECT tsv FROM chunks')").fetchall()
            self._doc_freq = {word: ndoc for word, ndoc in stats}
            self._n_chunks = conn.execute("SELECT count(*) FROM chunks").fetchone()[0]
        # Postgres ranking has no IDF; dropping near-ubiquitous terms ("data", "person")
        # stops them from drowning out the discriminative ones.
        kept = [lex for lex in lexemes if self._doc_freq.get(lex, 0) <= max(max_df * self._n_chunks, 1)]
        return kept or lexemes

    def fulltext_search(self, conn: psycopg.Connection, query: str, limit: int) -> list[tuple[int, float]]:
        lexemes = self._query_lexemes(conn, query)
        if not lexemes:
            return []
        rows = conn.execute(
            """
            SELECT id, ts_rank_cd(tsv, q, 1) AS rank
            FROM chunks, CAST(%s AS tsquery) AS q
            WHERE tsv @@ q
            ORDER BY rank DESC, id
            LIMIT %s
            """,
            (tsquery_from_lexemes(lexemes), limit),
        ).fetchall()
        return [(r[0], float(r[1])) for r in rows]

    def fetch_chunks(self, conn: psycopg.Connection, ids: list[int]) -> dict[int, RetrievedChunk]:
        rows = conn.execute(
            """
            SELECT c.id, c.document_id, d.short_name, d.title, c.section_id, c.section_title,
                   c.hierarchy, c.chunk_index, c.content
            FROM chunks c JOIN documents d ON d.id = c.document_id
            WHERE c.id = ANY(%s)
            """,
            (ids,),
        ).fetchall()
        return {r[0]: RetrievedChunk(*r) for r in rows}

    # ------------------------------------------------------------------ strategies

    def retrieve(self, query: str, mode: Mode | str = Mode.HYBRID_RERANK, top_k: int | None = None) -> RetrievalResult:
        mode = Mode(mode)
        top_k = top_k or self.settings.top_k
        depth = self.settings.candidates_per_retriever
        timings: dict[str, float] = {}

        t0 = time.perf_counter()
        query_vec = self.embedder.embed_query(query)
        timings["embed_query"] = (time.perf_counter() - t0) * 1000

        with self._connection() as conn:
            t0 = time.perf_counter()
            vector_hits = self.vector_search(conn, query_vec, depth if mode != Mode.VECTOR else top_k)
            timings["vector_search"] = (time.perf_counter() - t0) * 1000
            vector_rank = {cid: i for i, (cid, _) in enumerate(vector_hits, start=1)}

            fulltext_rank: dict[int, int] = {}
            if mode == Mode.VECTOR:
                ordered = vector_hits
            else:
                t0 = time.perf_counter()
                fulltext_hits = self.fulltext_search(conn, query, depth)
                timings["fulltext_search"] = (time.perf_counter() - t0) * 1000
                fulltext_rank = {cid: i for i, (cid, _) in enumerate(fulltext_hits, start=1)}
                fused = reciprocal_rank_fusion(
                    [[cid for cid, _ in vector_hits], [cid for cid, _ in fulltext_hits]], k=self.settings.rrf_k
                )
                limit = self.settings.rerank_candidates if mode == Mode.HYBRID_RERANK else top_k
                ordered = sorted(fused.items(), key=lambda kv: (-kv[1], kv[0]))[:limit]

            chunks_by_id = self.fetch_chunks(conn, [cid for cid, _ in ordered])

        results = []
        for cid, score in ordered:
            chunk = chunks_by_id[cid]
            chunk.score = score
            chunk.vector_rank = vector_rank.get(cid)
            chunk.fulltext_rank = fulltext_rank.get(cid)
            results.append(chunk)

        if mode == Mode.HYBRID_RERANK and results:
            t0 = time.perf_counter()
            texts = [embedding_text(c.doc_short_name, c.section_id, c.section_title, c.content) for c in results]
            for chunk, score in zip(results, self.reranker.score(query, texts), strict=True):
                chunk.rerank_score = score
                chunk.score = score
            results.sort(key=lambda c: -c.score)
            timings["rerank"] = (time.perf_counter() - t0) * 1000

        timings["total"] = sum(timings.values())
        return RetrievalResult(chunks=results[:top_k], timings_ms=timings)
