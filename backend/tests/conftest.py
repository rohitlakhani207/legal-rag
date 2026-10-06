import os

# Must be set before app modules read settings. Tests never touch the dev database.
TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL", "postgresql://legalrag:legalrag@localhost:5433/legalrag_test")
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ["EMBEDDING_MODEL"] = "hashing-test"
os.environ["EMBEDDING_DIM"] = "768"
os.environ["STARTUP_BOOTSTRAP"] = "false"

import json  # noqa: E402

import psycopg  # noqa: E402
import pytest  # noqa: E402

from app.generation.llm import ChatResult  # noqa: E402
from app.ingestion.parsers import Section  # noqa: E402


class FakeLLM:
    """Returns canned responses and records every call."""

    def __init__(self, responses: list[str] | None = None, default: str = "Answer [1]."):
        self.responses = list(responses or [])
        self.default = default
        self.calls: list[dict] = []

    def chat(self, model, messages, *, format=None, num_predict=None) -> ChatResult:
        self.calls.append({"model": model, "messages": messages, "format": format})
        content = self.responses.pop(0) if self.responses else self.default
        return ChatResult(content=content, model=model, prompt_tokens=10, completion_tokens=5, duration_ms=1.0)

    def list_models(self) -> list[str]:
        return ["fake:latest"]


@pytest.fixture
def fake_llm() -> FakeLLM:
    return FakeLLM()


SAMPLE_SECTIONS = [
    Section(
        "gdpr",
        "Article 33",
        "Notification of a personal data breach to the supervisory authority",
        "1. In the case of a personal data breach, the controller shall notify the supervisory authority "
        "not later than 72 hours after having become aware of it.",
        "Chapter IV",
        1,
    ),
    Section(
        "gdpr",
        "Article 17",
        "Right to erasure ('right to be forgotten')",
        "1. The data subject shall have the right to obtain from the controller the erasure of personal data "
        "concerning him or her without undue delay.",
        "Chapter III",
        2,
    ),
    Section(
        "gdpr",
        "Article 8",
        "Conditions applicable to child's consent",
        "1. Processing of the personal data of a child shall be lawful where the child is at least 16 years old.",
        "Chapter II",
        3,
    ),
]


def _database_available() -> bool:
    try:
        admin_url = TEST_DATABASE_URL.rsplit("/", 1)[0] + "/postgres"
        dbname = TEST_DATABASE_URL.rsplit("/", 1)[1]
        with psycopg.connect(admin_url, autocommit=True, connect_timeout=3) as conn:
            exists = conn.execute("SELECT 1 FROM pg_database WHERE datname = %s", (dbname,)).fetchone()
            if not exists:
                conn.execute(f'CREATE DATABASE "{dbname}"')
        return True
    except psycopg.OperationalError:
        return False


@pytest.fixture(scope="session")
def database():
    if not _database_available():
        pytest.skip(f"PostgreSQL not reachable at {TEST_DATABASE_URL}")
    from app.config import get_settings
    from app.db import close_pool, connection, init_schema
    from app.ingestion.pipeline import ingest_document
    from app.retrieval.models import HashingEmbedder

    settings = get_settings()
    embedder = HashingEmbedder(settings.embedding_dim)
    with connection() as conn:
        init_schema(conn, settings, reset=True)
        ingest_document(
            conn, embedder, settings, {"id": "gdpr", "title": "GDPR", "short_name": "GDPR"}, SAMPLE_SECTIONS
        )
    yield settings
    close_pool()


@pytest.fixture(scope="session")
def retriever(database):
    from app.db import connection
    from app.retrieval.models import HashingEmbedder, OverlapReranker
    from app.retrieval.search import Retriever

    return Retriever(connection, HashingEmbedder(database.embedding_dim), OverlapReranker, database)


def load_jsonl(path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
