"""Research papers: markdown store + lightweight BM25 retrieval (simple RAG).

Papers live as markdown files with a small YAML front-matter block in
``research/papers/<slug>.md``. At startup they are split into section-sized
chunks; for each chat question we score the chunks with BM25 (pure Python, no
extra dependencies) and, when the question is about a paper, the top chunks are
injected into the LLM context with a citation instruction.

Add a paper: drop another ``<slug>.md`` into ``research/papers/`` with the same
front-matter keys (title, slug, authors, arxiv, date, url, pdf). No code change.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import yaml

PAPERS_DIR = Path(__file__).resolve().parent / "papers"

_STOP = set("""
a an and are as at be been but by can could did do does for from had has have he her his how i if in
into is it its julian julian's kaljuvee me my of on or our she so than that the their them then there
these they this those to was we were what when where which who why will with would you your about
tell explain describe give show please paper papers study research
""".split())

# Words that signal the visitor is asking about research/papers in general.
_RESEARCH_HINTS = {"paper", "papers", "arxiv", "research", "publication", "publications",
                   "published", "preprint", "study", "co-authored", "coauthored", "authors"}


@dataclass
class Paper:
    slug: str
    title: str
    authors: str
    arxiv: str
    date: str
    url: str
    pdf: str
    body: str            # markdown without front-matter
    abstract: str = ""
    meta: dict = field(default_factory=dict)


@dataclass
class Chunk:
    paper: Paper
    section: str
    text: str
    tokens: list[str]


def _tokenize(s: str) -> list[str]:
    s = s.lower().replace("m&a", "manda")
    return [t for t in re.findall(r"[a-z0-9][a-z0-9\-]*", s) if t not in _STOP and len(t) > 1]


def _split_front_matter(raw: str) -> tuple[dict, str]:
    if raw.startswith("---"):
        _, fm, body = raw.split("---", 2)
        return (yaml.safe_load(fm) or {}), body.lstrip()
    return {}, raw


@lru_cache(maxsize=1)
def load_papers() -> tuple[Paper, ...]:
    papers = []
    for p in sorted(PAPERS_DIR.glob("*.md")):
        meta, body = _split_front_matter(p.read_text(encoding="utf-8"))
        m = re.search(r"^## Abstract\s*\n+(.+?)(?=\n## )", body, re.S | re.M)
        papers.append(Paper(
            slug=str(meta.get("slug") or p.stem), title=str(meta.get("title", p.stem)),
            authors=str(meta.get("authors", "")), arxiv=str(meta.get("arxiv", "")),
            date=str(meta.get("date", "")), url=str(meta.get("url", "")),
            pdf=str(meta.get("pdf", "")), body=body,
            abstract=m.group(1).strip() if m else "", meta=meta,
        ))
    return tuple(papers)


def by_slug(slug: str) -> Paper | None:
    return next((p for p in load_papers() if p.slug == slug), None)


def _chunk_paper(paper: Paper, max_chars: int = 1800) -> list[Chunk]:
    chunks: list[Chunk] = []
    heading = "Front matter"
    buf: list[str] = []

    def flush():
        text = "\n\n".join(buf).strip()
        buf.clear()
        if not text:
            return
        # Split long sections on paragraph boundaries.
        parts, cur = [], ""
        for para in text.split("\n\n"):
            if cur and len(cur) + len(para) > max_chars:
                parts.append(cur)
                cur = ""
            cur = (cur + "\n\n" + para).strip()
        if cur:
            parts.append(cur)
        for part in parts:
            chunks.append(Chunk(paper, heading, part, _tokenize(heading + " " + part)))

    in_refs = False
    for block in paper.body.split("\n\n"):
        b = block.strip()
        if re.match(r"^#{1,4} ", b):
            flush()
            heading = b.lstrip("#").strip()
            in_refs = heading.lower() == "references"
            continue
        if in_refs:  # references are rendered on the page but not retrieved
            continue
        buf.append(b)
    flush()
    return chunks


@lru_cache(maxsize=1)
def _index():
    chunks = [c for p in load_papers() for c in _chunk_paper(p)]
    df = Counter()
    for c in chunks:
        df.update(set(c.tokens))
    n = max(len(chunks), 1)
    avgdl = sum(len(c.tokens) for c in chunks) / n
    idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}
    return chunks, idf, avgdl


def search(query: str, k: int = 5, k1: float = 1.4, b: float = 0.75) -> list[tuple[float, Chunk]]:
    chunks, idf, avgdl = _index()
    q = _tokenize(query)
    if not q or not chunks:
        return []
    scored = []
    for c in chunks:
        tf = Counter(c.tokens)
        dl = len(c.tokens) or 1
        s = 0.0
        for t in q:
            f = tf.get(t)
            if f:
                s += idf.get(t, 0) * f * (k1 + 1) / (f + k1 * (1 - b + b * dl / avgdl))
        if s > 0:
            scored.append((s, c))
    scored.sort(key=lambda x: -x[0])
    return scored[:k]


def _title_terms(p: Paper) -> set[str]:
    return set(_tokenize(p.title)) | {p.arxiv, "leakage", "finbert", "fnspid", "lookahead",
                                       "look-ahead", "chronological", "manda"}


def is_research_query(query: str, history: str = "") -> bool:
    """True when the question (or the recent conversation) is about a paper."""
    toks = set(_tokenize(query)) | set(re.findall(r"[a-z\-]+", query.lower()))
    if toks & _RESEARCH_HINTS:
        return True
    for p in load_papers():
        if len(toks & _title_terms(p)) >= 1:
            return True
    # Follow-ups ("what was the MCC?") after a research turn.
    if history:
        htoks = set(_tokenize(history))
        if any(len(htoks & _title_terms(p)) >= 2 for p in load_papers()):
            hits = search(query, k=1)
            return bool(hits and hits[0][0] > 4.0)
    return False


def build_context(query: str, history: str = "", k: int = 5) -> str | None:
    """Return a context block of retrieved paper chunks, or None if not relevant."""
    if not load_papers() or not is_research_query(query, history):
        return None
    hits = search(query + " " + history[-400:], k=k)
    if not hits or hits[0][0] < 5.0:
        # Vague question ("tell me about his paper") → give the key findings + conclusion.
        chunks, _, _ = _index()
        core = [c for c in chunks if c.section.startswith(("1.3", "9 Conclusion"))]
        seen = {id(c) for _, c in hits}
        hits = hits + [(0.0, c) for c in core if id(c) not in seen]
        hits = hits[:k + 2]
    papers = {c.paper.slug: c.paper for _, c in hits} or {p.slug: p for p in load_papers()}
    lines = ["# Retrieved research context (from Julian's papers on kaljuvee.chat/research)",
             "Answer using ONLY these excerpts plus the paper metadata. Quote numbers exactly. "
             "Cite the paper as: *Title* (arXiv:ID) and link https://kaljuvee.chat/research/<slug> "
             "and the arXiv URL. If a paper detail isn't in the excerpts, say so rather than guess; "
             "for non-paper parts of the question, answer from the CV as usual.", ""]
    for p in papers.values():
        lines += [f"## Paper: {p.title}", f"- Authors: {p.authors}",
                  f"- arXiv: {p.arxiv} ({p.url}), submitted {p.date}",
                  f"- On this site: https://kaljuvee.chat/research/{p.slug}",
                  f"- Abstract: {p.abstract}", ""]
    for i, (score, c) in enumerate(hits, 1):
        lines += [f"### Excerpt {i} — {c.paper.title.split(':')[0]} · section \"{c.section}\"", c.text, ""]
    return "\n".join(lines)


def grounding_markdown() -> str:
    """Short always-on summary of the papers for the system prompt."""
    papers = load_papers()
    if not papers:
        return ""
    out = ["# Research papers (Julian is a co-author)",
           "Full markdown versions are on https://kaljuvee.chat/research. When a question is about "
           "a paper, retrieved excerpts are added to the user's message — rely on them for details."]
    for p in papers:
        out += [f"\n## {p.title}", f"- Authors: {p.authors}", f"- arXiv:{p.arxiv} · {p.url} · {p.date}",
                f"- Page: https://kaljuvee.chat/research/{p.slug}", f"- Abstract: {p.abstract}"]
    return "\n".join(out)
