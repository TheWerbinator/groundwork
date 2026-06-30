"""Chat-model factory.

Mirrors the embedder factory in the ingestion package: one `build_chat_model` that returns a
LangChain chat model for whichever provider the config names. The rest of the agent calls
`.invoke(messages)` and reads `.content`, never knowing which provider it got. That uniform
interface is what lets the same graph run on Claude, GPT, or a local Ollama model, and it is
what the Phase 10 eval harness exploits to compare them.
"""

from __future__ import annotations

from ingestion.config import Settings

# Messages are passed as (role, content) tuples, e.g. ("system", "..."), ("human", "...").
# LangChain chat models accept this shorthand and so does the FakeChatModel used in tests.
Message = tuple[str, str]


def build_chat_model(settings: Settings):
    """Return a LangChain chat model for settings.default_provider."""
    provider = settings.default_provider.lower()

    if provider == "claude":
        from langchain_anthropic import ChatAnthropic

        # Note: newer Claude models (e.g. sonnet-4-6) reject `temperature`, so it is omitted
        # here. The model's default sampling is used.
        return ChatAnthropic(
            model=settings.anthropic_model,
            api_key=settings.anthropic_api_key or None,
        )
    if provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key or None,
            temperature=0,
        )
    if provider == "ollama":
        from langchain_ollama import ChatOllama

        # Local Ollama needs no auth. Ollama Cloud (:cloud models) wants the API key as a
        # bearer token; attach it only when set, and point OLLAMA_HOST at https://ollama.com.
        client_kwargs = None
        if settings.ollama_api_key:
            client_kwargs = {
                "headers": {"Authorization": f"Bearer {settings.ollama_api_key}"}
            }
        return ChatOllama(
            model=settings.ollama_model,
            base_url=settings.ollama_host,
            client_kwargs=client_kwargs,
            temperature=0,
        )
    raise ValueError(
        f"Unknown DEFAULT_PROVIDER {provider!r}. Expected 'claude', 'openai', or 'ollama'."
    )
