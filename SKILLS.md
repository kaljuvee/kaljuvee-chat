# SKILLS.md — Ask Julian (kaljuvee.chat)

Operational guide for developing, testing, evaluating and deploying the CV chatbot.

---

## 1. Local development

```bash
uv venv && source .venv/bin/activate        # or: python -m venv .venv
uv pip install -r requirements.txt          # or: pip install -r requirements.txt
cp env.sample .env                          # add XAI_API_KEY (or OPENAI/ANTHROPIC)
python main.py                              # http://localhost:5011
```

SQLite (`kaljuvee_chat.db`) is created automatically. Health: `curl localhost:5011/health`.

Key routes: `/` → `/app` (chat), `/health`, `/cv/pdf`, `/cv/docx`.

## 2. Tests

```bash
pytest -q                                   # structural smoke tests (tests/test_smoke.py)
```

## 3. Evals (deepeval + Grok LLM judge)

```bash
uv pip install -r requirements-eval.txt     # deepeval (dev-only, not in the image)
python -m evals.run_eval                     # full suite → eval/eval-results.json + evals/EVAL_REPORT.md
python -m evals.run_eval --category technical --limit 5
```

22 recruiter-question cases across cv_facts / technical / experience_years / career / soft
(incl. guardrails). Each live answer is scored on Groundedness / Correctness / Relevancy by a
Grok judge (`evals/grok_judge.py`). Baseline ≈ 82% pass. See `evals/README.md`.

## 4. Deploy (Coolify + GitHub webhook CI/CD)

**Auto-deploy: push to `main` → GitHub webhook → Coolify builds & deploys.** No manual step.

```bash
git add <files> && git commit -m "…" && git push origin main   # triggers deploy
```

### How CI/CD is wired (replicated from the predictivelabsai repos)

- The Coolify app (project *predictive labs apps* → *production*) deploys the public repo
  `github.com/kaljuvee/kaljuvee-chat`, branch `main`, Build Pack **Docker Compose**.
- A GitHub **push webhook** on the repo points at Coolify's manual endpoint:
  `https://coolify.finespresso.org/webhooks/source/github/events/manual`
  (content-type `json`, shared secret set in Coolify *Webhooks* tab **and** the GitHub hook).
- Created via `gh` (no browser):
  ```bash
  gh api repos/kaljuvee/kaljuvee-chat/hooks -X POST --input - <<'JSON'
  { "name":"web","active":true,"events":["push"],
    "config":{"url":"https://coolify.finespresso.org/webhooks/source/github/events/manual",
              "content_type":"json","insecure_ssl":"0","secret":"<same-secret>"} }
  JSON
  ```
- Inspect deliveries: `gh api repos/kaljuvee/kaljuvee-chat/hooks/<id>/deliveries`.
- Manual redeploy button lives in the Coolify app view (or the deploy webhook:
  `https://coolify.finespresso.org/api/v1/deploy?uuid=<app-uuid>&force=false`, Bearer API token).

### Coolify gotchas (learned the hard way)

- **Compose is required** — Coolify is in Docker-Compose mode; `docker-compose.yaml` must exist.
- **Do NOT publish a host port** (`ports: 5011:5011`) — it collides with other apps on the
  shared server (`Bind for 0.0.0.0:5011 failed: port is already allocated`). Use `expose: 5011`;
  Traefik routes the domain to the internal port.
- **Never name an env var `SERVICE_URL*`** — Coolify reserves that prefix for its own magic vars
  and injects it empty. The app reads `APP_BASE_URL`, fed in compose from Coolify's auto
  `SERVICE_URL_WEB` (= `https://kaljuvee.chat`).
- **SQLite persistence** — DB lives on the named volume `kaljuvee-data:/app/data`
  (`DB_URL=sqlite:////app/data/kaljuvee_chat.db`); without the volume it resets each deploy.

### Post-deploy verification

```bash
curl -s -o /dev/null -w '%{http_code}\n' https://kaljuvee.chat/health   # 200
curl -s -o /dev/null -w '%{http_code}\n' https://kaljuvee.chat/cv/pdf   # 200
```

## 5. Environment variables

| Variable | Req | Description |
|---|---|---|
| `XAI_API_KEY` | yes* | xAI (Grok) key — *or* `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` |
| `LLM_PROVIDER` | no | `xai` (default) / `openai` / `anthropic` |
| `APP_SECRET` | yes | session signing secret |
| `APP_BASE_URL` | no | public URL for OAuth redirect + email links (compose sets it) |
| `DB_URL` | no | default `sqlite:///kaljuvee_chat.db`; compose overrides to the volume path |
| `FREE_QUERY_LIMIT` | no | anonymous free queries before sign-in (default 3) |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | no | Google sign-in |
| `POSTMARK_API_TOKEN` / `FROM_EMAIL` | no | verify/reset emails |

Secrets live only in `.env` (gitignored) and the Coolify UI — never committed. Google OAuth
client "Ask Julian (kaljuvee.chat)" lives in the **finespresso** GCP project; redirect URIs
`https://kaljuvee.chat/auth/google/callback` and `http://localhost:5011/auth/google/callback`.

## 6. Updating content

- **What the bot knows** — `prompts/shared/cv.md`, `prompts/shared/career_facts.md`
- **How it behaves** — `prompts/system/ask_julian.md`
- **Nav links / projects** — `PROFILE_LINKS` / `PROJECTS_BY_SECTOR` in `chat/components.py`
- **Articles feed** — `config/articles.yaml`
- **CV downloads** — `/cv/pdf` serves `docs/*.pdf`; `/cv/docx` is generated from `cv.md`

See `docs/architecture_readme.md` for the full architecture with Mermaid diagrams.
