"""/visuals — a shareable, tabbed charts dashboard inside the 3-pane app shell.

Each tab is a real URL (``/visuals?tab=skills``) so views are bookmarkable/shareable
— no chat overlay, same pattern as a normal app page.
"""

from __future__ import annotations

import json

from fasthtml.common import Html, Body, Div, Span, A, Button, Script, NotStr

from chat.layout import _head
from chat.components import left_pane, right_pane, signin_overlay
from charts import DASHBOARD, build_chart

# Each chart → the tab section(s) it belongs to.
SECTIONS = {
    "radar": "skills", "years": "skills stack", "heatmap": "skills",
    "treemap": "stack",
    "timeline": "career", "sankey": "career", "donut": "career", "adoption": "career stack",
}
TABS = [("all", "All"), ("skills", "Skills"), ("career", "Career"), ("stack", "Stack")]
_TAB_KEYS = {k for k, _ in TABS}
WIDE = {"timeline", "sankey", "adoption", "years"}  # charts that read better full-width

_HAMBURGER = ('<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
              'stroke-width="2"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/>'
              '<line x1="3" y1="18" x2="21" y2="18"/></svg>')
_BOOK = ('<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">'
         '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>')


def _charts_for(tab: str) -> list[str]:
    if tab == "all":
        return DASHBOARD
    return [n for n in DASHBOARD if tab in SECTIONS.get(n, "").split()]


def _center(tab: str):
    cards, scripts = [], []
    for name in _charts_for(tab):
        c = build_chart(name)
        if not c:
            continue
        div_id = f"viz-{name}"
        cards.append(Div(
            Div(c["title"], cls="visual-card-title"),
            Div(id=div_id, cls="visual-plot"),
            cls="visual-card" + (" wide" if name in WIDE else ""),
        ))
        fig = c["figure"]
        scripts.append(
            f"Plotly.newPlot('{div_id}', {json.dumps(fig['data'])}, "
            f"{json.dumps(fig['layout'])}, {{responsive:true, displayModeBar:false}});"
        )

    tabs = [A(label, href=f"/visuals?tab={key}",
              cls="viz-tab" + (" active" if key == tab else ""))
            for key, label in TABS]

    header = Div(
        Button(NotStr(_HAMBURGER), cls="mobile-menu-btn", onclick="toggleLeftPane()"),
        Div(*tabs, cls="viz-tabs"),
        Div(
            Button(NotStr(_BOOK), id="artifact-btn", onclick="toggleArtifactPane()",
                   cls="header-icon-btn", title="Research & Talks"),
            cls="chat-header-actions",
        ),
        cls="chat-header viz-header-bar",
    )
    center = Div(header, Div(*cards, cls="messages visuals-grid", id="viz-scroll"), cls="center-pane")
    return center, "\n".join(scripts)


def _page(tab: str, user_email=None, sessions=None):
    center, chart_js = _center(tab)
    body = Body(
        signin_overlay(),
        Div(id="left-overlay", cls="left-overlay", onclick="toggleLeftPane()"),
        left_pane(user_email=user_email, sessions=sessions, current_sid=""),
        center,
        Div(id="right-overlay", cls="right-overlay", onclick="toggleArtifactPane()"),
        right_pane(),
        Button(NotStr(_BOOK), Span("Research", cls="toggle-label"),
               id="right-pane-toggle-btn", cls="right-pane-toggle", onclick="toggleArtifactPane()"),
        Script(NotStr(chart_js)),
        Script(src="/static/chat.js?v=5"),
        cls="bg-white text-ink font-sans antialiased app",
        **({"data-signed-in": "1"} if user_email else {}),
    )
    return Html(_head("Visuals"), body)


def register_visuals_routes(rt):
    @rt("/visuals")
    def visuals(sess, tab: str = "all"):
        if tab not in _TAB_KEYS:
            tab = "all"
        from chat.routes import _ensure_user, _list_sessions
        uid, email = _ensure_user(sess)
        sessions = _list_sessions(uid) if uid else []
        return _page(tab, user_email=email, sessions=sessions)
