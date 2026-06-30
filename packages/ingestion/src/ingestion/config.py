"""Settings loaded from environment / .env.

Local-first defaults: a local embedding model and an on-disk Chroma index, so the pipeline
runs with zero API keys. Set EMBEDDING_PROVIDER=openai (and OPENAI_API_KEY) to swap in hosted
embeddings, or CHROMA_HOST to point at a Chroma server instead of the local store.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Repo root is four parents up from this file:
# packages/ingestion/src/ingestion/config.py -> groundwork/
REPO_ROOT = Path(__file__).resolve().parents[4]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(REPO_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Embeddings
    embedding_provider: str = "fastembed"  # "fastembed" | "openai"
    fastembed_model: str = "BAAI/bge-small-en-v1.5"
    openai_api_key: str = ""
    openai_embedding_model: str = "text-embedding-3-small"

    # Vector store
    chroma_host: str = ""  # empty -> local PersistentClient at index_path
    index_path: Path = REPO_ROOT / "data" / "index"
    collection_name: str = "groundwork-kb"

    # Corpus + chunking
    kb_path: Path = REPO_ROOT / "packages" / "kb"
    chunk_size: int = 800
    chunk_overlap: int = 120


@lru_cache
def get_settings() -> Settings:
    return Settings()
