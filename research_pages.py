"""/research — Julian's research papers, rendered from markdown in research/papers/.

/research            list of papers (title, authors, abstract, links)
/research/<slug>     full markdown version of one paper (rendered client-side with
                     marked + KaTeX, same 3-pane app shell as /visuals)
/research/<slug>.md  the raw markdown
"""

from __future__ import annotations

import json

from fasthtml.common import (Html, Body, Div, Span, A, Button, Script, NotStr, H1, H2, P, Link)
from starlette.responses import PlainTextResponse, HTMLResponse, FileResponse

from chat.layout import _head
from chat.components import left_pane, right_pane, signin_overlay
import research

_HAMBURGER = ('<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
              'stroke-width="2"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/>'
              '<line x1="3" y1="18" x2="21" y2="18"/></svg>')
_BOOK = ('<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">'
         '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>')

KATEX = "https://cdn.jsdelivr.net/npm/katex@0.16.11/dist"


def _header(title: str):
    return Div(
        Button(NotStr(_HAMBURGER), cls="mobile-menu-btn", onclick="toggleLeftPane()"),
        Div(A("Research", href="/research", cls="viz-tab active"), Span(title, cls="research-crumb"),
            cls="viz-tabs"),
        Div(Button(NotStr(_BOOK), id="artifact-btn", onclick="toggleArtifactPane()",
                   cls="header-icon-btn", title="Research & Talks"), cls="chat-header-actions"),
        cls="chat-header viz-header-bar",
    )


def _ask_href(p) -> str:
    from urllib.parse import quote_plus
    return "/app?q=" + quote_plus(f"What are the main findings of the paper \"{p.title.split(':')[0]}\"?")


def _paper_card(p: research.Paper):
    return Div(
        A(p.title, href=f"/research/{p.slug}", cls="research-card-title"),
        Div(p.authors, cls="research-authors"),
        Div(Span(f"arXiv:{p.arxiv}", cls="article-chip"), Span(p.date, cls="article-date"),
            Span(p.julian_role, cls="article-date") if p.julian_role else "",
            cls="article-meta"),
        P(p.abstract, cls="research-abstract"),
        Div(A("Read the markdown version", href=f"/research/{p.slug}", cls="research-btn primary"),
            A("Download PDF", href=f"/research/{p.slug}.pdf", download="", cls="research-btn"),
            A("arXiv", href=p.url, target="_blank", rel="noopener", cls="research-btn"),
            A("Markdown (LLM-readable)", href=f"/research/{p.slug}.md", cls="research-btn"),
            A("Ask about it", href=_ask_href(p), cls="research-btn"),
            cls="research-actions"),
        cls="research-card",
    )


def _shell(title: str, center, user_email=None, sessions=None, extra_head=(), scripts=()):
    head = _head(title)
    head.children = tuple(head.children) + tuple(extra_head)
    body = Body(
        signin_overlay(),
        Div(id="left-overlay", cls="left-overlay", onclick="toggleLeftPane()"),
        left_pane(user_email=user_email, sessions=sessions, current_sid=""),
        center,
        Div(id="right-overlay", cls="right-overlay", onclick="toggleArtifactPane()"),
        right_pane(),
        Button(NotStr(_BOOK), Span("Research", cls="toggle-label"),
               id="right-pane-toggle-btn", cls="right-pane-toggle", onclick="toggleArtifactPane()"),
        *scripts,
        Script(src="/static/chat.js?v=6"),
        cls="bg-white text-ink font-sans antialiased app",
        **({"data-signed-in": "1"} if user_email else {}),
    )
    return Html(head, body)


def _user(sess):
    from chat.routes import _ensure_user, _list_sessions
    uid, email = _ensure_user(sess)
    return email, (_list_sessions(uid) if uid else [])


RENDER_JS = """
(function(){
  const src = JSON.parse(document.getElementById('paper-md').textContent);
  // Protect $…$ / $$…$$ math from the markdown parser, then render with KaTeX.
  const maths = [];
  const stash = s => { maths.push(s); return '@@MATH' + (maths.length-1) + '@@'; };
  let t = src.replace(/\\$\\$([\\s\\S]+?)\\$\\$/g, m => stash(m)).replace(/\\$([^$\\n]+?)\\$/g, m => stash(m));
  let html = marked.parse(t);
  html = html.replace(/@@MATH(\\d+)@@/g, (_, i) => {
    const m = maths[+i]; const disp = m.startsWith('$$');
    const tex = disp ? m.slice(2,-2) : m.slice(1,-1);
    try { return katex.renderToString(tex, {displayMode: disp, throwOnError: false}); }
    catch(e) { return m; }
  });
  const el = document.getElementById('paper-body'); el.innerHTML = html;
  // Table of contents from h2s.
  const toc = document.getElementById('paper-toc');
  el.querySelectorAll('h2').forEach((h, i) => {
    h.id = 'sec-' + i;
    const a = document.createElement('a'); a.href = '#sec-' + i; a.textContent = h.textContent;
    toc.appendChild(a);
  });
})();
"""


