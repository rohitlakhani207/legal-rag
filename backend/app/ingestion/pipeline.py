import json
import logging
from pathlib import Path

import httpx
import psycopg

from app.config import Settings
from app.db import init_schema
from app.ingestion.chunker import chunk_section, embedding_text
from app.ingestion.parsers import PARSERS, Section
from app.retrieval.models import Embedder

log = logging.getLogger(__name__)


def load_sources(settings: Settings) -> list[dict]:
    return json.loads(settings.sources_file.read_text(encoding="utf-8"))


def download_sources(settings: Settings, force: bool = False) -> list[Path]:
    settings.raw_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    headers = {"User-Agent": "Mozilla/5.0 (legal-rag corpus downloader)"}
    for source in load_sources(settings):
        target = settings.raw_dir / source["filename"]
        if target.exists() and not force:
            log.info("skip %s (already downloaded)", target.name)
        else:
            log.info("download %s", source["url"])
            response = httpx.get(source["url"], headers=headers, follow_redirects=True, timeout=120)
            response.raise_for_status()
            target.write_bytes(response.content)
        paths.append(target)
    return paths


def build_corpus(settings: Settings) -> dict[str, int]:
    """Parse raw downloads into data/corpus/<doc_id>.jsonl (one citable section per line)."""
    settings.corpus_dir.mkdir(parents=True, exist_ok=True)
    counts = {}
    for source in load_sources(settings):
        sections = PARSERS[source["parser"]](settings.raw_dir / source["filename"], source["id"])
        out = settings.corpus_dir / f"{source['id']}.jsonl"
        with out.open("w", encoding="utf-8") as f:
            for section in sections:
                f.write(json.dumps(section.to_dict(), ensure_ascii=False) + "\n")
        counts[source["id"]] = len(sections)
        log.info("%s: %d sections -> %s", source["id"], len(sections), out)
    return counts


def read_corpus(settings: Settings, doc_id: str) -> list[Section]:
    path = settings.corpus_dir / f"{doc_id}.jsonl"
    with path.open(encoding="utf-8") as f:
        return [Section(**json.loads(line)) for line in f if line.strip()]


def ingest_document(
    conn: psycopg.Connection,
    embedder: Embedder,
    settings: Settings,
    doc: dict,
    sections: list[Section],
) -> int:
    """Replace a document's chunks. `doc` needs id, title and short_name."""
    chunks = [c for s in sections for c in chunk_section(s, settings.chunk_max_words, settings.chunk_overlap_words)]
    texts = [embedding_text(doc["short_name"], c.section_id, c.section_title, c.content) for c in chunks]
    vectors = embedder.embed_documents(texts)

    conn.execute(
        """
        INSERT INTO documents (id, title, short_name, jurisdiction, source_url)
        VALUES (%(id)s, %(title)s, %(short_name)s, %(jurisdiction)s, %(url)s)
        ON CONFLICT (id) DO UPDATE SET title = EXCLUDED.title, short_name = EXCLUDED.short_name,
            jurisdiction = EXCLUDED.jurisdiction, source_url = EXCLUDED.source_url
        """,
        {"jurisdiction": None, "url": None, **doc},
    )
    conn.execute("DELETE FROM chunks WHERE document_id = %s", (doc["id"],))
    with conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO chunks (document_id, section_id, section_title, hierarchy, chunk_index, content, embedding)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            [
                (doc["id"], c.section_id, c.section_title, c.hierarchy, c.chunk_index, c.content, v)
                for c, v in zip(chunks, vectors, strict=True)
            ],
        )
    conn.commit()
    return len(chunks)


def ingest_corpus(
    conn: psycopg.Connection, embedder: Embedder, settings: Settings, reset: bool = False
) -> dict[str, int]:
    init_schema(conn, settings, reset=reset)
    counts = {}
    for source in load_sources(settings):
        sections = read_corpus(settings, source["id"])
        counts[source["id"]] = ingest_document(conn, embedder, settings, source, sections)
        log.info("%s: %d chunks indexed", source["id"], counts[source["id"]])
    return counts
