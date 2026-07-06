# Ask Julian — Architecture

**Ask Julian** (kaljuvee.chat) is a personal, recruiter-facing AI chatbot that answers
questions about Julian Kaljuvee's career, skills and projects. Answers are **grounded in the
CV** — the full CV plus curated facts are injected into the system prompt, so the assistant
stays factual rather than relying on retrieval or model memory.

It is built on **FastHTML** (server-rendered hypermedia + SSE streaming) with a single
**LangGraph** agent and a small **SQLite** data layer.

This document describes the system with Mermaid diagrams. Render them in any Mermaid-compatible
viewer (GitHub, VS Code, etc.).

---

## 1. High-Level System Architecture

The whole app runs as a single FastHTML process. There is no separate frontend build and no
external database service — SQLite is a file on disk, and the only network dependency at
request time is the LLM provider.

```mermaid
flowchart TB
    USER(["Recruiter (browser)"])

    subgraph Server["FastHTML process (main.py, port 5011)"]
        IDX["/  →  redirect to /app<br/>main.py"]
        APP["Chat app<br/>chat/routes.py · /app<br/>3-pane shell + SSE streaming"]
        AUTH["Auth routes<br/>auth/routes.py<br/>login · register · reset · Google OAuth"]
        STATIC["Static assets<br/>/static (css, js) · /img (portrait)"]
        GATE{{"Free-query gate<br/>3 anon queries → sign in"}}
    end

    subgraph Agent["LangGraph agent"]
        ROUTER["router.py<br/>single agent → ask_julian"]
        ASKJ["ask_julian<br/>create_react_agent, no tools"]
        PROMPT["Grounded system prompt<br/>cv.md + career_facts.md + ask_julian.md"]
    end

    subgraph Data["SQLite (kaljuvee_chat.db)"]
        DB[("chat_users<br/>chat_sessions<br/>chat_messages")]
    end

    subgraph Content["File-based content"]
        CV["prompts/shared/cv.md<br/>prompts/shared/career_facts.md"]
        ART["config/articles.yaml"]
    end

    subgraph External["External APIs"]
        LLM[["LLM provider<br/>xAI Grok (default) /<br/>OpenAI / Anthropic"]]
        GOOG[["Google OAuth<br/>(optional sign-in)"]]
        RSS[["RSS feeds<br/>(optional, articles)"]]
        POST[["Postmark<br/>(optional verify/reset email)"]]
    end

    USER -->|HTTPS| IDX
    USER -->|HTTPS| APP
    APP --> GATE
    GATE -->|allowed| ROUTER
    ROUTER --> ASKJ
    ASKJ --> PROMPT
    PROMPT -. reads .-> CV
    ASKJ -->|chat completion| LLM
    APP -->|persist chat| DB
    AUTH -->|accounts| DB
    AUTH -.->|optional| GOOG
    APP -. articles feed .-> ART
    ART -.->|optional merge| RSS
    AUTH -.->|optional| POST
```

---

## 2. Chat Request Flow (with the free-query gate)

Anonymous visitors get `FREE_QUERY_LIMIT` (default **3**) free questions, tracked in the
signed session cookie. The 4th anonymous request returns a `gate` SSE event instead of an
answer, and the client opens the sign-in overlay. Any sign-in (email/password or Google)
removes the limit.

The query counter is incremented in the **route handler body** — not inside the SSE
generator — so the updated cookie is written before the streaming response starts.

```mermaid
sequenceDiagram
    participant B as Browser (chat.js)
    participant R as chat/routes.py
    participant S as Session cookie
    participant A as LangGraph agent
    participant L as LLM provider
    participant DB as SQLite

    B->>R: POST /app/chat {msg}
    R->>S: read signed_in? anon_count?
    alt not signed in AND anon_count >= limit
        R-->>B: SSE event: gate
        B->>B: open sign-in overlay
    else allowed
        R->>S: increment anon_count (handler body)
        R->>DB: ensure user + session, persist user msg
        R-->>B: SSE event: session, agent_route
        R->>A: astream_events(history + msg)
        A->>L: grounded prompt + messages
        loop streamed tokens
            L-->>A: token
            A-->>R: on_chat_model_stream
            R-->>B: SSE event: token
        end
        R->>DB: persist assistant msg
        R-->>B: SSE event: done
    end
```

