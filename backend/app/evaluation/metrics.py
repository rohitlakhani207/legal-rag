"""Metric definitions (kept deliberately simple so they are easy to audit).

Section keys look like "gdpr:Article 33". Retrieval and citations are scored at the
provision level, not the chunk level: citing any chunk of the right article counts.
"""

import statistics


def recall_at_k(retrieved: list[str], gold: set[str], k: int) -> float:
    """Share of gold provisions that appear in the top-k retrieved chunks."""
    if not gold:
        return 0.0
    return len(gold & set(retrieved[:k])) / len(gold)


def reciprocal_rank(retrieved: list[str], gold: set[str]) -> float:
    for rank, key in enumerate(retrieved, start=1):
        if key in gold:
            return 1.0 / rank
    return 0.0


def citation_accuracy(cited: list[str], invalid_markers: int, gold: set[str]) -> float:
    """1.0 when the answer cites at least one gold provision and has no dangling citations
    (markers that point at no provided source). Extra citations are scored by
    citation_precision instead, since citing a related provision is not necessarily wrong."""
    if invalid_markers:
        return 0.0
    return 1.0 if gold & set(cited) else 0.0


def citation_precision(cited: list[str], gold: set[str], acceptable: set[str]) -> float:
    if not cited:
        return 0.0
    allowed = gold | acceptable
    return sum(1 for c in cited if c in allowed) / len(cited)


def mean(values: list[float]) -> float | None:
    values = [v for v in values if v is not None]
    return statistics.fmean(values) if values else None


def percentile(values: list[float], pct: float) -> float | None:
    values = sorted(v for v in values if v is not None)
    if not values:
        return None
    index = min(len(values) - 1, max(0, round(pct / 100 * (len(values) - 1))))
    return values[index]
