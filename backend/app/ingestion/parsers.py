"""Turn raw legal documents into a flat list of citable sections.

A *section* is the unit we cite and evaluate against: a GDPR article, a section of an
Indian Act, a schedule. Chunking happens later and never crosses section boundaries.
"""

import re
import warnings
from dataclasses import asdict, dataclass
from pathlib import Path

from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)


@dataclass
class Section:
    doc_id: str
    section_id: str
    title: str
    text: str
    hierarchy: str = ""
    ordinal: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


_LIST_MARKER = re.compile(r"^(\((?:[a-z]{1,3}|[ivxlc]+|\d+)\)|\d+\.)\s*\n+", re.MULTILINE)


def normalize_text(text: str) -> str:
    text = text.replace("\xa0", " ").replace(" ", " ")
    # EUR-Lex renders "(a)" and its item text in separate table cells.
    text = _LIST_MARKER.sub(r"\1 ", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# --------------------------------------------------------------------------- EUR-Lex


def _eurlex_hierarchy(article) -> str:
    parts = []
    for div in article.find_parents("div", id=re.compile(r"^cpt_")):
        heading = div.find("p", class_=re.compile(r"^oj-ti-section"), recursive=False)
        title = div.find("div", id=f"{div['id']}.tit_1", recursive=False)
        label = heading.get_text(" ", strip=True) if heading else div["id"]
        label = re.sub(r"^(CHAPTER|SECTION)\b", lambda m: m.group(1).title(), label)
        if title:
            label = f"{label} — {title.get_text(' ', strip=True)}"
        parts.append(label)
    return " > ".join(reversed(parts))


def parse_eurlex_html(path: Path, doc_id: str) -> list[Section]:
    """Parse an EUR-Lex consolidated/OJ HTML page into one Section per article."""
    soup = BeautifulSoup(path.read_text(encoding="utf-8"), "lxml")
    sections = []
    for ordinal, article in enumerate(soup.select("div.eli-subdivision[id^=art_]"), start=1):
        number_el = article.find("p", class_="oj-ti-art")
        title_el = article.find("p", class_="oj-sti-art")
        section_id = number_el.get_text(" ", strip=True)
        title = title_el.get_text(" ", strip=True) if title_el else ""
        for el in (number_el, title_el):
            if el is not None:
                el.decompose()
        body = normalize_text(article.get_text("\n"))
        sections.append(
            Section(
                doc_id=doc_id,
                section_id=normalize_text(section_id),
                title=normalize_text(title),
                text=body,
                hierarchy=_eurlex_hierarchy(article),
                ordinal=ordinal,
            )
        )
    if not sections:
        raise ValueError(f"No articles found in {path}; is this an EUR-Lex HTML page?")
    return sections


# --------------------------------------------------------------------------- Gazette of India

# Body text sits in a central column (x0 >= ~117pt); marginal notes (section titles) and
# "24 of 1997."-style Act references are printed in the outer margins. Classification is
# per word, because margin words can spill a few points into the body column.
_LEFT_MARGIN_X0, _RIGHT_MARGIN_X0 = 110, 482
_HEADER_BOTTOM = 82
_ACT_REFERENCE = re.compile(r"^\d+ of \d{4}\.$")
_CHAPTER = re.compile(r"^CHAPTER ([IVXL]+)$")


@dataclass
class _Line:
    top: float
    words: list[dict]

    @property
    def text(self) -> str:
        return " ".join(w["text"] for w in sorted(self.words, key=lambda w: w["x0"]))


def _group_lines(words: list[dict], tolerance: float = 3.0) -> list[_Line]:
    lines: list[_Line] = []
    for word in sorted(words, key=lambda w: (w["top"], w["x0"])):
        if lines and abs(lines[-1].top - word["top"]) <= tolerance:
            lines[-1].words.append(word)
        else:
            lines.append(_Line(top=word["top"], words=[word]))
    return lines


def _split_page(page) -> tuple[list[_Line], list[_Line]]:
    body, left, right = [], [], []
    for word in page.extract_words():
        if word["top"] < _HEADER_BOTTOM:
            continue
        if word["x0"] < _LEFT_MARGIN_X0:
            left.append(word)
        elif word["x0"] >= _RIGHT_MARGIN_X0:
            right.append(word)
        else:
            body.append(word)
    # Group each margin separately so notes on opposite sides never merge into one line.
    margin = sorted(_group_lines(left) + _group_lines(right), key=lambda line: line.top)
    return _group_lines(body), margin


_PARAGRAPH_START = re.compile(r"^(“?\(\w{1,5}\)|Explanation|Illustration|Provided|\d+\.\s)")
_SMALL_WORDS = {"a", "an", "and", "as", "at", "by", "for", "in", "of", "on", "or", "the", "to"}


def _unwrap(lines: list[str]) -> str:
    """Join PDF hard-wrapped lines back into paragraphs."""
    paragraphs: list[str] = []
    for line in lines:
        if not paragraphs or _PARAGRAPH_START.match(line) or paragraphs[-1].endswith((":—", "––", ":")):
            paragraphs.append(line)
        else:
            paragraphs[-1] += " " + line
    return "\n".join(paragraphs)


def _title_case(text: str) -> str:
    words = text.lower().split()
    return " ".join(w if i and w in _SMALL_WORDS else w.capitalize() for i, w in enumerate(words))


def _margin_notes(lines: list[_Line], page_no: int) -> list[tuple[int, float, str]]:
    notes, current, current_top, last_top = [], [], 0.0, 0.0
    for line in lines:
        text = line.text.strip()
        if not text or _ACT_REFERENCE.match(text):
            continue
        if current and line.top - last_top > 16:  # a vertical gap starts a new note
            notes.append((page_no, current_top, " ".join(current)))
            current = []
        if not current:
            current_top = line.top
        current.append(text)
        last_top = line.top
        if text.endswith("."):
            notes.append((page_no, current_top, " ".join(current)))
            current = []
    if current:
        notes.append((page_no, current_top, " ".join(current)))
    return notes


def _parse_schedule(lines: list[_Line]) -> str:
    """Rebuild the two-column penalty table ("Breach" | "Penalty") as readable rows."""
    header = next((line for line in lines if any(w["text"] == "Penalty" for w in line.words)), None)
    if header is None:
        return "\n".join(line.text for line in lines)
    split_x = next(w["x0"] for w in header.words if w["text"] == "Penalty") - 25
    rows: list[tuple[list[str], list[str]]] = []
    for line in lines:
        ordered = sorted(line.words, key=lambda w: w["x0"])
        left = " ".join(w["text"] for w in ordered if w["x0"] < split_x)
        right = " ".join(w["text"] for w in ordered if w["x0"] >= split_x)
        if left.startswith("————"):
            break
        if re.match(r"^\d+\.\s", left):
            rows.append(([left], [right] if right else []))
        elif rows:
            rows[-1][0].append(left)
            if right:
                rows[-1][1].append(right)
    out = ["Penalties for breach of provisions of this Act or rules made thereunder [See section 33(1)]:"]
    for left, right in rows:
        out.append(f"{' '.join(p for p in left if p)} Penalty: {' '.join(right)}")
    return "\n".join(out)


def parse_india_gazette_pdf(path: Path, doc_id: str) -> list[Section]:
    """Parse an Act as published in the Gazette of India (e.g. the DPDP Act, 2023).

    Sections are detected as numbered paragraphs that follow the previous section number,
    which avoids false positives from numbered lists inside the text. Section titles come
    from the marginal notes aligned with each section's first line.
    """
    import pdfplumber

    body: list[tuple[int, float, str]] = []
    margin: list[tuple[int, float, str]] = []
    schedule_text = ""
    with pdfplumber.open(path) as pdf:
        for page_no, page in enumerate(pdf.pages):
            body_lines, margin_lines = _split_page(page)
            if any(line.text.strip() == "THE SCHEDULE" for line in body_lines):
                schedule_text = _parse_schedule(body_lines)
                continue
            margin.extend(_margin_notes(margin_lines, page_no))
            body.extend((page_no, line.top, line.text.strip()) for line in body_lines)

    start = next((i for i, (_, _, text) in enumerate(body) if text == "CHAPTER I"), 0)
    body = body[start:]

    sections: list[Section] = []
    starts: list[tuple[int, float, int]] = []  # page, top, index into sections
    chapter, expect_title, current = "", False, None
    buffer: list[str] = []

    def flush():
        if current is not None:
            current.text = normalize_text(_unwrap(buffer))

    for page_no, top, text in body:
        chapter_match = _CHAPTER.match(text)
        if chapter_match:
            chapter, expect_title = f"Chapter {chapter_match.group(1)}", True
            continue
        if expect_title:
            chapter = f"{chapter} — {_title_case(text)}"
            expect_title = False
            continue
        number = len(sections) + 1
        match = re.match(rf"^{number}\.\s+(.*)$", text)
        if match:
            flush()
            current = Section(
                doc_id=doc_id, section_id=f"Section {number}", title="", text="", hierarchy=chapter, ordinal=number
            )
            sections.append(current)
            starts.append((page_no, top, len(sections) - 1))
            buffer = [match.group(1)]
        elif current is not None:
            buffer.append(text)
    flush()

    for page_no, top, note in margin:
        candidates = [(abs(s_top - top), idx) for s_page, s_top, idx in starts if s_page == page_no]
        if not candidates:
            continue
        _, idx = min(candidates)
        if not sections[idx].title:
            sections[idx].title = note.rstrip(".")

    if schedule_text:
        sections.append(
            Section(
                doc_id=doc_id,
                section_id="Schedule",
                title="Penalties",
                text=normalize_text(schedule_text),
                hierarchy="The Schedule",
                ordinal=len(sections) + 1,
            )
        )
    if not sections:
        raise ValueError(f"No sections found in {path}")
    return sections


# --------------------------------------------------------------------------- generic uploads

_GENERIC_HEADING = re.compile(
    r"^(?P<id>(?:Article|Section|Rule|Regulation|Clause)\s+\d+[A-Z]?)\.?\s*(?:[-—:.]\s*)?(?P<title>.{0,120})$",
    re.IGNORECASE,
)


def parse_plain_text(text: str, doc_id: str) -> list[Section]:
    """Best-effort split of an uploaded document on 'Article N' / 'Section N' headings."""
    sections: list[Section] = []
    preamble: list[str] = []
    for raw_line in normalize_text(text).splitlines():
        line = raw_line.strip()
        match = _GENERIC_HEADING.match(line)
        if match:
            sections.append(
                Section(
                    doc_id=doc_id,
                    section_id=match.group("id").title(),
                    title=match.group("title").strip(),
                    text="",
                    ordinal=len(sections) + 1,
                )
            )
        elif sections:
            sections[-1].text += line + "\n"
        else:
            preamble.append(line)
    if not sections:
        # No recognisable structure: treat the whole document as one citable unit.
        return [Section(doc_id=doc_id, section_id="Full text", title="", text=normalize_text(text), ordinal=1)]
    if any(preamble):
        sections.insert(0, Section(doc_id=doc_id, section_id="Preamble", title="", text="\n".join(preamble), ordinal=0))
    for s in sections:
        s.text = normalize_text(s.text)
    return [s for s in sections if s.text]


def parse_upload(filename: str, data: bytes, doc_id: str) -> list[Section]:
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf":
        import io

        import pdfplumber

        with pdfplumber.open(io.BytesIO(data)) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
    elif suffix in {".html", ".htm"}:
        text = BeautifulSoup(data, "lxml").get_text("\n")
    elif suffix in {".txt", ".md"}:
        text = data.decode("utf-8", errors="replace")
    else:
        raise ValueError(f"Unsupported file type: {suffix or filename}")
    return parse_plain_text(text, doc_id)


PARSERS = {
    "eurlex_html": parse_eurlex_html,
    "india_gazette_pdf": parse_india_gazette_pdf,
}
