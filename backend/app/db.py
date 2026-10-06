from collections.abc import Iterator
from contextlib import contextmanager

import psycopg
from pgvector.psycopg import register_vector
from psycopg_pool import ConnectionPool

from app.config import Settings, get_settings

_pool: ConnectionPool | None = None


def _configure(conn: psycopg.Connection) -> None:
    register_vector(conn)
    # The default ef_search (40) caps HNSW results below our candidate depth.
    conn.execute("SET hnsw.ef_search = 200")
    conn.commit()


def ensure_extension(settings: Settings) -> None:
    # register_vector needs the type to exist, so create it on a plain connection first.
    with psycopg.connect(settings.database_url, autocommit=True) as conn:
        conn.execute("CREATE EXTENSION IF NOT EXISTS vector")


def get_pool() -> ConnectionPool:
    global _pool
    if _pool is None:
        settings = get_settings()
        ensure_extension(settings)
        _pool = ConnectionPool(settings.database_url, min_size=1, max_size=8, configure=_configure, open=True)
    return _pool


def close_pool() -> None:
    global _pool
    if _pool is not None:
        _pool.close()
        _pool = None


@contextmanager
def connection() -> Iterator[psycopg.Connection]:
    with get_pool().connection() as conn:
        yield conn


def schema_sql(dim: int) -> str:
    return f"""
    CREATE TABLE IF NOT EXISTS meta (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS documents (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        short_name TEXT NOT NULL,
        jurisdiction TEXT,
        source_url TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    CREATE TABLE IF NOT EXISTS chunks (
        id BIGSERIAL PRIMARY KEY,
        document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
        section_id TEXT NOT NULL,
        section_title TEXT NOT NULL DEFAULT '',
        hierarchy TEXT NOT NULL DEFAULT '',
        chunk_index INT NOT NULL,
        content TEXT NOT NULL,
        embedding vector({dim}) NOT NULL,
        tsv tsvector GENERATED ALWAYS AS (
            setweight(to_tsvector('english', section_id || ' ' || section_title), 'A') ||
            setweight(to_tsvector('english', content), 'B')
        ) STORED,
        UNIQUE (document_id, section_id, chunk_index)
    );
    CREATE INDEX IF NOT EXISTS chunks_embedding_hnsw ON chunks USING hnsw (embedding vector_cosine_ops);
    CREATE INDEX IF NOT EXISTS chunks_tsv_gin ON chunks USING gin (tsv);
    CREATE INDEX IF NOT EXISTS chunks_document ON chunks (document_id);
    """


def init_schema(conn: psycopg.Connection, settings: Settings, reset: bool = False) -> None:
    if reset:
        conn.execute("DROP TABLE IF EXISTS chunks, documents, meta CASCADE")
    conn.execute(schema_sql(settings.embedding_dim))
    row = conn.execute("SELECT value FROM meta WHERE key = 'embedding_model'").fetchone()
    if row is None:
        conn.execute("INSERT INTO meta (key, value) VALUES ('embedding_model', %s)", (settings.embedding_model,))
    elif row[0] != settings.embedding_model:
        raise RuntimeError(
            f"Database was indexed with {row[0]!r} but EMBEDDING_MODEL is {settings.embedding_model!r}. "
            "Re-run ingestion with --reset."
        )
    conn.commit()


def chunk_count(conn: psycopg.Connection) -> int:
    exists = conn.execute("SELECT to_regclass('public.chunks') IS NOT NULL").fetchone()[0]
    if not exists:
        return 0
    return conn.execute("SELECT count(*) FROM chunks").fetchone()[0]
