from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(REPO_ROOT / ".env", ".env"), extra="ignore")

    database_url: str = "postgresql://legalrag:legalrag@localhost:5433/legalrag"

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3.5:4b"
    # Judge model for faithfulness scoring; defaults to the generator model when empty.
    judge_model: str = ""
    ollama_num_ctx: int = 8192
    ollama_timeout_s: float = 600.0
    ollama_keep_alive: str = "30m"

    embedding_model: str = "BAAI/bge-base-en-v1.5"
    embedding_dim: int = 768
    # BGE v1.5 models retrieve better when queries carry this instruction prefix.
    query_instruction: str = "Represent this sentence for searching relevant passages: "
    reranker_model: str = "Xenova/ms-marco-MiniLM-L-12-v2"
    model_cache_dir: str | None = None

    chunk_max_words: int = 220
    chunk_overlap_words: int = 40

    top_k: int = 5
    candidates_per_retriever: int = 50
    rerank_candidates: int = 30
    rrf_k: int = 60
    # Full-text search ignores query terms that occur in more than this share of chunks.
    fts_max_df: float = 0.2

    corpus_dir: Path = REPO_ROOT / "data" / "corpus"
    raw_dir: Path = REPO_ROOT / "data" / "raw"
    sources_file: Path = REPO_ROOT / "data" / "sources.json"
    eval_results_dir: Path = REPO_ROOT / "evaluation" / "results"

    auto_ingest: bool = False
    # Load models (and auto-ingest) in a background thread at API startup.
    startup_bootstrap: bool = True
    cors_origins: str = "*"

    @property
    def effective_judge_model(self) -> str:
        return self.judge_model or self.ollama_model


@lru_cache
def get_settings() -> Settings:
    return Settings()
