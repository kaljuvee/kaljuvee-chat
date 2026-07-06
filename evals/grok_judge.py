"""A deepeval-compatible LLM judge backed by the same provider the app uses (Grok).

deepeval defaults to OpenAI for its judge; this wraps our provider-agnostic
`build_llm()` so evals run on the configured LLM (xAI Grok by default) with no
extra API keys.
"""

from __future__ import annotations

import json
import re

from deepeval.models import DeepEvalBaseLLM

from utils.config import settings
from utils.llm import build_llm


def _extract_json(text: str) -> dict:
    """Best-effort: pull a JSON object out of an LLM response."""
    text = text.strip()
    # strip ```json ... ``` fences
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence:
        text = fence.group(1)
    else:
        brace = re.search(r"\{.*\}", text, re.DOTALL)
        if brace:
            text = brace.group(0)
    return json.loads(text)


class GrokJudge(DeepEvalBaseLLM):
    def __init__(self, temperature: float = 0.0):
        self._llm = build_llm(temperature=temperature)
        self._name = settings().grok_model or "grok"

    def load_model(self):
        return self._llm

    def _coerce(self, prompt: str, schema):
        raw = self._llm.invoke(prompt).content
        if schema is None:
            return raw
        try:
            return schema.model_validate(_extract_json(raw))
        except Exception:
            fields = list(schema.model_fields.keys())
            strict = (
                prompt
                + f"\n\nReturn ONLY a valid JSON object with exactly these keys: "
                + f"{fields}. No commentary, no markdown fences."
            )
            raw2 = self._llm.invoke(strict).content
            return schema.model_validate(_extract_json(raw2))

    def generate(self, prompt: str, schema=None):
        return self._coerce(prompt, schema)

    async def a_generate(self, prompt: str, schema=None):
        raw = (await self._llm.ainvoke(prompt)).content
        if schema is None:
            return raw
        try:
            return schema.model_validate(_extract_json(raw))
        except Exception:
            fields = list(schema.model_fields.keys())
            strict = (
                prompt
                + f"\n\nReturn ONLY a valid JSON object with exactly these keys: "
                + f"{fields}. No commentary, no markdown fences."
            )
            raw2 = (await self._llm.ainvoke(strict)).content
            return schema.model_validate(_extract_json(raw2))

    def get_model_name(self) -> str:
        return f"GrokJudge({self._name})"
