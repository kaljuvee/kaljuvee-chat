from __future__ import annotations

from functools import lru_cache

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    db_url: str = Field(default="sqlite:///kaljuvee_chat.db", alias="DB_URL")
    app_secret: str = Field(default="ask-julian-2026", alias="APP_SECRET")
    port: int = Field(default=5011, alias="PORT")
    # Public base URL for OAuth redirect + email links. NOT named SERVICE_URL —
    # Coolify reserves the SERVICE_URL* prefix for its own auto-generated magic vars.
    service_url: str = Field(default="https://kaljuvee.chat", alias="APP_BASE_URL")

    # LLM providers (langchain_openai compatible: OpenAI or xAI Grok)
    xai_api_key: str = Field(default="", alias="XAI_API_KEY")
    xai_base_url: str = Field(default="https://api.x.ai/v1", alias="XAI_BASE_URL")
    grok_model: str = Field(default="grok-4-1-fast-reasoning", alias="GROK_MODEL")
    xai_agent_model: str = Field(default="", alias="XAI_AGENT_MODEL")

    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o", alias="OPENAI_MODEL")

    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    anthropic_model: str = Field(default="claude-sonnet-5", alias="ANTHROPIC_MODEL")

    # Provider switch: "xai" (Grok, default), "openai", or "anthropic".
    llm_provider: str = Field(default="xai", alias="LLM_PROVIDER")

    # Anonymous visitors get this many free queries before sign-in is required.
    free_query_limit: int = Field(default=3, alias="FREE_QUERY_LIMIT")


@lru_cache(maxsize=1)
def settings() -> Settings:
    return Settings()
