"""Structure-aware chunking: chunks never cross a section boundary, prefer paragraph
boundaries, and fall back to sentence splits only for oversized paragraphs."""

import re
from dataclasses import dataclass

from app.ingestion.parsers import Section

_SENTENCE_END = re.compile(r"(?<=[.;:])\s+(?=[A-Z(“])")


@dataclass
class Chunk:
    doc_id: str
    section_id: str
    section_title: str
    hierarchy: str
    chunk_index: int
    content: str


def _words(text: str) -> int:
    return len(text.split())


def _split_long(paragraph: str, max_words: int) -> list[str]:
    pieces, current = [], ""
    for sentence in _SENTENCE_END.split(paragraph):
        if current and _words(current) + _words(sentence) > max_words:
            pieces.append(current)
            current = sentence
        else:
            current = f"{current} {sentence}".strip()
    if current:
        pieces.append(current)
    # A single run-on sentence can still exceed the budget; hard-split on words.
    out = []
    for piece in pieces:
        words = piece.split()
        out.extend(" ".join(words[i : i + max_words]) for i in range(0, len(words), max_words))
    return out


def chunk_section(section: Section, max_words: int = 220, overlap_words: int = 40) -> list[Chunk]:
    units: list[str] = []
    for paragraph in (p.strip() for p in section.text.split("\n")):
        if not paragraph:
            continue
        units.extend(_split_long(paragraph, max_words) if _words(paragraph) > max_words else [paragraph])

    groups: list[list[str]] = []
    current: list[str] = []
    count = 0
    for unit in units:
        size = _words(unit)
        if current and count + size > max_words:
            groups.append(current)
            # Carry trailing paragraphs forward as overlap so context survives the cut.
            carry: list[str] = []
            carried = 0
            for previous in reversed(current):
                if carried + _words(previous) > overlap_words:
                    break
                carry.insert(0, previous)
                carried += _words(previous)
            current, count = carry, carried
        current.append(unit)
        count += size
    if current:
        groups.append(current)

    return [
        Chunk(
            doc_id=section.doc_id,
            section_id=section.section_id,
            section_title=section.title,
            hierarchy=section.hierarchy,
            chunk_index=i,
            content="\n".join(group),
        )
        for i, group in enumerate(groups)
    ]


def embedding_text(short_name: str, chunk_section_id: str, section_title: str, content: str) -> str:
    """Prefix chunks with their citation so 'Article 33'-style queries and titles embed well."""
    header = f"{short_name} {chunk_section_id}"
    if section_title:
        header += f" — {section_title}"
    return f"{header}\n{content}"
