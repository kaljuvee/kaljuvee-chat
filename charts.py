"""Plotly chart builders for Talk to Julian.

Single source of truth for every chart — used both inline in the chat (streamed
via SSE) and on the static /visuals dashboard. Each builder returns a plain
``{"data": [...], "layout": {...}}`` dict (``json.loads(fig.to_json())``) that the
client renders with ``Plotly.newPlot``.

Underlying data is curated from Julian's CV (skills matrix + role timeline).
"""

from __future__ import annotations

import json
from datetime import datetime

import plotly.graph_objects as go

INK = "#1A1A1A"
MUTED = "#6B7280"
GRID = "#ECECEC"
FONT = "Inter, system-ui, sans-serif"

# Blue → red scheme.
BLUE_DEEP = "#1E40AF"
BLUE = "#2563EB"
BLUE_MID = "#3B82F6"
BLUE_SOFT = "#60A5FA"
RED_SOFT = "#F87171"
RED = "#DC2626"


def _lerp_blue_red(frac: float) -> str:
    """0.0 → blue, 1.0 → red (through violet)."""
    frac = max(0.0, min(1.0, frac))
    b, r = (0x25, 0x63, 0xEB), (0xDC, 0x26, 0x26)
    c = tuple(round(b[i] + (r[i] - b[i]) * frac) for i in range(3))
    return f"rgb({c[0]},{c[1]},{c[2]})"


# Domain palette (kept — the dashboard's varied colours read well).
DOMAIN_COLORS = {
    "Investment Banking / Markets": "#2563EB",
    "Credit & Ratings": "#6366F1",
    "Retail / FMCG": "#F59E0B",
    "Fintech": "#0EA5E9",
    "Biotech": "#10B981",
    "Enterprise AI": "#8B5CF6",
    "Private Equity / CRE": "#EF4444",
}

# ── Curated data ─────────────────────────────────────────────────────────────

# Radar: overall emphasis/proficiency per domain (0–10), informed by years + depth.
SKILL_LEVELS = {
    "Data Engineering": 9,
    "ML / Data Science": 9,
    "GenAI / LLMs": 9,
    "Cloud": 8,
    "DevOps / MLOps": 8,
    "Programming": 8,
    "Visualisation": 7,
    "Quant / Risk": 8,
}

# Years of experience per technology (from the CV skills matrix).
TECH_YEARS = [
    ("RDBMS (SQL)", 10, "Data"),
    ("Python", 6, "Languages"),
    ("Java / Scala", 5, "Languages"),
    ("ML / Deep Learning", 5, "ML/AI"),
    ("AutoML (SageMaker/Vertex)", 5, "ML/AI"),
    ("Airflow", 5, "DevOps"),
    ("Terraform", 5, "DevOps"),
    ("Docker / Kubernetes", 5, "DevOps"),
    ("Snowflake/Databricks/BigQuery", 5, "Data"),
    ("Visualisation (Plotly/Tableau)", 5, "Viz"),
    ("Kafka / PySpark", 4, "Data"),
    ("Azure", 4, "Cloud"),
    ("AWS", 4, "Cloud"),
    ("GenAI / LLMs", 3, "ML/AI"),
    ("GCP", 3, "Cloud"),
]

CATEGORY_COLORS = {
    "Languages": "#2563EB", "ML/AI": "#8B5CF6", "Cloud": "#0EA5E9",
    "DevOps": "#F59E0B", "Data": "#10B981", "Viz": "#EC4899",
}

