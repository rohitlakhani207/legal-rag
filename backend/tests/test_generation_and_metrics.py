import json

import pytest

from app.evaluation.judge import judge_faithfulness, split_statements
from app.evaluation.metrics import citation_accuracy, citation_precision, percentile, recall_at_k, reciprocal_rank
from app.generation.answer import (
    ABSTAIN_MESSAGE,
    build_messages,
    generate_answer,
    is_abstention,
    parse_citation_markers,
)
from app.retrieval.search import RetrievedChunk, reciprocal_rank_fusion, tsquery_from_lexemes
from tests.conftest import FakeLLM


def _chunk(i: int, section: str, doc: str = "gdpr") -> RetrievedChunk:
    return RetrievedChunk(i, doc, doc.upper(), "", section, "Title", "", 0, f"text of {section}")


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Claim [1]. Other [2][3].", [1, 2, 3]),
        ("Claim [1, 2] and [2].", [1, 2]),
        ("Range [1-3].", [1, 2, 3]),
        ("Source style [Source 4].", [4]),
        ("No citations here.", []),
    ],
)
def test_parse_citation_markers(text, expected):
    assert parse_citation_markers(text) == expected


def test_generate_answer_maps_citations_and_flags_invalid_markers():
    chunks = [_chunk(10, "Article 33"), _chunk(11, "Article 34")]
    llm = FakeLLM(["Notify within 72 hours under GDPR Article 33 [1]. See also [7]."])
    answer = generate_answer("deadline?", chunks, llm, "m")
    assert [c.label for c in answer.citations] == ["GDPR Article 33"]
    assert answer.citations[0].section_key == "gdpr:Article 33"
    assert answer.invalid_markers == [7]
    assert not answer.abstained
    prompt = llm.calls[0]["messages"][1]["content"]
    assert "[1] GDPR Article 33 — Title" in prompt and "Question: deadline?" in prompt


def test_generate_answer_without_sources_abstains_without_calling_llm():
    llm = FakeLLM()
    answer = generate_answer("q", [], llm, "m")
    assert answer.abstained and answer.answer == ABSTAIN_MESSAGE
    assert llm.calls == []


def test_is_abstention():
    assert is_abstention("The provided sources do not answer this question.")
    assert not is_abstention("The controller must notify [1].")


def test_build_messages_has_system_rules():
    messages = build_messages("q", [_chunk(1, "Article 1")])
    assert messages[0]["role"] == "system" and "ONLY" in messages[0]["content"]


def test_retrieval_metrics():
    retrieved = ["gdpr:Article 5", "gdpr:Article 33", "dpdp:Section 8"]
    assert recall_at_k(retrieved, {"gdpr:Article 33", "dpdp:Section 8"}, k=2) == 0.5
    assert recall_at_k(retrieved, {"gdpr:Article 33", "dpdp:Section 8"}, k=3) == 1.0
    assert reciprocal_rank(retrieved, {"gdpr:Article 33"}) == 0.5
    assert reciprocal_rank(retrieved, {"gdpr:Article 99"}) == 0.0


def test_citation_metrics():
    gold, acceptable = {"gdpr:Article 33"}, {"gdpr:Article 34"}
    assert citation_accuracy(["gdpr:Article 33"], 0, gold) == 1.0
    assert citation_accuracy(["gdpr:Article 33", "gdpr:Article 5"], 0, gold) == 1.0
    assert citation_accuracy(["gdpr:Article 5"], 0, gold) == 0.0
    assert citation_accuracy(["gdpr:Article 33"], 1, gold) == 0.0
    assert citation_accuracy([], 0, gold) == 0.0
    assert citation_precision(["gdpr:Article 33", "gdpr:Article 34"], gold, acceptable) == 1.0
    assert citation_precision(["gdpr:Article 33", "gdpr:Article 5"], gold, acceptable) == 0.5


def test_percentile():
    assert percentile([1, 2, 3, 4, 100], 95) == 100
    assert percentile([], 50) is None


def test_reciprocal_rank_fusion_rewards_agreement():
    scores = reciprocal_rank_fusion([[1, 2, 3], [3, 1, 4]], k=60)
    assert max(scores, key=scores.get) == 1
    assert scores[3] > scores[2] and scores[4] < scores[2]


def test_tsquery_quotes_lexemes():
    assert tsquery_from_lexemes(["breach", "o'neil", "e-commerc"]) == "'breach' | 'o''neil' | 'e-commerc'"


def test_split_statements():
    answer = "Controllers must notify within 72 hours [1]. Processors must notify controllers [1][2].\n- Short."
    assert split_statements(answer) == [
        "Controllers must notify within 72 hours [1].",
        "Processors must notify controllers [1][2]. Short.",
    ]


def test_judge_faithfulness_scores_supported_share():
    verdicts = {"verdicts": [{"statement": 1, "supported": True}, {"statement": 2, "supported": False}]}
    llm = FakeLLM([json.dumps(verdicts)])
    result = judge_faithfulness(
        "Notify within 72 hours [1]. Fines are unlimited [1].", [_chunk(1, "Article 33")], llm, "j"
    )
    assert result.score == 0.5
    assert llm.calls[0]["format"]["required"] == ["verdicts"]


def test_judge_missing_verdict_counts_as_unsupported():
    llm = FakeLLM([json.dumps({"verdicts": [{"statement": 1, "supported": True}]})])
    result = judge_faithfulness("First claim here [1]. Second claim here [1].", [_chunk(1, "Article 33")], llm, "j")
    assert result.score == 0.5


def test_judge_handles_garbage_output():
    result = judge_faithfulness("A claim is made [1].", [_chunk(1, "Article 33")], FakeLLM(["not json"]), "j")
    assert result.score is None and "unparseable" in result.error
