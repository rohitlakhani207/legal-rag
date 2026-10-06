import logging
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import get_retriever, router
from app.config import get_settings
from app.db import chunk_count, close_pool, connection, init_schema
from app.ingestion.pipeline import ingest_corpus

log = logging.getLogger("legal_rag")


def _bootstrap() -> None:
    """Create the schema, index the bundled corpus if the DB is empty, and load models."""
    settings = get_settings()
    retriever = get_retriever()
    with connection() as conn:
        init_schema(conn, settings)
        if settings.auto_ingest and chunk_count(conn) == 0:
            log.info("Empty index: ingesting bundled corpus from %s", settings.corpus_dir)
            ingest_corpus(conn, retriever.embedder, settings)
    retriever.embedder.embed_query("warm-up")
    retriever.reranker.score("warm-up", ["warm-up"])
    log.info("Models loaded; ready.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    # Model downloads can take minutes on first boot; keep the HTTP server responsive meanwhile.
    if get_settings().startup_bootstrap:
        threading.Thread(target=_bootstrap, name="bootstrap", daemon=True).start()
    yield
    close_pool()


app = FastAPI(
    title="Legal RAG",
    description="Retrieval-augmented legal Q&A over GDPR and India's DPDP Act, running fully locally.",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in get_settings().cors_origins.split(",")],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)