# Role timeline: (role, employer, start, end, domain). end None = present.
ROLES = [
    ("Quant Analyst", "UBS", "2010-01", "2014-06", "Investment Banking / Markets"),
    ("Data Scientist", "LSEG / LCH", "2014-07", "2015-11", "Investment Banking / Markets"),
    ("Quant Analyst", "HSBC / Std Chartered", "2015-11", "2018-06", "Investment Banking / Markets"),
    ("Data Scientist", "UBS", "2018-06", "2019-07", "Investment Banking / Markets"),
    ("Quant Researcher", "DBRS Morningstar", "2019-07", "2020-06", "Credit & Ratings"),
    ("Snr Data Scientist / ML", "Nandos", "2020-06", "2021-12", "Retail / FMCG"),
    ("Snr Data Scientist", "IKEA", "2022-01", "2022-10", "Retail / FMCG"),
    ("Head of Data Eng", "Worldremit", "2022-10", "2023-06", "Fintech"),
    ("Head of AI", "Vaxart", "2023-06", "2024-03", "Biotech"),
    ("Gen AI Engineer", "Microsoft", "2024-04", "2025-09", "Enterprise AI"),
    ("AI Engineer", "Indurent (Blackstone)", "2025-09", None, "Private Equity / CRE"),
]

# Sankey: career era → sector → skill area.
SANKEY_ERAS = ["2010–2019 · Quant/Finance", "2020–2023 · Data & ML", "2024–now · GenAI"]
SANKEY_SECTORS = ["Banking & Markets", "Credit / Ratings", "Retail / FMCG",
                  "Fintech", "Biotech", "Enterprise AI", "Private Equity"]
SANKEY_SKILLS = ["Quant / Risk", "Data Engineering", "ML / Forecasting",
                 "GenAI / LLMs", "MLOps", "Knowledge Graphs"]
# (source_label, target_label, value)
SANKEY_LINKS = [
    ("2010–2019 · Quant/Finance", "Banking & Markets", 8),
    ("2010–2019 · Quant/Finance", "Credit / Ratings", 2),
    ("2020–2023 · Data & ML", "Retail / FMCG", 3),
    ("2020–2023 · Data & ML", "Fintech", 2),
    ("2020–2023 · Data & ML", "Biotech", 2),
    ("2024–now · GenAI", "Enterprise AI", 3),
    ("2024–now · GenAI", "Private Equity", 2),
    ("Banking & Markets", "Quant / Risk", 6),
    ("Banking & Markets", "Data Engineering", 2),
    ("Credit / Ratings", "ML / Forecasting", 2),
    ("Retail / FMCG", "Data Engineering", 2),
    ("Retail / FMCG", "ML / Forecasting", 2),
    ("Fintech", "Data Engineering", 2),
    ("Biotech", "GenAI / LLMs", 1),
    ("Biotech", "ML / Forecasting", 1),
    ("Enterprise AI", "GenAI / LLMs", 3),
    ("Enterprise AI", "MLOps", 1),
    ("Private Equity", "GenAI / LLMs", 1),
    ("Private Equity", "Knowledge Graphs", 1),
]

# Tech-adoption: first year Julian used each major tech.
TECH_ADOPTION = [
    ("SQL / RDBMS", 2010), ("Python", 2014), ("Scikit-learn", 2015),
    ("AWS", 2016), ("Spark / Databricks", 2018), ("Airflow / DBT", 2019),
    ("GCP / BigQuery", 2020), ("Kubernetes", 2020), ("Terraform", 2021),
    ("Snowflake", 2021), ("LLMs / LangChain", 2023), ("Azure AI", 2024),
    ("LangGraph / Agents", 2024), ("GraphRAG / Neo4j", 2025),
]

# Skill × era intensity heatmap (0–3).
HEATMAP_ERAS = ["2010–2015", "2016–2019", "2020–2023", "2024–now"]
HEATMAP_SKILLS = ["Quant / Risk", "Data Engineering", "ML / Forecasting",
                  "Cloud / DevOps", "GenAI / LLMs", "Leadership"]
HEATMAP_Z = [
    [3, 3, 1, 0],  # Quant / Risk
    [1, 2, 3, 2],  # Data Engineering
    [1, 2, 3, 2],  # ML / Forecasting
    [1, 2, 3, 3],  # Cloud / DevOps
    [0, 0, 1, 3],  # GenAI / LLMs
    [0, 1, 2, 3],  # Leadership
]


