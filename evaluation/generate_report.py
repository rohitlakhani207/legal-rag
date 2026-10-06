#!/usr/bin/env python3
"""Render evaluation results as Markdown and keep the README table in sync.

    python evaluation/generate_report.py                 # update README + write results/report.md
    python evaluation/generate_report.py --check         # exit 1 if README is stale (used in CI)
    python evaluation/generate_report.py --results path/to/run.json

Standard library only, so it runs without the backend environment.
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = ROOT / "evaluation" / "results"
README = ROOT / "README.md"
START, END = "<!-- EVAL:START -->", "<!-- EVAL:END -->"

MODE_LABELS = {"vector": "Vector", "hybrid": "Hybrid", "hybrid_rerank": "Hybrid + Reranker"}


def pct(value: float | None) -> str:
    return "—" if value is None else f"{value * 100:.1f}%"


def secs(value: float | None) -> str:
    return "—" if value is None else f"{value:.1f} s"


def ms(value: float | None) -> str:
    return "—" if value is None else f"{value:,.0f} ms"


def _best(summary: dict, key: str, lower_is_better: bool = False) -> float | None:
    values = [s[key] for s in summary.values() if s.get(key) is not None]
    if not values:
        return None
    return min(values) if lower_is_better else max(values)


def _cell(value: float | None, best: float | None, fmt) -> str:
    text = fmt(value)
    return f"**{text}**" if value is not None and best is not None and abs(value - best) < 1e-9 else text


def headline_table(result: dict) -> str:
    summary, config = result["summary"], result["config"]
    k = config["top_k"]
    columns = [
        ("retrieval_recall", f"Retrieval Recall@{k}", pct, False),
        ("citation_accuracy", "Citation Accuracy", pct, False),
        ("faithfulness", "Faithfulness", pct, False),
        ("avg_latency_s", "Avg. Latency", secs, True),
    ]
    lines = [
        "| Approach | " + " | ".join(c[1] for c in columns) + " |",
        "|---|" + "---:|" * len(columns),
    ]
    for mode, label in MODE_LABELS.items():
        if mode not in summary:
            continue
        s = summary[mode]
        cells = [_cell(s.get(key), _best(summary, key, lower), fmt) for key, _, fmt, lower in columns]
        lines.append(f"| {label} | " + " | ".join(cells) + " |")

    hw = config.get("hardware", {})
    any_mode = next(iter(summary.values()))
    lines += [
        "",
        f"<sub>{config['n_questions']} questions ({any_mode['n_answerable']} answerable, "
        f"{config['n_questions'] - any_mode['n_answerable']} unanswerable) · generator `{config.get('generator_model') or '—'}` · "
        f"judge `{config.get('judge_model') or '—'}` · embeddings `{config['embedding_model']}` · "
        f"reranker `{config['reranker_model']}` · CPU only ({hw.get('cpus')} cores, {hw.get('memory_gb')} GB RAM) · "
        f"run `{result['run_id']}`</sub>",
    ]
    return "\n".join(lines)


def detailed_report(result: dict) -> str:
    summary, config = result["summary"], result["config"]
    out = [f"# Evaluation report — `{result['run_id']}`", "", headline_table(result), ""]

    out += ["## All metrics", "", "| Metric | " + " | ".join(MODE_LABELS[m] for m in summary) + " |"]
    out.append("|---|" + "---:|" * len(summary))
    rows = [
        ("Retrieval recall@k", "retrieval_recall", pct),
        ("Hit rate (≥1 gold provision retrieved)", "hit_rate", pct),
        ("MRR", "mrr", lambda v: "—" if v is None else f"{v:.3f}"),
        ("Citation accuracy", "citation_accuracy", pct),
        ("Citation precision", "citation_precision", pct),
        ("Faithfulness", "faithfulness", pct),
        ("Abstained on answerable questions", "abstention_rate_answerable", pct),
        ("Abstained on unanswerable questions (higher is better)", "abstention_rate_unanswerable", pct),
        ("Avg. end-to-end latency", "avg_latency_s", secs),
        ("p95 end-to-end latency", "p95_latency_s", secs),
        ("Avg. retrieval latency", "avg_retrieval_ms", ms),
        ("Avg. generation latency", "avg_generation_s", secs),
    ]
    for label, key, fmt in rows:
        out.append(f"| {label} | " + " | ".join(fmt(s.get(key)) for s in summary.values()) + " |")

    types = sorted({t for s in summary.values() for t in s.get("by_type", {})})
    if types:
        out += ["", "## Retrieval recall by question type", ""]
        out.append("| Type | n | " + " | ".join(MODE_LABELS[m] for m in summary) + " |")
        out.append("|---|---:|" + "---:|" * len(summary))
        for t in types:
            n = next(s["by_type"][t]["n"] for s in summary.values() if t in s.get("by_type", {}))
            cells = [pct(s.get("by_type", {}).get(t, {}).get("retrieval_recall")) for s in summary.values()]
            out.append(f"| {t} | {n} | " + " | ".join(cells) + " |")

    out += ["", "## Per-question results", ""]
    out.append("| Question | Mode | Recall | Citation | Faithful | Latency | Retrieved |")
    out.append("|---|---|---:|---:|---:|---:|---|")
    for r in result["records"]:
        retrieved = ", ".join(dict.fromkeys(c["citation"] for c in r["retrieved"]))
        latency = r.get("latency_ms", r["retrieval_ms"]) / 1000
        out.append(
            f"| `{r['id']}` {r['question']} | {MODE_LABELS[r['mode']]} | {pct(r['recall'])} | "
            f"{pct(r.get('citation_accuracy'))} | {pct(r.get('faithfulness'))} | {latency:.1f} s | {retrieved} |"
        )

    out += ["", "## Configuration", "", "```json", json.dumps(config, indent=2), "```", ""]
    return "\n".join(out)


def update_readme(table: str, check: bool) -> bool:
    text = README.read_text(encoding="utf-8")
    if START not in text or END not in text:
        sys.exit(f"README is missing the {START} / {END} markers")
    before, rest = text.split(START, 1)
    _, after = rest.split(END, 1)
    updated = f"{before}{START}\n{table}\n{END}{after}"
    if updated == text:
        return False
    if check:
        return True
    README.write_text(updated, encoding="utf-8")
    return True


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, default=RESULTS_DIR / "latest.json")
    parser.add_argument("--check", action="store_true", help="fail if the README table is out of date")
    args = parser.parse_args()

    if not args.results.exists():
        sys.exit(f"{args.results} not found. Run the benchmark first: cd backend && python -m app.evaluation")
    result = json.loads(args.results.read_text(encoding="utf-8"))
    table = headline_table(result)
    changed = update_readme(table, args.check)
    if args.check:
        if changed:
            sys.exit("README evaluation table is out of date: run python evaluation/generate_report.py")
        print("README evaluation table is up to date.")
        return
    report_path = args.results.parent / "report.md"
    report_path.write_text(detailed_report(result), encoding="utf-8")
    print(table)
    print(f"\nREADME {'updated' if changed else 'already up to date'}; detailed report: {report_path}")


if __name__ == "__main__":
    main()
