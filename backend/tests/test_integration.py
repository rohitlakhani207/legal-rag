"""End-to-end tests against a real PostgreSQL + pgvector database, with a hashing
embedder and a fake LLM so they run in CI without downloading any model."""

import json

import pytest
from fastapi.testclient import TestClient

from app.api.routes import get_retriever
from app.evaluation.runner import run_evaluation
from app.generation.llm import get_llm
from app.main import app
from app.retrieval.search import Mode
from tests.conftest import FakeLLM

pytestmark = pytest.mark.integration


@pytest.mark.parametrize("mode", list(Mode))
def test_each_mode_finds_the_breach_article(retriever, mode):
    result = retriever.retrieve("notify supervisory authority personal data breach 72 hours", mode, top_k=2)
    assert result.chunks[0].citation == "GDPR Article 33"
    assert "total" in result.timings_ms


def test_hybrid_records_both_rankings(retriever):
    result = retriever.retrieve("right to erasure, right to be forgotten", Mode.HYBRID, top_k=3)
    top = result.chunks[0]
    assert top.section_id == "Article 17"
    assert top.vector_rank is not None and top.fulltext_rank is not None


def test_fulltext_ignores_stopword_only_queries(retriever, database):
    from app.db import connection

    with connection() as conn:
        assert retriever.fulltext_search(conn, "the and of", 5) == []


@pytest.fixture
def client(retriever):
    llm = FakeLLM(default="The controller must notify within 72 hours under GDPR Article 33 [1].")
    app.dependency_overrides[get_retriever] = lambda: retriever
    app.dependency_overrides[get_llm] = lambda: llm
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_api_ask(client):
    response = client.post("/ask", json={"question": "When must a breach be notified?", "mode": "hybrid", "top_k": 3})
    assert response.status_code == 200
    body = response.json()
    assert body["citations"][0]["label"] == body["sources"][0]["citation"]
    assert body["timings_ms"]["total"] >= body["timings_ms"]["generation"]


def test_api_search_and_documents(client):
    response = client.post("/search", json={"query": "child consent 16 years", "mode": "vector", "top_k": 2})
    assert response.status_code == 200
    assert response.json()["sources"][0]["section_id"] == "Article 8"
    docs = client.get("/documents").json()
    assert docs[0]["id"] == "gdpr" and docs[0]["sections"] == 3


def test_api_validates_mode(client):
    assert client.post("/ask", json={"question": "x?", "mode": "bm25"}).status_code == 422


def test_api_health(client):
    body = client.get("/health").json()
    assert body["database"] is True and body["chunks"] > 0


def test_upload_and_delete_document(client, retriever):
    text = b"Section 1. Scope\nThis Act applies to widgets.\nSection 2. Penalties\nFines up to 10 dollars."
    response = client.post(
        "/documents",
        files={"file": ("widgets.txt", text, "text/plain")},
        data={"title": "Widgets Act", "short_name": "Widgets Act"},
    )
    assert response.status_code == 201, response.text
    assert response.json() == {"id": "widgets-act", "sections": 2, "chunks": 2}
    hits = client.post("/search", json={"query": "widgets penalties fines", "mode": "hybrid", "top_k": 1}).json()
    assert hits["sources"][0]["citation"] == "Widgets Act Section 2"
    assert client.delete("/documents/widgets-act").status_code == 204
    assert client.delete("/documents/widgets-act").status_code == 404


def test_evaluation_runner_end_to_end(retriever, database, tmp_path):
    questions = [
        {
            "id": "q1",
            "type": "specific",
            "question": "breach notification 72 hours supervisory authority",
            "gold": [{"doc": "gdpr", "section": "Article 33"}],
        },
        {"id": "q2", "type": "unanswerable", "question": "maternity leave weeks", "gold": []},
    ]
    llm = FakeLLM(
        responses=[
            "OK",  # warm-up call
            "Notify within 72 hours under GDPR Article 33 [1].",
            "The provided sources do not answer this question.",
            json.dumps({"verdicts": [{"statement": 1, "supported": True}]}),
        ]
    )
    out = run_evaluation(
        questions=questions,
        modes=[Mode.HYBRID],
        retriever=retriever,
        llm=llm,
        settings=database,
        output_dir=tmp_path,
        top_k=2,
    )
    result = json.loads(out.read_text())
    summary = result["summary"]["hybrid"]
    assert summary["retrieval_recall"] == 1.0
    assert summary["citation_accuracy"] == 1.0
    assert summary["faithfulness"] == 1.0
    assert summary["abstention_rate_unanswerable"] == 1.0
    assert (tmp_path / "latest.json").exists()
    assert not list(tmp_path.glob("*.progress.jsonl"))
