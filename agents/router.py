"""Single-agent router.

There is only one agent (Ask Julian), so routing is trivial — every message goes
to it. Kept as a module so chat.routes can call route()/strip_prefix() unchanged.
"""

from __future__ import annotations

import re

DEFAULT_SLUG = "ask_julian"


def route(message: str) -> str:
    return DEFAULT_SLUG


def strip_prefix(message: str) -> str:
    return re.sub(r"^\w+:\s*", "", message.strip())
