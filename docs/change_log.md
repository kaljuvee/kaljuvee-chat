# Change log

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
