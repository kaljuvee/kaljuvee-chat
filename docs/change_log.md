# Change log

## 1.2.0 — 2026-11-12

- Paper PDF added to the repo (`research/papers/temporal-leakage-financial-news-nlp.pdf`, arXiv
  2608.17223 v2) and served from the site at `/research/<slug>.pdf` (application/pdf).
- Left menu: new **Research** section listing each paper with *Download PDF* (our copy),
  *arXiv* and *Markdown* (LLM-readable `/research/<slug>.md`) links; the title opens the paper page.
- `/llms.txt` lists the research markdown, PDF and arXiv links for LLM crawlers.
- Chat: questions about Julian's research / publications / papers ("What is Julian's research
  about?", "What has Julian Kaljuvee published?", "his papers", "your research") route to the
  paper retrieval; context and system prompt state he is a co-author (last author of 8) and
  carry page, PDF, markdown and arXiv links. Numbers are asked for in plain text, not LaTeX.
- Explicit `/llms.txt` and `/research/*` routes are moved ahead of FastHTML's static catch-all
  (which otherwise swallowed `.pdf` / `.txt`). Sample question "What is Julian's research about?".
- Markdown version re-checked against arXiv: v2 is still the latest version.

## 1.1.2 — 2026-11-11

- RAG citation instruction now asks for the paper's full title (the model sometimes printed a
  literal "*Title*" placeholder).

## 1.1.1 — 2026-11-11

- CI: the "Deploy to Coolify" workflow now POSTs to the new Coolify deploy endpoint
  (coolify.predictivelabs.ai app `hmc8zfjzyzpsvpvl8qpvpaul`); repo secrets
  `COOLIFY_WEBHOOK_URL` / `COOLIFY_TOKEN` were updated from the expired coolify.finespresso.org.

## 1.1.0 — 2026-11-11

- **Research section.** New `/research` page (left-nav "Research" link) and `/research/<slug>`
  paper pages rendered from markdown with KaTeX math, a table of contents, and links to the
  arXiv original / PDF / raw `.md`. First paper: *Temporal Leakage in Financial News NLP: A
  Multi-Architecture Audit with a Regime-Specific M&A Signal* (arXiv:2608.17223, Xue, Guesmi,
  Feng, Gong, Sundram, Pang, Wang, Kaljuvee), converted from the arXiv HTML v2 into
  `research/papers/temporal-leakage-financial-news-nlp.md`.
- **Simple RAG.** `research/` splits each paper into section chunks and ranks them with a
  pure-Python BM25. When a question is about a paper, the top chunks (plus title, authors and
  abstract) are prepended to that turn's message with a citation instruction. A short paper
  summary is always in the system prompt.
- Papers section in the right "Research and Talks" pane; new sample question; `?q=` prefill in
  the chat input; tests for the paper store and retrieval.
- Added `docs/query_gate.md` (previously uncommitted on the ThinkPad).
- Redeployed on Coolify (coolify.predictivelabs.ai, 187.124.131.91) after the old host
  (coolify.finespresso.org, 72.62.88.13) expired. Chat history from the old SQLite volume was
  not recoverable; a fresh SQLite volume was created.