# ── Shared layout ────────────────────────────────────────────────────────────

def _layout(title: str = "", height: int = 340, **extra) -> dict:
    lay = dict(
        title=dict(text=title, font=dict(size=14, color=INK, family=FONT), x=0.5, xanchor="center"),
        paper_bgcolor="white", plot_bgcolor="white",
        font=dict(family=FONT, color=INK, size=12),
        margin=dict(l=40, r=20, t=40 if title else 16, b=30),
        height=height, autosize=True,
    )
    lay.update(extra)
    return lay


def _fig(fig: go.Figure) -> dict:
    return json.loads(fig.to_json())


def _months(start: str, end: str | None) -> tuple[datetime, datetime]:
    s = datetime.strptime(start, "%Y-%m")
    e = datetime.now() if not end else datetime.strptime(end, "%Y-%m")
    return s, e


# ── Builders ─────────────────────────────────────────────────────────────────

def skill_radar() -> dict:
    axes = list(SKILL_LEVELS.keys())
    vals = list(SKILL_LEVELS.values())
    fig = go.Figure(go.Scatterpolar(
        r=vals + [vals[0]], theta=axes + [axes[0]],
        fill="toself", mode="lines+markers",
        line=dict(color=BLUE, width=2.5), marker=dict(color=RED, size=6),
        fillcolor="rgba(37,99,235,0.14)", hovertemplate="%{theta}: %{r}/10<extra></extra>",
    ))
    fig.update_layout(_layout("Skill emphasis", height=360, showlegend=False,
        polar=dict(bgcolor="white",
                   radialaxis=dict(range=[0, 10], tickvals=[2, 4, 6, 8, 10],
                                   gridcolor=GRID, tickfont=dict(size=9, color=MUTED)),
                   angularaxis=dict(gridcolor=GRID, tickfont=dict(size=10, color=INK)))))
    return _fig(fig)


def years_bar() -> dict:
    data = sorted(TECH_YEARS, key=lambda x: x[1])
    techs = [t[0] for t in data]
    yrs = [t[1] for t in data]
    colors = [CATEGORY_COLORS.get(t[2], INK) for t in data]
    fig = go.Figure()
    # lollipop stems
    for tch, y, c in zip(techs, yrs, colors):
        fig.add_trace(go.Scatter(x=[0, y], y=[tch, tch], mode="lines",
                                 line=dict(color=c, width=2), hoverinfo="skip", showlegend=False))
    fig.add_trace(go.Scatter(x=yrs, y=techs, mode="markers+text",
                             marker=dict(size=12, color=colors),
                             text=[f"{y}+" if y >= 10 else str(y) for y in yrs],
                             textposition="middle right", textfont=dict(size=10, color=INK),
                             hovertemplate="%{y}: %{x} yrs<extra></extra>", showlegend=False))
    fig.update_layout(_layout("Years of experience by technology", height=420,
        xaxis=dict(range=[0, 12], gridcolor=GRID, zeroline=False, title="Years"),
        yaxis=dict(gridcolor="white"), margin=dict(l=180, r=30, t=40, b=30)))
    return _fig(fig)


def career_timeline() -> dict:
    fig = go.Figure()
    seen = set()
    for role, emp, start, end, domain in ROLES:
        s, e = _months(start, end)
        dur_ms = (e - s).total_seconds() * 1000
        color = DOMAIN_COLORS.get(domain, INK)
        fig.add_trace(go.Bar(
            y=[f"{emp}"], x=[dur_ms], base=[s], orientation="h",
            marker=dict(color=color, line=dict(width=0)),
            name=domain, legendgroup=domain, showlegend=domain not in seen,
            hovertemplate=f"<b>{emp}</b><br>{role}<br>{start} → {end or 'present'}<extra></extra>",
        ))
        seen.add(domain)
    fig.update_layout(_layout("Career timeline", height=460, barmode="overlay",
        xaxis=dict(type="date", gridcolor=GRID, tickformat="%Y"),
        yaxis=dict(autorange="reversed", gridcolor="white"),
        legend=dict(orientation="h", y=-0.12, font=dict(size=9)),
        margin=dict(l=150, r=20, t=40, b=60)))
    return _fig(fig)


