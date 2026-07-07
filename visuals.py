"""Static /visuals dashboard — a grid of every chart from charts.py."""

from __future__ import annotations

import json

from fasthtml.common import Html, Body, Div, H1, P, A, Script, NotStr

from chat.layout import _head
from charts import DASHBOARD, build_chart

# Charts that read better full-width across the grid.
WIDE = {"timeline", "sankey", "adoption", "years"}


def _visuals_page():
    cards, scripts = [], []
    for name in DASHBOARD:
        c = build_chart(name)
        if not c:
            continue
        div_id = f"viz-{name}"
        wide = " wide" if name in WIDE else ""
        cards.append(Div(
            Div(c["title"], cls="visual-card-title"),
            Div(id=div_id, cls="visual-plot"),
            cls=f"visual-card{wide}",
        ))
        fig = c["figure"]
        scripts.append(
            f"Plotly.newPlot('{div_id}', {json.dumps(fig['data'])}, "
            f"{json.dumps(fig['layout'])}, {{responsive:true, displayModeBar:false}});"
        )

    body = Body(
        Div(
            Div(
                A("← Back to chat", href="/app", cls="viz-back"),
                H1("Visuals", cls="viz-title"),
                P("A visual snapshot of Julian Kaljuvee's skills, stack and 15-year career.",
                  cls="viz-sub"),
                cls="viz-header",
            ),
            Div(*cards, cls="visuals-grid"),
            cls="viz-page",
        ),
        Script(NotStr("\n".join(scripts))),
        cls="bg-white text-ink font-sans antialiased",
    )
    return Html(_head("Visuals"), body)


def register_visuals_routes(rt):
    @rt("/visuals")
    def visuals():
        return _visuals_page()
