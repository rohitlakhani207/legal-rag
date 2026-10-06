import json
import re
from functools import lru_cache
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.api.schemas import (
    AskRequest,
    AskResponse,
    CitationOut,
    DocumentOut,
    SearchRequest,
    SearchResponse,
    Source,
    UploadResponse,
)
from app.config import Settings, get_settings
from app.db import chunk_count, connection, init_schema
from app.generation.answer import generate_answer
from app.generation.llm import LLM, OllamaError, get_llm
from app.ingestion.parsers import parse_upload
from app.ingestion.pipeline import ingest_document
from app.retrieval.models import get_embedder, get_reranker
from app.retrieval.search import Mode, RetrievedChunk, Retriever

router = APIRouter()


@lru_cache
def get_retriever() -> Retriever:
    return Retriever(connection, get_embedder(), get_reranker, get_settings())


RetrieverDep = Annotated[Retriever, Depends(get_retriever)]
LLMDep = Annotated[LLM, Depends(get_llm)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


def _sources(chunks: list[RetrievedChunk]) -> list[Source]:
    return [
        Source(
            marker=i,
            chunk_id=c.id,
            document_id=c.document_id,
            doc_short_name=c.doc_short_name,
            doc_title=c.doc_title,
            section_id=c.section_id,
            section_title=c.section_title,
            hierarchy=c.hierarchy,
            citation=c.citation,
            content=c.content,
            score=c.score,
            vector_rank=c.vector_rank,
            fulltext_rank=c.fulltext_rank,
            rerank_score=c.rerank_score,
        )
        for i, c in enumerate(chunks, start=1)
    ]


@router.get("/health")
def health(settings: SettingsDep, llm: LLMDep) -> dict:
    status: dict = {"status": "ok", "database": False, "chunks": 0, "ollama": False}
    try:
        with connection() as conn:
            status["chunks"] = chunk_count(conn)
            status["database"] = True
    except Exception as exc:  # noqa: BLE001 - health must report, not raise
        status["status"] = "degraded"
        status["database_error"] = str(exc)[:200]
    try:
        models = llm.list_models() if hasattr(llm, "list_models") else []
        status["ollama"] = True
        status["generator_model_available"] = any(
            m == settings.ollama_model or m == f"{settings.ollama_model}:latest" for m in models
        )
    except (httpx.HTTPError, OSError) as exc:
        status["status"] = "degraded"
        status["ollama_error"] = str(exc)[:200]
    status["models"] = {
        "generator": settings.ollama_model,
        "judge": settings.effective_judge_model,
        "embedding": settings.embedding_model,
        "reranker": settings.reranker_model,
    }
    return status


@router.get("/config")
def config(settings: SettingsDep) -> dict:
    return {
        "modes": [m.value for m in Mode],
        "default_mode": Mode.HYBRID_RERANK.value,
        "top_k": settings.top_k,
        "generator_model": settings.ollama_model,
        "embedding_model": settings.embedding_model,
        "reranker_model": settings.reranker_model,
    }


@router.get("/documents", response_model=list[DocumentOut])
def list_documents() -> list[DocumentOut]:
    with connection() as conn:
        rows = conn.execute(
            """
            SELECT d.id, d.title, d.short_name, d.jurisdiction, d.source_url,
                   count(DISTINCT c.section_id), count(c.id)
            FROM documents d LEFT JOIN chunks c ON c.document_id = d.id
            GROUP BY d.id ORDER BY d.created_at, d.id
            """
        ).fetchall()
    return [
        DocumentOut(
            id=r[0], title=r[1], short_name=r[2], jurisdiction=r[3], source_url=r[4], sections=r[5], chunks=r[6]
        )
        for r in rows
    ]


@router.post("/documents", response_model=UploadResponse, status_code=201)
def upload_document(
    retriever: RetrieverDep,
    settings: SettingsDep,
    file: UploadFile = File(...),
    title: str = Form(...),
    short_name: str = Form(...),
    jurisdiction: str | None = Form(None),
) -> UploadResponse:
    doc_id = re.sub(r"[^a-z0-9]+", "-", short_name.lower()).strip("-") or "document"
    data = file.file.read()
    if len(data) > 20 * 1024 * 1024:
        raise HTTPException(413, "File too large (max 20 MB)")
    try:
        sections = parse_upload(file.filename or "", data, doc_id)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    with connection() as conn:
        init_schema(conn, settings)
        doc = {"id": doc_id, "title": title, "short_name": short_name, "jurisdiction": jurisdiction}
        chunks = ingest_document(conn, retriever.embedder, settings, doc, sections)
    retriever.refresh_stats()
    return UploadResponse(id=doc_id, sections=len(sections), chunks=chunks)


@router.delete("/documents/{doc_id}", status_code=204)
def delete_document(doc_id: str, retriever: RetrieverDep) -> None:
    with connection() as conn:
        deleted = conn.execute("DELETE FROM documents WHERE id = %s", (doc_id,)).rowcount
        conn.commit()
    if not deleted:
        raise HTTPException(404, f"Unknown document {doc_id!r}")
    retriever.refresh_stats()


@router.post("/search", response_model=SearchResponse)
def search(request: SearchRequest, retriever: RetrieverDep) -> SearchResponse:
    result = retriever.retrieve(request.query, request.mode, request.top_k)
    return SearchResponse(
        query=request.query, mode=request.mode, sources=_sources(result.chunks), timings_ms=result.timings_ms
    )


@router.post("/ask", response_model=AskResponse)
def ask(request: AskRequest, retriever: RetrieverDep, llm: LLMDep, settings: SettingsDep) -> AskResponse:
    result = retriever.retrieve(request.question, request.mode, request.top_k)
    try:
        answer = generate_answer(request.question, result.chunks, llm, settings.ollama_model)
    except (OllamaError, httpx.HTTPError) as exc:
        raise HTTPException(503, f"Local LLM unavailable: {exc}") from exc
    timings = {f"retrieval_{k}": v for k, v in result.timings_ms.items()}
    timings["generation"] = answer.duration_ms
    timings["total"] = result.timings_ms.get("total", 0.0) + answer.duration_ms
    return AskResponse(
        question=request.question,
        mode=request.mode,
        model=answer.model,
        answer=answer.answer,
        abstained=answer.abstained,
        citations=[CitationOut(marker=c.marker, chunk_id=c.chunk_id, label=c.label) for c in answer.citations],
        invalid_citation_markers=answer.invalid_markers,
        sources=_sources(result.chunks),
        timings_ms=timings,
    )


@router.get("/evaluation/latest")
def latest_evaluation(settings: SettingsDep) -> dict:
    path = settings.eval_results_dir / "latest.json"
    if not path.exists():
        raise HTTPException(404, "No evaluation has been run yet. Run: python -m app.evaluation")
    data = json.loads(path.read_text(encoding="utf-8"))
    data["records"] = [
        {
            key: r.get(key)
            for key in (
                "mode",
                "id",
                "type",
                "question",
                "answerable",
                "gold",
                "recall",
                "citation_accuracy",
                "faithfulness",
                "latency_ms",
                "abstained",
                "answer",
            )
        }
        | {"retrieved": [c["citation"] for c in r.get("retrieved", [])]}
        for r in data.get("records", [])
    ]
    return data