def skills_sankey() -> dict:
    labels = SANKEY_ERAS + SANKEY_SECTORS + SANKEY_SKILLS
    idx = {l: i for i, l in enumerate(labels)}
    node_colors = (["#111827"] * len(SANKEY_ERAS)
                   + ["#6366F1"] * len(SANKEY_SECTORS)
                   + ["#10B981"] * len(SANKEY_SKILLS))
    src = [idx[a] for a, b, v in SANKEY_LINKS]
    tgt = [idx[b] for a, b, v in SANKEY_LINKS]
    val = [v for a, b, v in SANKEY_LINKS]
    fig = go.Figure(go.Sankey(
        arrangement="snap",
        node=dict(label=labels, color=node_colors, pad=14, thickness=14,
                  line=dict(color="white", width=0.5),
                  hovertemplate="%{label}<extra></extra>"),
        link=dict(source=src, target=tgt, value=val, color="rgba(99,102,241,0.18)",
                  hovertemplate="%{source.label} → %{target.label}<extra></extra>"),
    ))
    fig.update_layout(_layout("Experience flow: era → sector → skills", height=440,
                              font=dict(size=10, color=INK, family=FONT)))
    return _fig(fig)


def tech_treemap() -> dict:
    cats, techs, parents, vals, colors = [], [], [], [], []
    by_cat: dict[str, int] = {}
    for tch, y, cat in TECH_YEARS:
        by_cat[cat] = by_cat.get(cat, 0) + y
    labels = list(by_cat.keys())
    parents_top = [""] * len(labels)
    values_top = [by_cat[c] for c in labels]
    colours_top = [CATEGORY_COLORS.get(c, INK) for c in labels]
    for tch, y, cat in TECH_YEARS:
        labels.append(tch); parents_top.append(cat); values_top.append(y)
        colours_top.append(CATEGORY_COLORS.get(cat, INK))
    fig = go.Figure(go.Treemap(
        labels=labels, parents=parents_top, values=values_top,
        marker=dict(colors=colours_top, line=dict(width=1, color="white")),
        textfont=dict(family=FONT, size=11), branchvalues="total",
        hovertemplate="%{label}<br>%{value} yrs<extra></extra>",
    ))
    fig.update_layout(_layout("Tech stack by category", height=400))
    return _fig(fig)


def domain_donut() -> dict:
    share: dict[str, float] = {}
    for role, emp, start, end, domain in ROLES:
        s, e = _months(start, end)
        share[domain] = share.get(domain, 0) + (e - s).days / 365.25
    labels = list(share.keys())
    fig = go.Figure(go.Pie(
        labels=labels, values=[round(share[d], 1) for d in labels], hole=0.55,
        marker=dict(colors=[DOMAIN_COLORS.get(d, INK) for d in labels],
                    line=dict(color="white", width=2)),
        textinfo="label+percent", textfont=dict(size=10),
        hovertemplate="%{label}: %{value} yrs<extra></extra>",
    ))
    fig.update_layout(_layout("Career years by domain", height=400,
                              showlegend=False))
    return _fig(fig)


