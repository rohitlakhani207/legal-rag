"""Benchmark the three retrieval strategies end to end.

Phase 1 retrieves and generates an answer for every (mode, question) pair and checkpoints
each record to a .progress.jsonl file, so long CPU runs can be resumed. Phase 2 scores
faithfulness with the judge model; doing it afterwards means Ollama swaps models once
instead of on every question.
"""

import json
import logging
import os
import platform
import shutil
import time
from collections import defaultdict
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from app.config import Settings
from app.evaluation.judge import judge_faithfulness
from app.evaluation.metrics import (
    citation_accuracy,
    citation_precision,
    mean,
    percentile,
    recall_at_k,
    reciprocal_rank,
)
from app.generation.answer import generate_answer
from app.generation.llm import LLM
from app.retrieval.search import Mode, RetrievedChunk, Retriever

log = logging.getLogger(__name__)


def section_key(ref: dict) -> str:
    return f"{ref['doc']}:{ref['section']}"


def load_questions(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data["questions"] if isinstance(data, dict) else data


def _hardware() -> dict:
    mem_gb = None
    try:
        with open("/proc/meminfo") as f:
            mem_gb = round(int(f.readline().split()[1]) / 1024 / 1024, 1)
    except OSError:
        pass
    return {"machine": platform.machine(), "cpus": os.cpu_count(), "memory_gb": mem_gb, "system": platform.system()}


def evaluate_question(
    question: dict,
    mode: Mode,
    retriever: Retriever,
    llm: LLM | None,
    settings: Settings,
    top_k: int,
) -> dict:
    gold = {section_key(g) for g in question.get("gold", [])}
    acceptable = {section_key(g) for g in question.get("acceptable", [])}
    answerable = bool(gold)

    start = time.perf_counter()
    retrieval = retriever.retrieve(question["question"], mode, top_k)
    retrieval_ms = (time.perf_counter() - start) * 1000
    keys = [c.section_key for c in retrieval.chunks]

    record: dict = {
        "mode": mode.value,
        "id": question["id"],
        "type": question.get("type", ""),
        "question": question["question"],
        "answerable": answerable,
        "gold": sorted(gold),
        "retrieved": [
            {
                "chunk_id": c.id,
                "citation": c.citation,
                "section_key": c.section_key,
                "score": round(c.score, 5),
                "content": c.content,
                "section_title": c.section_title,
                "doc_short_name": c.doc_short_name,
            }
            for c in retrieval.chunks
        ],
        "retrieval_ms": round(retrieval_ms, 1),
        "retrieval_timings_ms": {k: round(v, 1) for k, v in retrieval.timings_ms.items()},
        "recall": recall_at_k(keys, gold, top_k) if answerable else None,
        "reciprocal_rank": reciprocal_rank(keys, gold) if answerable else None,
    }
    if llm is None:
        return record

    answer = generate_answer(question["question"], retrieval.chunks, llm, settings.ollama_model)
    cited = [c.section_key for c in answer.citations]
    record.update(
        {
            "answer": answer.answer,
            "citations": [asdict(c) for c in answer.citations],
            "invalid_markers": answer.invalid_markers,
            "abstained": answer.abstained,
            "generation_ms": round(answer.duration_ms, 1),
            "latency_ms": round(retrieval_ms + answer.duration_ms, 1),
            "completion_tokens": answer.completion_tokens,
            "citation_accuracy": citation_accuracy(cited, len(answer.invalid_markers), gold) if answerable else None,
            "citation_precision": citation_precision(cited, gold, acceptable) if answerable else None,
        }
    )
    return record


def _chunks_from_record(record: dict) -> list[RetrievedChunk]:
    out = []
    for r in record["retrieved"]:
        doc_id, section_id = r["section_key"].split(":", 1)
        out.append(
            RetrievedChunk(
                id=r["chunk_id"],
                document_id=doc_id,
                doc_short_name=r["doc_short_name"],
                doc_title="",
                section_id=section_id,
                section_title=r["section_title"],
                hierarchy="",
                chunk_index=0,
                content=r["content"],
            )
        )
    return out


def summarize(records: list[dict], top_k: int) -> dict:
    by_mode: dict[str, list[dict]] = defaultdict(list)
    for r in records:
        by_mode[r["mode"]].append(r)

    summary = {}
    for mode, rs in by_mode.items():
        answerable = [r for r in rs if r["answerable"]]
        unanswerable = [r for r in rs if not r["answerable"]]
        generated = [r for r in rs if "answer" in r]
        by_type: dict[str, dict] = {}
        for qtype in sorted({r["type"] for r in answerable}):
            subset = [r for r in answerable if r["type"] == qtype]
            by_type[qtype] = {
                "n": len(subset),
                "retrieval_recall": mean([r["recall"] for r in subset]),
                "citation_accuracy": mean([r.get("citation_accuracy") for r in subset]),
            }
        summary[mode] = {
            "n_questions": len(rs),
            "n_answerable": len(answerable),
            "top_k": top_k,
            "retrieval_recall": mean([r["recall"] for r in answerable]),
            "hit_rate": mean([1.0 if r["recall"] else 0.0 for r in answerable]),
            "mrr": mean([r["reciprocal_rank"] for r in answerable]),
            "citation_accuracy": mean([r.get("citation_accuracy") for r in answerable]) if generated else None,
            "citation_precision": mean([r.get("citation_precision") for r in answerable]) if generated else None,
            "faithfulness": mean([r.get("faithfulness") for r in generated]) if generated else None,
            "abstention_rate_answerable": mean([1.0 if r.get("abstained") else 0.0 for r in answerable])
            if generated
            else None,
            "abstention_rate_unanswerable": mean([1.0 if r.get("abstained") else 0.0 for r in unanswerable])
            if generated and unanswerable
            else None,
            "avg_latency_s": mean([r["latency_ms"] / 1000 for r in generated]) if generated else None,
            "p95_latency_s": percentile([r["latency_ms"] / 1000 for r in generated], 95) if generated else None,
            "avg_retrieval_ms": mean([r["retrieval_ms"] for r in rs]),
            "avg_generation_s": mean([r["generation_ms"] / 1000 for r in generated]) if generated else None,
            "by_type": by_type,
        }
    return summary


def run_evaluation(
    *,
    questions: list[dict],
    modes: list[Mode],
    retriever: Retriever,
    llm: LLM | None,
    settings: Settings,
    output_dir: Path,
    top_k: int,
    judge: bool = True,
    resume: Path | None = None,
    tag: str = "",
    update_latest: bool = True,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + (f"-{tag}" if tag else "")
    progress_path = resume or output_dir / f"{run_id}.progress.jsonl"
    if resume:
        run_id = resume.name.removesuffix(".progress.jsonl")

    records: dict[tuple[str, str], dict] = {}
    if progress_path.exists():
        for line in progress_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                records[(r["mode"], r["id"])] = r
        log.info("resuming %s with %d finished records", progress_path.name, len(records))

    # Warm up so model loading time is not billed to the first question.
    if Mode.HYBRID_RERANK in modes:
        retriever.retrieve("warm-up query", Mode.HYBRID_RERANK, top_k)
    if llm is not None:
        llm.chat(settings.ollama_model, [{"role": "user", "content": "Reply with OK."}], num_predict=4)

    total = len(modes) * len(questions)
    with progress_path.open("a", encoding="utf-8") as progress:
        for mode in modes:
            for question in questions:
                if (mode.value, question["id"]) in records:
                    continue
                record = evaluate_question(question, mode, retriever, llm, settings, top_k)
                records[(mode.value, question["id"])] = record
                progress.write(json.dumps(record, ensure_ascii=False) + "\n")
                progress.flush()
                log.info(
                    "[%d/%d] %s %s recall=%s latency=%.1fs",
                    len(records),
                    total,
                    mode.value,
                    question["id"],
                    record["recall"],
                    record.get("latency_ms", record["retrieval_ms"]) / 1000,
                )

    if llm is not None and judge:
        judge_model = settings.effective_judge_model
        to_judge = [r for r in records.values() if "answer" in r and "faithfulness" not in r]
        for i, record in enumerate(to_judge, start=1):
            if record["abstained"]:
                # "The sources do not answer this" makes no claim that could be unsupported.
                record["faithfulness"], record["faithfulness_detail"] = 1.0, {"note": "abstained"}
            else:
                result = judge_faithfulness(record["answer"], _chunks_from_record(record), llm, judge_model)
                record["faithfulness"] = result.score
                record["faithfulness_detail"] = {
                    "statements": result.statements,
                    "verdicts": result.verdicts,
                    "error": result.error,
                }
            log.info(
                "[judge %d/%d] %s %s faithfulness=%s",
                i,
                len(to_judge),
                record["mode"],
                record["id"],
                record["faithfulness"],
            )
        with progress_path.open("w", encoding="utf-8") as progress:
            for r in records.values():
                progress.write(json.dumps(r, ensure_ascii=False) + "\n")

    ordered = [records[(m.value, q["id"])] for m in modes for q in questions if (m.value, q["id"]) in records]
    for r in ordered:
        for chunk in r["retrieved"]:
            chunk.pop("content", None)

    result = {
        "run_id": run_id,
        "created_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "config": {
            "generator_model": settings.ollama_model if llm else None,
            "judge_model": settings.effective_judge_model if llm and judge else None,
            "embedding_model": settings.embedding_model,
            "reranker_model": settings.reranker_model,
            "top_k": top_k,
            "candidates_per_retriever": settings.candidates_per_retriever,
            "rerank_candidates": settings.rerank_candidates,
            "rrf_k": settings.rrf_k,
            "fts_max_df": settings.fts_max_df,
            "chunk_max_words": settings.chunk_max_words,
            "chunk_overlap_words": settings.chunk_overlap_words,
            "n_questions": len(questions),
            "retrieval_only": llm is None,
            "hardware": _hardware(),
        },
        "summary": summarize(ordered, top_k),
        "records": ordered,
    }
    out_path = output_dir / f"{run_id}.json"
    out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    if update_latest:
        shutil.copyfile(out_path, output_dir / "latest.json")
    progress_path.unlink(missing_ok=True)
    return out_path
