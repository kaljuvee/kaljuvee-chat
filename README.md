# Ask Julian — kaljuvee.chat

A personal, recruiter-facing AI chatbot that answers questions about **Julian Kaljuvee's**
career, skills, experience and projects. Answers are grounded in Julian's CV (`docs/`), so
the assistant stays factual and points recruiters to the right links and contact details.

Built with **FastHTML** + **LangGraph**, backed by a small **SQLite** database.

## Features

- **Grounded Q&A** — the full CV (`prompts/shared/cv.md`) plus curated facts
  (`prompts/shared/career_facts.md`) are injected into the system prompt; no RAG needed.
- **3-free-query gate** — anonymous visitors get 3 free questions, then must sign in
  (email/password or Google) to continue. Protects against bots and token drain.
  Configurable via `FREE_QUERY_LIMIT`.
- **Left nav** — logo, sample questions, profile links (LinkedIn, personal site, GitHub,
  Predictive Labs), and selected projects grouped by sector.
- **Right pane** — an Articles/writing feed driven by `config/articles.yaml`
  (append an entry per post; optional RSS auto-merge).

## Run locally

```bash
python3 -m venv .venv && source .venv/bin/activate   # or: uv venv
pip install -r requirements.txt                       # or: uv pip install -r requirements.txt
cp env.sample .env    # add XAI_API_KEY (Grok) or OPENAI_API_KEY
python main.py        # http://localhost:5011
```

The SQLite file (`kaljuvee_chat.db`) is created automatically on first run.

## Configuration

Key `.env` settings (see `env.sample`):

- `LLM_PROVIDER` — `xai` (Grok, default) or `openai`
- `XAI_API_KEY` / `OPENAI_API_KEY`
- `FREE_QUERY_LIMIT` — free anonymous queries before sign-in (default `3`)
- `SERVICE_URL` — public URL, used for OAuth redirect and email links
- `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` — optional Google sign-in
- `POSTMARK_API_TOKEN` — optional, for verify/reset emails

## Updating content

- **CV / facts**: edit `prompts/shared/cv.md` and `prompts/shared/career_facts.md`.
- **Persona / behaviour**: edit `prompts/system/ask_julian.md`.
- **Nav links & projects**: edit `PROFILE_LINKS` / `PROJECTS_BY_SECTOR` in `chat/components.py`.
- **Articles feed**: add entries to `config/articles.yaml`.

## Deploy

Dockerfile + `.github/workflows/deploy.yml` (Coolify webhook) are included.

> **Note:** SQLite lives in a file inside the container. On Coolify, mount a **persistent
> volume** for `kaljuvee_chat.db` so chat history/accounts survive redeploys — otherwise
> the DB is recreated on each deploy.
