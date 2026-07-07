"""Build the Talk to Julian LangGraph agent, grounded in the CV + curated facts."""

from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path

from langchain_core.tools import BaseTool
from langgraph.prebuilt import create_react_agent

from agents.registry import AgentSpec
from utils.llm import build_agent_llm

log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
SYSTEM_DIR = ROOT / "prompts" / "system"
SHARED_DIR = ROOT / "prompts" / "shared"


def _read(path: Path) -> str:
    return path.read_text() if path.exists() else ""


def _load_system_prompt(slug: str) -> str:
    """Compose persona + CV + curated facts into one grounded system prompt."""
    persona = _read(SYSTEM_DIR / f"{slug}.md")
    cv = _read(SHARED_DIR / "cv.md")
    facts = _read(SHARED_DIR / "career_facts.md")
    if not persona:
        log.warning("no persona prompt for %s", slug)
    parts = [
        persona,
        "# Julian Kaljuvee — CV (verbatim source of truth)\n\n" + cv if cv else "",
        facts,
    ]
    return "\n\n---\n\n".join(p for p in parts if p).strip()


def build_agent(spec: AgentSpec, tools: list[BaseTool]):
    system = _load_system_prompt(spec.slug)
    llm = build_agent_llm()
    return create_react_agent(llm, tools, prompt=system or None)


@lru_cache(maxsize=8)
def cached_agent(slug: str):
    from agents import registry
    spec = registry.by_slug(slug)
    if spec is None:
        raise ValueError(f"unknown agent slug: {slug}")
    import importlib
    module = importlib.import_module(f"agents.{spec.category}.{spec.slug}")
    return module.build()
