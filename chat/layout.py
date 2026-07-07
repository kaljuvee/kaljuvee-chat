"""Page wrappers for the Ask Julian chat app."""

from __future__ import annotations

from fasthtml.common import (
    Html, Head, Body, Meta, Title, Link, Script, NotStr,
    Div, Span, Button,
)

from chat.components import left_pane, center_pane, right_pane, signin_overlay


TAILWIND_CONFIG = """
tailwind.config = {
  theme: {
    extend: {
      colors: {
        ink: { DEFAULT: '#1A1A1A', muted: '#6B7280', dim: '#9CA3AF' },
        surface: { DEFAULT: '#FFFFFF', alt: '#F5F5F5' },
        border: '#E5E5E5',
      },
      fontFamily: {
        display: ['DM Serif Display', 'Georgia', 'serif'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
}
"""

FAVICON = "/img/julian-kaljuvee-portrait.jpeg"


def _head(title: str = "Ask Julian") -> Head:
    return Head(
        Meta(charset="utf-8"),
        Meta(name="viewport", content="width=device-width, initial-scale=1, viewport-fit=cover"),
        Meta(name="theme-color", content="#FFFFFF"),
        Meta(name="description",
             content="Ask Julian — an AI assistant that answers questions about Julian Kaljuvee's career, skills and projects."),
        Meta(name="apple-mobile-web-app-capable", content="yes"),
        Link(rel="icon", href=FAVICON),
        Link(rel="apple-touch-icon", href=FAVICON),
        Link(rel="manifest", href="/static/manifest.json"),
        Title(f"{title} · kaljuvee.chat"),
        Link(rel="preconnect", href="https://fonts.googleapis.com"),
        Link(rel="preconnect", href="https://fonts.gstatic.com", crossorigin=""),
        Link(rel="stylesheet",
             href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=DM+Serif+Display&display=swap"),
        Script(src="https://cdn.tailwindcss.com"),
        Script(NotStr(TAILWIND_CONFIG)),
        Script(src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"),
        Script(src="https://cdn.plot.ly/plotly-2.35.2.min.js"),
        Link(rel="stylesheet", href="/static/app.css"),
    )


def chat_page(user_email=None, sessions=None, current_sid="",
              messages=None, current_agent_slug=None):
    body = Body(
        signin_overlay(),
        Div(id="left-overlay", cls="left-overlay", onclick="toggleLeftPane()"),
        left_pane(user_email=user_email, sessions=sessions, current_sid=current_sid),
        center_pane(messages=messages, current_agent_slug=current_agent_slug),
        Div(id="right-overlay", cls="right-overlay", onclick="toggleArtifactPane()"),
        right_pane(),
        Button(
            NotStr('<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>'),
            Span("Research", cls="toggle-label"),
            id="right-pane-toggle-btn", cls="right-pane-toggle", onclick="toggleArtifactPane()",
        ),
        Script(src="/static/chat.js?v=5"),
        cls="bg-white text-ink font-sans antialiased app",
        **({"data-signed-in": "1"} if user_email else {}),
    )
    return Html(_head("Ask Julian"), body)


def shared_chat_page(title: str = "Shared Chat", messages=None, agent_slug=None):
    msg_els = []
    for m in (messages or []):
        role = m.get("role", "user")
        content = m.get("content", "")
        bubble = Div(content, cls="msg-bubble")
        msg_els.append(Div(bubble, cls=f"msg msg-{role}"))

    body = Body(
        Div(
            Div(
                Div(title, cls="chat-header-title"),
                Div(Div("Shared from Ask Julian · kaljuvee.chat", cls="text-sm text-gray-400"),
                    cls="chat-header-actions"),
                cls="chat-header",
            ),
            Div(*msg_els, id="messages", cls="messages"),
            cls="center-pane", style="max-width:800px;margin:0 auto;",
        ),
        Script(src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"),
        Script(NotStr("""
            document.querySelectorAll('.msg-bubble').forEach(b => {
                if (typeof marked !== 'undefined') b.innerHTML = marked.parse(b.textContent);
            });
        """)),
        cls="bg-white text-ink font-sans antialiased",
    )
    return Html(_head(title), body)
