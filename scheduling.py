"""Scheduling / "book a call" support for the chat.

Mirrors cv_export: a regex to detect a booking intent in a chat message, and a
canned HTML bubble that offers a "Book a call" button (no LLM call). The booking
target is Julian's Cal.com page, overridable via the BOOKING_URL env var.
"""

from __future__ import annotations

import os
import re

BOOKING_URL = os.environ.get("BOOKING_URL", "https://cal.com/kaljuvee")


# ── Request detection ────────────────────────────────────────────────────────

_SCHED_RE = re.compile(
    # "book / schedule / set up / arrange … a call / meeting / chat / time / intro"
    r"\b(?:book|schedule|set[\s-]?up|arrange|organi[sz]e|reserve|grab|find|pick)\b"
    r".{0,24}\b(?:call|meeting|chat|time|slot|intro|demo|appointment|session|conversation|catch[\s-]?up)\b"
    # "call / meeting / chat / catch up … with Julian / him / you"
    r"|\b(?:call|meeting|chat|catch[\s-]?up|conversation|speak|talk)\b.{0,20}\bwith\b.{0,12}\b(?:julian|him|you)\b"
    # "hop / jump / get on a call/chat"
    r"|\b(?:hop|jump|get)\b\s+on\s+a\s+(?:call|chat)\b"
    # "can we talk / could I speak / let's chat / meet"
    r"|\b(?:can|could|shall|let'?s|would love to|want to|i'?d like to)\b.{0,20}\b(?:talk|chat|speak|meet|connect)\b"
    # direct: "book a call", "book time", "book a slot"
    r"|\bbook\b.{0,12}\b(?:call|time|slot|chat|meeting|him|julian)\b"
    # availability / calendar wording
    r"|\byour\s+(?:calendar|availability|diary)\b"
    r"|\bavailab\w*\b.{0,16}\b(?:call|chat|meeting|talk)\b"
    r"|\b(?:cal\.com|calendly)\b",
    re.IGNORECASE,
)


def is_scheduling_request(message: str) -> bool:
    return bool(_SCHED_RE.search(message or ""))


# ── Response HTML (rendered by marked.js in a chat bubble) ───────────────────

def scheduling_response_html() -> str:
    """Markdown/HTML bubble with a 'Book a call' button (reuses the cv-download styling)."""
    return (
        "Happy to help set that up — Julian keeps a few slots open for intro calls. "
        "Pick a time that suits you and it'll land straight on his calendar:\n\n"
        '<div class="cv-downloads">'
        f'<a class="cv-download-btn" href="{BOOKING_URL}" target="_blank" rel="noopener">'
        '<span class="cv-dl-ic">CAL</span> Book a call</a>'
        "</div>\n\n"
        "Prefer email? Reach him directly at **kaljuvee@gmail.com** or on "
        "[LinkedIn](https://www.linkedin.com/in/juliankaljuvee/). "
        "It helps to mention what you'd like to discuss."
    )
