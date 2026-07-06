"""LLM factory — provider-configurable via the LLM_PROVIDER env var.

Supported providers (all via LangChain):
  - xai      → Grok, through the OpenAI-compatible endpoint (default)
  - openai   → OpenAI
  - anthropic→ Claude (requires `langchain-anthropic` installed)

Switch providers by setting LLM_PROVIDER in .env; no code changes needed.
"""

from __future__ import annotations

from functools import lru_cache

from langchain_core.language_models import BaseChatModel

from utils.config import settings


def build_llm(model: str | None = None, temperature: float = 0.0, **kw) -> BaseChatModel:
    s = settings()
    provider = (s.llm_provider or "xai").lower()

    if provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=model or s.openai_model,
            api_key=s.openai_api_key,
            temperature=temperature,
            timeout=300,
            **kw,
        )

    if provider == "anthropic":
        try:
            from langchain_anthropic import ChatAnthropic
        except ImportError as e:  # pragma: no cover
            raise RuntimeError(
                "LLM_PROVIDER=anthropic but langchain-anthropic is not installed. "
                "Run: pip install langchain-anthropic"
            ) from e
        return ChatAnthropic(
            model=model or s.anthropic_model,
            api_key=s.anthropic_api_key,
            temperature=temperature,
            timeout=300,
            **kw,
        )

    # Default: xai / Grok via the OpenAI-compatible API.
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(
        model=model or s.grok_model,
        api_key=s.xai_api_key,
        base_url=s.xai_base_url,
        temperature=temperature,
        timeout=300,
        **kw,
    )


def build_agent_llm(temperature: float = 0.0, **kw) -> BaseChatModel:
    s = settings()
    provider = (s.llm_provider or "xai").lower()
    # Allow a dedicated agent model per provider; fall back to the chat model.
    model = None
    if provider == "xai":
        model = s.xai_agent_model or s.grok_model
    return build_llm(model=model, temperature=temperature, **kw)


@lru_cache(maxsize=1)
def default_llm() -> BaseChatModel:
    return build_llm()
