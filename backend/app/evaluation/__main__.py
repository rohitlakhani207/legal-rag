"""Run the benchmark.

python -m app.evaluation                      # full run: retrieval + generation + judge
python -m app.evaluation --retrieval-only     # fast, no LLM needed
python -m app.evaluation --limit 5 --modes hybrid_rerank
python -m app.evaluation --resume ../evaluation/results/<run>.progress.jsonl
"""

import argparse
import logging
from pathlib import Path

from app.config import REPO_ROOT, get_settings
from app.db import connection
from app.evaluation.runner import load_questions, run_evaluation
from app.generation.llm import get_llm
from app.retrieval.models import get_embedder, get_reranker
from app.retrieval.search import Mode, Retriever


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m app.evaluation")
    parser.add_argument("--questions", type=Path, default=REPO_ROOT / "evaluation" / "questions.json")
    parser.add_argument("--modes", default=",".join(m.value for m in Mode))
    parser.add_argument("--top-k", type=int, default=None)
    parser.add_argument("--limit", type=int, default=None, help="only the first N questions")
    parser.add_argument("--retrieval-only", action="store_true")
    parser.add_argument("--skip-judge", action="store_true")
    parser.add_argument("--resume", type=Path, default=None)
    parser.add_argument("--tag", default="")
    parser.add_argument("--no-latest", action="store_true", help="do not overwrite results/latest.json")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
    logging.getLogger("httpx").setLevel(logging.WARNING)

    settings = get_settings()
    questions = load_questions(args.questions)[: args.limit]
    modes = [Mode(m.strip()) for m in args.modes.split(",") if m.strip()]
    retriever = Retriever(connection, get_embedder(), get_reranker, settings)
    out = run_evaluation(
        questions=questions,
        modes=modes,
        retriever=retriever,
        llm=None if args.retrieval_only else get_llm(),
        settings=settings,
        output_dir=settings.eval_results_dir,
        top_k=args.top_k or settings.top_k,
        judge=not args.skip_judge,
        resume=args.resume,
        tag=args.tag,
        update_latest=not args.no_latest and not args.retrieval_only,
    )
    print(f"Results written to {out}")


if __name__ == "__main__":
    main()
