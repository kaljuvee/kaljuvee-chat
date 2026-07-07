# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

**Ask Julian** (kaljuvee.chat) — a personal AI chatbot that answers questions about
Julian Kaljuvee's career, grounded in his CV. Built with **FastHTML** (server-rendered
hypermedia + SSE), a single **LangGraph** agent, and **SQLite**. It was repurposed from a car
app (`carhero`); if you find stray car-domain references, they are vestigial — this is a CV bot.

Deep references: **`docs/architecture_readme.md`** (Mermaid diagrams) and **`SKILLS.md`**
(ops: run, test, eval, deploy). Read those before large changes.

## Commands

The venv is **uv-managed** — use `uv pip`, not bare `pip` (bare `pip` hits PEP-668 / the wrong interpreter):

```bash
source .venv/bin/activate
uv pip install -r requirements.txt          # app deps
uv pip install -r requirements-eval.txt     # deepeval, for evals only (kept out of the image)
python main.py                              # serves on PORT (default 5011); SQLite auto-created

pytest -q                                   # smoke tests
pytest tests/test_smoke.py::test_router_single_agent   # a single test

python -m evals.run_eval                    # full eval suite → eval/eval-results.json + evals/EVAL_REPORT.md
python -m evals.run_eval --category technical --limit 5
```

`main.py` calls `serve()` at import time, so you cannot `import main` — exercise routes by
running the server, or import the sub-modules (`chat.routes`, `agents.base`, etc.) directly.

## Architecture (the parts that span files)

**Grounding, not RAG.** The CV is small, so the whole thing is injected into the system prompt.
`agents/base._load_system_prompt(slug)` concatenates three files: `prompts/system/{slug}.md`
(persona) + `prompts/shared/cv.md` (verbatim CV) + `prompts/shared/career_facts.md` (company,
projects-by-sector, links). **The persona filename must equal the agent slug** (`ask_julian.md`).
To change what the bot knows, edit the markdown — no code change.

**Single agent.** `agents/registry.py` holds one `AgentSpec` (`ask_julian`); `agents/router.py`
always routes to it; `agents/career/ask_julian.py` builds a `create_react_agent` with **no tools**.
The one-agent registry is kept so the generic chat pipeline (routing, message labels, sample
cards) keeps working.

**Request flow** (`chat/routes.py::chat_stream`, POST `/app/chat`, SSE):
1. **Free-query gate** — anonymous visitors get `FREE_QUERY_LIMIT` (default 3) queries, counted
   in the signed session cookie. On overflow it emits an `sse.GATE` event and the client opens
   the sign-in overlay. The counter is incremented in the **route-handler body, not inside the
   SSE generator** — otherwise the Set-Cookie header is already sent and the count is lost.
2. **CV-request intercept** — `cv_export.is_cv_request()` short-circuits "give me your CV"
   messages to a canned HTML bubble with `/cv/pdf` + `/cv/docx` buttons (no LLM call).
3. Otherwise stream tokens from the LangGraph agent (`agents.base.cached_agent`).

**Content is file-based, not DB.** SQLite stores only chat auth/history (3 tables:
`chat_users` / `chat_sessions` / `chat_messages`). The CV, projects, nav links (`PROFILE_LINKS`,
`PROJECTS_BY_SECTOR` in `chat/components.py`) and the articles feed (`config/articles.yaml` via
`utils/articles.py`) are all files.

**SQLite via `SCHEMA = "main"`.** `db.py` uses SQLite; `main` is SQLite's default database name,
so schema-qualified queries (`main.chat_users`, used in `auth/routes.py`) stay valid. `NOW()` is
replaced with `CURRENT_TIMESTAMP`. Override `DB_URL` for other backends.

**LLM provider is swappable** via `LLM_PROVIDER` (`xai` Grok default / `openai` / `anthropic`),
dispatched in `utils/llm.build_llm()`. Agents and the eval judge both go through it.

**CV downloads** (`cv_export.py`): `/cv/pdf` serves the real `docs/*.pdf`; `/cv/docx` is generated
from `cv.md` via python-docx.

## Gotchas that will bite you

- **FastHTML route paths can't contain a dot** — it's treated as a format suffix. Use `/cv/pdf`,
  not `/cv.pdf`.
- **Coolify env vars: never name one `SERVICE_URL*`** — Coolify reserves that prefix for its own
  magic vars and injects it empty. The app reads `APP_BASE_URL` (fed in compose from Coolify's
  auto `SERVICE_URL_WEB`).
- **Coolify compose must `expose:` the port, not `ports:`** — publishing `5011:5011` collides with
  other apps on the shared server. Traefik routes the domain to the internal port.
- **SQLite persistence** depends on the named volume `kaljuvee-data:/app/data`
  (`DB_URL=sqlite:////app/data/kaljuvee_chat.db` in compose); without it the DB resets each deploy.

## Deploy / CI-CD

Coolify (Docker-Compose build pack). **Push to `main` auto-deploys** via a GitHub push webhook →
`https://coolify.finespresso.org/webhooks/source/github/events/manual`. Full setup, the `gh`
command to recreate the webhook, and post-deploy checks are in **`SKILLS.md §4`**.
