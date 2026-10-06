"""LLM-as-judge faithfulness: the share of answer statements that are supported by the
sources the generator was given. Runs on a local Ollama model, so it costs nothing."""

import json
import re
from dataclasses import dataclass, field

from app.generation.answer import format_sources
from app.generation.llm import LLM
from app.retrieval.search import RetrievedChunk

JUDGE_SYSTEM_PROMPT = """You are a strict fact-checker for answers produced by a legal research assistant.
You receive numbered SOURCES and numbered STATEMENTS taken from an answer.
For each statement decide whether everything it claims is stated in, or directly follows from, the sources.
- Ignore citation markers like [1]; judge only the content of the statement.
- Paraphrases are fine. Extra facts, numbers, deadlines or conditions not found in the sources are NOT supported.
- A statement saying the sources do not answer the question is supported.
Return JSON only: {"verdicts": [{"statement": <number>, "supported": true|false}, ...]} with one entry per statement."""

VERDICT_SCHEMA = {
    "type": "object",
    "properties": {
        "verdicts": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "statement": {"type": "integer"},
                    "supported": {"type": "boolean"},
                },
                "required": ["statement", "supported"],
            },
        }
    },
    "required": ["verdicts"],
}

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])(?:\s*\[\d+(?:[,\s–-]+\d+)*\])*\s+(?=[A-Z“\"(])")
_ABBREVIATIONS = ("e.g.", "i.e.", "Art.", "No.", "s.", "Sec.", "cf.", "etc.")


def split_statements(answer: str) -> list[str]:
    statements: list[str] = []
    for line in answer.splitlines():
        line = re.sub(r"^\s*(?:[-*•]|\d+[.)])\s+", "", line).strip()
        if not line:
            continue
        for piece in _SENTENCE_SPLIT.split(line):
            piece = piece.strip()
            if not piece:
                continue
            if statements and (len(piece.split()) < 4 or statements[-1].endswith(_ABBREVIATIONS)):
                statements[-1] = f"{statements[-1]} {piece}"
            else:
                statements.append(piece)
    return statements


@dataclass
class FaithfulnessResult:
    score: float | None
    statements: list[str] = field(default_factory=list)
    verdicts: list[dict] = field(default_factory=list)
    error: str | None = None


def judge_faithfulness(answer: str, chunks: list[RetrievedChunk], llm: LLM, model: str) -> FaithfulnessResult:
    statements = split_statements(answer)
    if not statements:
        return FaithfulnessResult(score=None, error="empty answer")
    numbered = "\n".join(f"{i}. {s}" for i, s in enumerate(statements, start=1))
    messages = [
        {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
        {"role": "user", "content": f"SOURCES:\n\n{format_sources(chunks)}\n\nSTATEMENTS:\n{numbered}"},
    ]
    result = llm.chat(model, messages, format=VERDICT_SCHEMA, num_predict=400)
    try:
        verdicts = json.loads(result.content)["verdicts"]
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        return FaithfulnessResult(score=None, statements=statements, error=f"unparseable judge output: {exc}")

    supported = {v.get("statement"): bool(v.get("supported")) for v in verdicts if isinstance(v, dict)}
    # A statement the judge skipped counts as unsupported: the burden of proof is on the answer.
    flags = [supported.get(i, False) for i in range(1, len(statements) + 1)]
    return FaithfulnessResult(score=sum(flags) / len(flags), statements=statements, verdicts=verdicts)