def register_research_routes(rt):
    @rt("/research")
    def research_index(sess):
        email, sessions = _user(sess)
        papers = research.load_papers()
        center = Div(
            _header("Papers"),
            Div(
                Div(H1("Research", cls="research-h1"),
                    P("Papers Julian has co-authored. Each paper has a clean markdown "
                      "version here, and the chat assistant can answer questions about it, citing the paper.",
                      cls="research-lead"),
                    *[_paper_card(p) for p in papers],
                    cls="research-wrap"),
                cls="messages research-scroll",
            ),
            cls="center-pane",
        )
        extra = (Link(rel="stylesheet", href=f"{KATEX}/katex.min.css"),
                 Script(src=f"{KATEX}/katex.min.js"),
                 Script(src=f"{KATEX}/contrib/auto-render.min.js"))
        js = Script(NotStr("document.querySelectorAll('.research-abstract').forEach(el => "
                           "renderMathInElement(el, {delimiters:[{left:'$',right:'$',display:false}], throwOnError:false}));"))
        return _shell("Research", center, email, sessions, extra, (js,))

    @rt("/research/{slug}")
    def research_paper(sess, slug: str):
        if slug.endswith(".pdf"):
            p = research.by_slug(slug[:-4])
            if not p or not p.has_local_pdf:
                return PlainTextResponse("not found", status_code=404)
            return FileResponse(p.pdf_path, media_type="application/pdf",
                                filename=f"{p.slug}-arXiv-{p.arxiv}.pdf",
                                content_disposition_type="inline")
        if slug.endswith(".md"):
            p = research.by_slug(slug[:-3])
            if not p:
                return PlainTextResponse("not found", status_code=404)
            raw = (research.PAPERS_DIR / f"{p.slug}.md").read_text(encoding="utf-8")
            return PlainTextResponse(raw, media_type="text/markdown; charset=utf-8")
        p = research.by_slug(slug)
        if not p:
            return HTMLResponse("<h2>Paper not found</h2><p><a href='/research'>Back to Research</a></p>",
                                status_code=404)
        email, sessions = _user(sess)
        body_md = p.body.split("\n## Abstract", 1)
        body_md = "## Abstract" + body_md[1] if len(body_md) == 2 else p.body
        center = Div(
            _header(p.title.split(":")[0]),
            Div(
                Div(
                    H1(p.title, cls="research-h1"),
                    Div(p.authors, cls="research-authors"),
                    Div(Span(f"arXiv:{p.arxiv}", cls="article-chip"),
                        Span(f"submitted {p.date}", cls="article-date"), cls="article-meta"),
                    Div(A("arXiv original", href=p.url, target="_blank", rel="noopener", cls="research-btn primary"),
                        A("Download PDF", href=f"/research/{p.slug}.pdf", download="", cls="research-btn"),
                        A("Markdown (LLM-readable)", href=f"/research/{p.slug}.md", cls="research-btn"),
                        A("Ask about this paper", href=_ask_href(p), cls="research-btn"),
                        cls="research-actions"),
                    P(NotStr("Markdown version converted from the arXiv HTML for reading and retrieval. "
                             "Figures are omitted. The <a href='" + p.url + "' target='_blank' rel='noopener'>"
                             "arXiv version</a> is authoritative; all credit to the authors."),
                      cls="research-note"),
                    Div(Span("Contents", cls="research-toc-title"), id="paper-toc", cls="research-toc"),
                    Div(id="paper-body", cls="paper-body"),
                    cls="research-wrap"),
                cls="messages research-scroll",
            ),
            cls="center-pane",
        )
        extra = (Link(rel="stylesheet", href=f"{KATEX}/katex.min.css"),
                 Script(src=f"{KATEX}/katex.min.js"))
        scripts = (Script(json.dumps(body_md), id="paper-md", type="application/json"),
                   Script(NotStr(RENDER_JS)))
        return _shell(p.title.split(":")[0], center, email, sessions, extra, scripts)


def llms_txt() -> str:
    base = "https://kaljuvee.chat"
    out = ["# kaljuvee.chat — Talk to Julian", "",
           "> AI assistant about Julian Kaljuvee's career, projects and research. The research papers below "
           "are available as clean markdown for LLMs.", "",
           "## Research papers (markdown)", ""]
    for p in research.load_papers():
        role = f" {p.julian_role}." if p.julian_role else ""
        out.append(f"- [{p.title}]({base}/research/{p.slug}.md): arXiv:{p.arxiv}, {p.date}. "
                   f"Authors: {p.authors}.{role} PDF: {base}/research/{p.slug}.pdf · arXiv: {p.url}")
    out += ["", "## Pages", "",
            f"- [Research]({base}/research): list of papers",
            f"- [Chat]({base}/app): ask questions about Julian's CV and research",
            f"- [CV (PDF)]({base}/cv/pdf)", ""]
    return "\n".join(out)


def register_llms_txt(rt):
    @rt("/llms.txt")
    def _llms():
        return PlainTextResponse(llms_txt(), media_type="text/plain; charset=utf-8")
