from app.config import get_settings
from app.ingestion.chunker import chunk_section, embedding_text
from app.ingestion.parsers import Section, normalize_text, parse_eurlex_html, parse_plain_text
from tests.conftest import load_jsonl

EURLEX_SNIPPET = """<html><body>
<div id="cpt_IV"><p class="oj-ti-section-1">CHAPTER IV</p>
<div id="cpt_IV.tit_1"><p class="oj-ti-section-2">Controller and processor</p></div>
<div class="eli-subdivision" id="art_33">
  <p class="oj-ti-art">Article 33</p>
  <div class="eli-title"><p class="oj-sti-art">Notification of a personal data breach</p></div>
  <p class="oj-normal">1.   The controller shall notify within 72 hours.</p>
  <table><tr><td><p class="oj-normal">(a)</p></td><td><p class="oj-normal">describe the nature of the breach;</p></td></tr></table>
</div></div></body></html>"""


def test_parse_eurlex_html(tmp_path):
    path = tmp_path / "doc.html"
    path.write_text(EURLEX_SNIPPET, encoding="utf-8")
    [section] = parse_eurlex_html(path, "gdpr")
    assert section.section_id == "Article 33"
    assert section.title == "Notification of a personal data breach"
    assert section.hierarchy == "Chapter IV — Controller and processor"
    assert "(a) describe the nature of the breach;" in section.text
    assert "Article 33" not in section.text


def test_normalize_text_joins_list_markers_and_spaces():
    assert normalize_text("(b)\n\nsecond   item\xa0here") == "(b) second item here"


def test_parse_plain_text_splits_on_headings():
    text = "Preamble text\nSection 1. Definitions\nTerm means x.\nSection 2 - Scope\nApplies to y."
    sections = parse_plain_text(text, "doc")
    assert [s.section_id for s in sections] == ["Preamble", "Section 1", "Section 2"]
    assert sections[2].title == "Scope"
    assert sections[2].text == "Applies to y."


def test_parse_plain_text_without_structure_returns_single_section():
    [section] = parse_plain_text("Just some contract text.", "doc")
    assert section.section_id == "Full text"


def test_chunks_respect_budget_and_carry_overlap():
    paragraphs = [f"({i}) " + " ".join(["word"] * 60) for i in range(6)]
    section = Section("d", "Article 1", "Title", "\n".join(paragraphs))
    chunks = chunk_section(section, max_words=150, overlap_words=70)
    assert len(chunks) > 1
    assert all(len(c.content.split()) <= 150 for c in chunks)
    assert [c.chunk_index for c in chunks] == list(range(len(chunks)))
    # The last paragraph of one chunk opens the next one.
    assert chunks[1].content.split("\n")[0] == chunks[0].content.split("\n")[-1]


def test_oversized_paragraph_is_split():
    section = Section("d", "Article 1", "", "Sentence one is here. " * 200)
    chunks = chunk_section(section, max_words=50, overlap_words=0)
    assert all(len(c.content.split()) <= 50 for c in chunks)


def test_embedding_text_has_citation_header():
    assert embedding_text("GDPR", "Article 33", "Breach", "body").startswith("GDPR Article 33 — Breach\n")


def test_bundled_corpus_is_complete():
    settings = get_settings()
    gdpr = load_jsonl(settings.corpus_dir / "gdpr.jsonl")
    dpdp = load_jsonl(settings.corpus_dir / "dpdp.jsonl")
    assert [s["section_id"] for s in gdpr] == [f"Article {i}" for i in range(1, 100)]
    assert [s["section_id"] for s in dpdp] == [f"Section {i}" for i in range(1, 45)] + ["Schedule"]
    assert all(s["title"] and s["text"] for s in gdpr + dpdp)
    # Gazette artefacts must not leak into the text.
    assert not any("GAZETTE OF INDIA" in s["text"] for s in dpdp)
