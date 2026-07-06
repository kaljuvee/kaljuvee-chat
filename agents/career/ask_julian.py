"""The Ask Julian agent — grounded CV Q&A, no tools."""

from functools import lru_cache

from agents.base import build_agent
from agents.registry import ASK_JULIAN


@lru_cache(maxsize=1)
def build():
    # No tools: answers are grounded purely in the CV + facts in the system prompt.
    return build_agent(ASK_JULIAN, [])