---

## 3. Prompt Grounding

There is no vector store or RAG. The CV is small (~4 pages), so the full text plus a curated
facts file are concatenated into one system prompt at agent-build time. This keeps answers
deterministic and cheap, and makes updates a one-file edit.

```mermaid
flowchart LR
    subgraph Files["prompts/"]
        P1["system/ask_julian.md<br/>persona · rules · guardrails"]
        P2["shared/cv.md<br/>verbatim CV"]
        P3["shared/career_facts.md<br/>company, projects by sector, links"]
    end

    P1 --> COMPOSE
    P2 --> COMPOSE
    P3 --> COMPOSE
    COMPOSE["agents/base._load_system_prompt()"] --> SYS["Single grounded<br/>system prompt (~19k chars)"]
    SYS --> AGENT["create_react_agent(llm, tools=[], prompt=sys)"]
```

To update what the bot knows, edit `cv.md` / `career_facts.md`; to change how it behaves,
edit `ask_julian.md`. No code changes required.

---

## 4. Data Model

Only chat auth and history are stored. Everything else (CV, projects, links, articles) is
file-based content, not database rows.

```mermaid
erDiagram
    chat_users ||--o{ chat_sessions : has
    chat_sessions ||--o{ chat_messages : contains

    chat_users {
        int id PK
        string email UK
        string password_hash
        string name
        bool is_verified
        string verify_token
        string reset_token
        datetime created_at
    }
    chat_sessions {
        int id PK
        int user_id FK
        string title
        string agent_slug
        string share_token
        datetime updated_at
    }
    chat_messages {
        int id PK
        int session_id FK
        string role
        text content
        string agent_slug
        datetime created_at
    }
```

---

## 5. Articles / Writing Feed

The right-hand pane renders a tag-filterable feed of Julian's writing. Because LinkedIn
articles are auth-gated and have no public RSS, the source of truth is a hand-curated YAML
file. Any RSS/Atom sources listed there are merged in and de-duplicated by URL, so an
RSS-capable blog updates automatically.

```mermaid
flowchart TB
    YAML["config/articles.yaml<br/>manual entries: title, url, date, tags"]
    RSSCFG["rss_feeds: [ ... ]<br/>(optional)"]
    LOADER["utils/articles.load_articles()<br/>15-min cache"]
    FEEDP["feedparser<br/>(optional dependency)"]
    PANE["right_pane()<br/>tag chips + cards"]

    YAML --> LOADER
    RSSCFG --> FEEDP --> LOADER
    LOADER -->|merge + dedup by URL,<br/>sort by date desc| PANE
```

---

## 6. Configuration & Deployment

| Concern | Mechanism |
|---|---|
| LLM provider | `LLM_PROVIDER` = `xai` (default) / `openai` / `anthropic` — dispatched in `utils/llm.py` via LangChain |
| Free-query limit | `FREE_QUERY_LIMIT` (default 3) |
| Database | `DB_URL` (default `sqlite:///kaljuvee_chat.db`) |
| Google sign-in | `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET`; redirect `<SERVICE_URL>/auth/google/callback` |
| Email (optional) | `POSTMARK_API_TOKEN` for verify/reset links |
| Container | `Dockerfile`; CI trigger in `.github/workflows/deploy.yml` (Coolify webhook) |

```mermaid
flowchart LR
    GIT["git push → GitHub main"] -->|webhook| COOLIFY["Coolify"]
    COOLIFY -->|build| IMG["Docker image<br/>(python:3.12-slim)"]
    IMG --> RUN["Container :5011"]
    VOL[("Persistent volume<br/>kaljuvee_chat.db")] -. mount .-> RUN
```

> **Deployment note:** SQLite is a single file inside the container. Mount a **persistent
> volume** for `kaljuvee_chat.db` on Coolify so accounts and chat history survive redeploys —
> otherwise the database is recreated on each deploy.
