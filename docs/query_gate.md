# Query gate

The application has an anonymous free-query gate to limit token usage. Despite the
name, this is **not** a bring-your-own-key (BYOK) flow: visitors are prompted to
sign in after using the free allowance, and the application continues to use the
server-configured LLM provider key.

## User-visible behaviour

The default allowance is three queries per browser session:

1. An anonymous visitor may submit three non-empty messages normally.
2. A fourth submission receives a `gate` server-sent event instead of being sent
   to an agent.
3. The chat displays the gate message and opens the sign-in overlay.
4. The blocked question is saved in browser `sessionStorage` under
   `aj_pending_q`.
5. After a successful sign-in and page reload, the client restores and
   automatically resubmits that question.

The limit is inclusive: with `FREE_QUERY_LIMIT=3`, requests numbered 1, 2, and 3
are accepted; request 4 and later are gated while the visitor remains anonymous.
Signed-in users bypass the gate.

## Server-side flow

The gate is implemented in `chat/routes.py` in `POST /app/chat`:

- Empty messages are rejected with HTTP 400 before gate evaluation.
- Authentication is determined by the presence of `chat_email` in the signed
  application session.
- For an anonymous request, `anon_queries` is compared with
  `FREE_QUERY_LIMIT`. If the count is already at or above the limit, the route
  returns an SSE stream containing a single `gate` event. It does not create a
  chat session, persist the message, route to an agent, or invoke an LLM.
- If the request is allowed, the counter is incremented immediately in the route
  handler so the updated session cookie is included in the response. The rest of
  the request then proceeds normally.

The counter is incremented for every accepted, non-empty anonymous chat request,
not only requests that reach the LLM. For example, locally handled CV requests
also consume one query. Because counting happens before downstream processing, a
request that later fails still consumes one query.

The counter helpers are in `utils/session.py`:

- `get_anon_query_count()` reads `anon_queries`, defaulting to zero.
- `increment_anon_query_count()` increments and stores it.
- `reset_anon_query_count()` exists but is not called by the current application.

The browser-side handler is in `static/chat.js`. On a `gate` event it adds the
server-provided message, preserves the blocked question, and calls
`showSignIn()`. The SSE event name is defined as `GATE = "gate"` in
`chat/sse.py`.

## Configuration

Set the allowance with an environment variable:

```dotenv
FREE_QUERY_LIMIT=3
```

`utils/config.py` defines the default as `3`. The comparison is direct, so `0`
causes all anonymous non-empty submissions to be gated immediately. Changes to
environment configuration require an application restart (settings are cached).

The LLM credentials remain deployment secrets such as `XAI_API_KEY`,
`OPENAI_API_KEY`, or `ANTHROPIC_API_KEY`, selected by `LLM_PROVIDER`. There is no
UI, endpoint, session field, or database field for a visitor's own API key.

## Session and persistence details

The count lives in the signed application session cookie, rather than in the
database or against an IP address. Consequently it is browser/session scoped and
is intended as lightweight token-drain protection, not a hard security or billing
quota. Clearing or replacing the session cookie starts a new anonymous allowance.

Anonymous conversations are persisted under a lightweight guest user. The auth
flows migrate guest sessions to the authenticated user. Signing in bypasses the
anonymous count; the count itself is not reset. Signing out removes the email and
user ID but leaves `anon_queries` in the session, so the previous anonymous count
applies again.

## Relevant files

- `chat/routes.py` — enforcement and `gate` SSE response
- `utils/session.py` — authentication/session counter helpers
- `utils/config.py` — `FREE_QUERY_LIMIT` setting
- `chat/sse.py` — SSE event names
- `static/chat.js` — gate UI, pending-question storage, and post-login retry
- `auth/routes.py` — sign-in and guest-conversation migration
- `tests/test_smoke.py` — unit-level coverage of the session counter helpers

Current automated coverage verifies the counter helpers, but does not exercise
the full `/app/chat` boundary, SSE gate response, or browser retry flow.
