"""Registry for the single Talk to Julian career assistant.

Kept as a one-entry registry so the rest of the chat pipeline (router, message
labels) keeps working unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class AgentSpec:
    slug: str
    name: str
    category: str
    icon: str
    one_liner: str
    description: str
    prefix: str
    example_prompts: tuple[str, ...] = field(default_factory=tuple)


ASK_JULIAN = AgentSpec(
    slug="ask_julian",
    name="Talk to Julian",
    category="career",
    icon="●",
    prefix="",
    one_liner="Answers questions about Julian Kaljuvee's career and work.",
    description="A grounded assistant that answers questions about Julian Kaljuvee's "
                "experience, skills, projects and company using his CV as the source of truth.",
    example_prompts=(
        "Can you give me your CV?",
        "What are Julian's strongest skills?",
        "Show his career timeline",
        "How have his skills evolved over time?",
        "What's his experience with GenAI and LLM systems?",
        "Has he worked in private equity or financial services?",
        "Tell me about his company, Predictive Labs.",
        "Is Julian available for contract work?",
    ),
)

AGENTS: tuple[AgentSpec, ...] = (ASK_JULIAN,)
AGENTS_BY_SLUG: dict[str, AgentSpec] = {a.slug: a for a in AGENTS}

# Left-menu sample questions (career-focused chips).
SAMPLE_QUESTIONS: tuple[str, ...] = ASK_JULIAN.example_prompts


def by_slug(slug: str) -> AgentSpec | None:
    return AGENTS_BY_SLUG.get(slug)
