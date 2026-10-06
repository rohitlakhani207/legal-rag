import re
from dataclasses import dataclass, field

from app.generation.llm import LLM
from app.retrieval.search import RetrievedChunk

ABSTAIN_MESSAGE = "The provided sources do not answer this question."

SYSTEM_PROMPT = f"""You are a careful legal research assistant. Answer the question using ONLY the numbered sources provided.

Rules:
- End every sentence with the number(s) of the source(s) that support it in square brackets, e.g. [1] or [2][3].
- Name the provision you rely on, e.g. "GDPR Article 33" or "DPDP Act Section 8".
- If the sources do not contain the answer, reply exactly: "{ABSTAIN_MESSAGE}"
- Never use outside knowledge. Be concise: at most 5 sentences of plain text, no Markdown."""

_CITATION = re.compile(r"\[(?:sources?\s*)?(\d+(?:\s*[,;–-]\s*\d+)*)\]", re.IGNORECASE)


@dataclass
class Citation:
    marker: int
    chunk_id: int
    label: str
    section_key: str


@dataclass
class GeneratedAnswer:
    answer: str
    model: str
    citations: list[Citation] = field(default_factory=list)
    invalid_markers: list[int] = field(default_factory=list)
    abstained: bool = False
    duration_ms: float = 0.0
    prompt_tokens: int = 0
    completion_tokens: int = 0


def format_sources(chunks: list[RetrievedChunk]) -> str:
    blocks = []
    for i, chunk in enumerate(chunks, start=1):
        header = f"[{i}] {chunk.citation}"
        if chunk.section_title:
            header += f" — {chunk.section_title}"
        blocks.append(f"{header}\n{chunk.content}")
    return "\n\n".join(blocks)


def build_messages(question: str, chunks: list[RetrievedChunk]) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Sources:\n\n{format_sources(chunks)}\n\nQuestion: {question}"},
    ]


def parse_citation_markers(text: str) -> list[int]:
    """Return citation numbers in order of first appearance; handles [1], [1, 2], [1-3]."""
    markers: list[int] = []
    for group in _CITATION.findall(text):
        for part in re.split(r"\s*[,;]\s*", group):
            if re.search(r"[–-]", part):
                lo, hi = (int(x) for x in re.split(r"\s*[–-]\s*", part))
                numbers = range(lo, hi + 1) if 0 < hi - lo < 20 else [lo, hi]
            else:
                numbers = [int(part)]
            for n in numbers:
                if n not in markers:
                    markers.append(n)
    return markers


def is_abstention(text: str) -> bool:
    return ABSTAIN_MESSAGE.lower().rstrip(".") in text.lower()


def generate_answer(question: str, chunks: list[RetrievedChunk], llm: LLM, model: str) -> GeneratedAnswer:
    if not chunks:
        return GeneratedAnswer(answer=ABSTAIN_MESSAGE, model=model, abstained=True)
    result = llm.chat(model, build_messages(question, chunks), num_predict=400)
    citations, invalid = [], []
    for marker in parse_citation_markers(result.content):
        if 1 <= marker <= len(chunks):
            chunk = chunks[marker - 1]
            citations.append(Citation(marker, chunk.id, chunk.citation, chunk.section_key))
        else:
            invalid.append(marker)
    return GeneratedAnswer(
        answer=result.content,
        model=model,
        citations=citations,
        invalid_markers=invalid,
        abstained=is_abstention(result.content),
        duration_ms=result.duration_ms,
        prompt_tokens=result.prompt_tokens,
        completion_tokens=result.completion_tokens,
    )
