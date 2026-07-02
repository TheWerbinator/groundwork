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

    # Retrieval
    candidate_pool: int = 20  # chunks each retriever contributes before fusion
    top_k: int = 5  # chunks returned after fusion + rerank
    rrf_k: int = 60  # Reciprocal Rank Fusion constant (Cormack et al. 2009)

    # Agent self-reflection (Phase 5)
    max_retries: int = 1  # how many times the critic may send a weak answer back to re-plan

    # Retrieval backend (Phase 6)
    retrieval_backend: str = "direct"  # "direct" (in-process) | "mcp" (over the MCP protocol)
    mcp_url: str = "http://localhost:9000/mcp"  # Groundwork MCP server (streamable-http)

    # LLM (the agent's answering model)
    default_provider: str = "claude"  # "claude" | "openai" | "ollama"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"  # sonnet by default: cheaper for an agent loop
    openai_model: str = "gpt-5"
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"
    ollama_api_key: str = ""  # set for Ollama Cloud (:cloud models); leave blank for local


@lru_cache
def get_settings() -> Settings:
    return Settings()
