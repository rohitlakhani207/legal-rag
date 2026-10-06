"""Corpus tooling.

python -m app.ingestion download   # fetch raw sources listed in data/sources.json
python -m app.ingestion build      # parse raw files -> data/corpus/*.jsonl
python -m app.ingestion ingest     # chunk + embed data/corpus into PostgreSQL
"""

import argparse
import logging

from app.config import get_settings
from app.db import connection
from app.ingestion.pipeline import build_corpus, download_sources, ingest_corpus
from app.retrieval.models import get_embedder


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(prog="python -m app.ingestion")
    sub = parser.add_subparsers(dest="command", required=True)
    download = sub.add_parser("download")
    download.add_argument("--force", action="store_true")
    sub.add_parser("build")
    ingest = sub.add_parser("ingest")
    ingest.add_argument("--reset", action="store_true", help="drop and recreate tables first")
    args = parser.parse_args()

    settings = get_settings()
    if args.command == "download":
        download_sources(settings, force=args.force)
    elif args.command == "build":
        print(build_corpus(settings))
    elif args.command == "ingest":
        with connection() as conn:
            print(ingest_corpus(conn, get_embedder(), settings, reset=args.reset))


if __name__ == "__main__":
    main()
