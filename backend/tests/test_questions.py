"""Guards the evaluation set: every gold label must exist and be backed by quoted text."""

import json

from app.config import REPO_ROOT, get_settings
from tests.conftest import load_jsonl


def _corpus() -> dict[tuple[str, str], str]:
    corpus = {}
    for path in get_settings().corpus_dir.glob("*.jsonl"):
        for s in load_jsonl(path):
            corpus[(s["doc_id"], s["section_id"])] = " ".join(f"{s['title']} {s['text']}".split())
    return corpus


def test_questions_are_well_formed_and_grounded():
    questions = json.loads((REPO_ROOT / "evaluation" / "questions.json").read_text(encoding="utf-8"))["questions"]
    corpus = _corpus()
    ids = [q["id"] for q in questions]
    assert len(ids) == len(set(ids)), "duplicate question ids"
    for q in questions:
        for ref in q.get("gold", []) + q.get("acceptable", []):
            assert (ref["doc"], ref["section"]) in corpus, f"{q['id']}: unknown provision {ref}"
        if q["gold"]:
            assert q.get("evidence"), f"{q['id']}: answerable questions need evidence quotes"
        for ev in q.get("evidence", []):
            text = corpus[(ev["doc"], ev["section"])]
            assert " ".join(ev["quote"].split()) in text, f"{q['id']}: quote not found in {ev['section']}"
    assert any(not q["gold"] for q in questions), "keep some unanswerable questions"