def tech_adoption() -> dict:
    data = sorted(TECH_ADOPTION, key=lambda x: x[1])
    years = [d[1] for d in data]
    names = [d[0] for d in data]
    fig = go.Figure(go.Scatter(
        x=years, y=list(range(len(names))), mode="markers+text",
        marker=dict(size=11, color=INK), text=names, textposition="middle right",
        textfont=dict(size=10, color=INK), hovertemplate="%{text}: %{x}<extra></extra>",
    ))
    fig.update_layout(_layout("When Julian first adopted each technology", height=460,
        xaxis=dict(range=[2009, 2028], gridcolor=GRID, dtick=2, title="Year first used"),
        yaxis=dict(visible=False), margin=dict(l=20, r=160, t=40, b=30)))
    return _fig(fig)


def skill_heatmap() -> dict:
    fig = go.Figure(go.Heatmap(
        z=HEATMAP_Z, x=HEATMAP_ERAS, y=HEATMAP_SKILLS,
        colorscale=[[0, "#F3F4F6"], [0.5, "#A5B4FC"], [1, "#4338CA"]],
        showscale=False, xgap=3, ygap=3,
        hovertemplate="%{y} · %{x}: intensity %{z}/3<extra></extra>",
    ))
    fig.update_layout(_layout("Skill intensity across career phases", height=360,
        xaxis=dict(side="top", tickfont=dict(size=10)),
        yaxis=dict(autorange="reversed", tickfont=dict(size=10)),
        margin=dict(l=130, r=20, t=50, b=20)))
    return _fig(fig)


# ── Registry + intent detection ──────────────────────────────────────────────

CHARTS = {
    "radar": ("Skill emphasis", skill_radar),
    "years": ("Years by technology", years_bar),
    "timeline": ("Career timeline", career_timeline),
    "sankey": ("Experience flow", skills_sankey),
    "treemap": ("Tech stack by category", tech_treemap),
    "donut": ("Career years by domain", domain_donut),
    "adoption": ("Tech adoption over time", tech_adoption),
    "heatmap": ("Skill intensity by phase", skill_heatmap),
}

# Charts surfaced on the static /visuals dashboard, in order.
DASHBOARD = ["radar", "timeline", "sankey", "years", "treemap", "donut", "adoption", "heatmap"]


def build_chart(name: str) -> dict | None:
    entry = CHARTS.get(name)
    if not entry:
        return None
    title, builder = entry
    return {"name": name, "title": title, "figure": builder()}


import re

_PATTERNS = [
    ("sankey", r"\bsankey\b|evolv|how (?:did|have).*(?:change|evolve)|over time|progress|journey|trajector"),
    ("timeline", r"\btimeline\b|\bgantt\b|career|work history|roles over|when did he work|employment"),
    ("radar", r"\bradar\b|skill (?:emphasis|distribution|profile|set|map)|strengths|expertise|how strong"),
    ("years", r"years of experience|how (?:many|long).*(?:years|experience)|experience (?:by|per)|\bbar chart\b"),
    ("treemap", r"\btreemap\b|tech stack|technolog(?:y|ies) (?:by|grouped)"),
    ("donut", r"\bdonut\b|\bpie\b|by (?:domain|sector|industry)|domain share"),
    ("adoption", r"\badoption\b|first use|when did he (?:start|adopt)"),
    ("heatmap", r"\bheat ?map\b|intensity"),
]

_GENERIC_SKILLS = re.compile(r"\bskills?\b|tech stack|technolog|proficien|capabilit", re.IGNORECASE)
_GENERIC_EXP = re.compile(r"\bexperience\b|\bcareer\b|background|history", re.IGNORECASE)


def detect_charts(message: str) -> list[str]:
    """Pick chart(s) to stream for a message. Explicit chart words win; otherwise
    skill questions → radar, experience questions → timeline."""
    m = (message or "").lower()
    hits = [name for name, pat in _PATTERNS if re.search(pat, m)]
    if hits:
        # de-dup, keep order, cap at 2 so we don't flood the bubble
        out = []
        for h in hits:
            if h not in out:
                out.append(h)
        return out[:2]
    if _GENERIC_SKILLS.search(m):
        return ["radar"]
    if _GENERIC_EXP.search(m):
        return ["timeline"]
    return []
