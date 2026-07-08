"""Chat routes -- 3-pane UI + SSE streaming for Talk to Julian."""

from __future__ import annotations

import json
import logging

from langchain_core.messages import HumanMessage, AIMessage
from starlette.requests import Request
from starlette.responses import StreamingResponse, JSONResponse

from chat.layout import chat_page
from chat import sse
from utils.config import settings
from utils.session import (get_user_email, set_user_email, clear_user,
                           get_user_id, set_user_id, is_signed_in,
                           get_anon_query_count, increment_anon_query_count)

log = logging.getLogger(__name__)


def _get_db():
    from db import SessionLocal
    return SessionLocal()


def _ensure_user(sess) -> tuple[int | None, str | None]:
    email = get_user_email(sess)
    if not email:
        return None, None
    uid = get_user_id(sess)
    if uid:
        return uid, email
    from sqlalchemy import text
    db = _get_db()
    try:
        db.execute(
            text("INSERT INTO chat_users (email) VALUES (:email) "
                 "ON CONFLICT (email) DO NOTHING"),
            {"email": email},
        )
        db.commit()
        row = db.execute(
            text("SELECT id FROM chat_users WHERE email = :email"),
            {"email": email},
        ).fetchone()
        uid = row[0]
    finally:
        db.close()
    set_user_id(sess, uid)
    return uid, email


def _ensure_guest(sess) -> int:
    """Create/reuse a lightweight guest user so anonymous chat can be persisted."""
    uid = get_user_id(sess)
    if uid:
        return uid
    from sqlalchemy import text
    db = _get_db()
    guest_email = f"guest+{id(sess):x}@kaljuvee.chat"
    try:
        db.execute(
            text("INSERT INTO chat_users (email) VALUES (:email) "
                 "ON CONFLICT (email) DO NOTHING"),
            {"email": guest_email},
        )
        db.commit()
        row = db.execute(
            text("SELECT id FROM chat_users WHERE email = :email"),
            {"email": guest_email},
        ).fetchone()
        uid = row[0]
    finally:
        db.close()
    set_user_id(sess, uid)
    return uid


def _ensure_session(user_id, sid, first_message=None):
    from sqlalchemy import text
    db = _get_db()
    try:
        if sid:
            try:
                sid_int = int(sid)
            except (TypeError, ValueError):
                sid_int = 0
            if sid_int:
                row = db.execute(
                    text("SELECT id FROM chat_sessions WHERE id = :sid AND user_id = :uid"),
                    {"sid": sid_int, "uid": user_id},
                ).fetchone()
                if row:
                    return sid_int

        title = (first_message or "New chat")[:80]
        db.execute(
            text("INSERT INTO chat_sessions (user_id, title) VALUES (:uid, :title)"),
            {"uid": user_id, "title": title},
        )
        db.commit()
        row = db.execute(text("SELECT last_insert_rowid()")).fetchone()
        return row[0]
    finally:
        db.close()


def _list_sessions(user_id, limit=30):
    from sqlalchemy import text
    db = _get_db()
    try:
        rows = db.execute(
            text("SELECT id, title, agent_slug, updated_at FROM chat_sessions "
                 "WHERE user_id = :uid ORDER BY updated_at DESC LIMIT :lim"),
            {"uid": user_id, "lim": limit},
        ).fetchall()
        return [dict(r._mapping) for r in rows]
    finally:
        db.close()


def _session_messages(session_id):
    from sqlalchemy import text
    db = _get_db()
    try:
        rows = db.execute(
            text("SELECT role, content, agent_slug FROM chat_messages "
                 "WHERE session_id = :sid ORDER BY id ASC"),
            {"sid": session_id},
        ).fetchall()
        return [dict(r._mapping) for r in rows]
    finally:
        db.close()


def _persist_message(session_id, role, content, agent_slug=None, tool_calls=None):
    from sqlalchemy import text
    db = _get_db()
    try:
        db.execute(
            text("INSERT INTO chat_messages (session_id, role, content, agent_slug, tool_calls) "
                 "VALUES (:sid, :role, :content, :agent, :tools)"),
            {"sid": session_id, "role": role, "content": content,
             "agent": agent_slug,
             "tools": json.dumps(tool_calls) if tool_calls else None},
        )
        db.execute(
            text("UPDATE chat_sessions SET updated_at = CURRENT_TIMESTAMP WHERE id = :sid"),
            {"sid": session_id},
        )
        db.commit()
    finally:
        db.close()


def register_chat_routes(rt):
    """Register all chat routes on the given FastHTML router."""

    @rt("/app")
    def app_home(sess, sid: str = ""):
        uid, email = _ensure_user(sess)
        sessions = _list_sessions(uid) if uid else []
        messages = []
        current_agent = None
        if uid and sid:
            try:
                from sqlalchemy import text
                db = _get_db()
                try:
                    row = db.execute(
                        text("SELECT id, agent_slug FROM chat_sessions WHERE id = :sid AND user_id = :uid"),
                        {"sid": int(sid), "uid": uid},
                    ).fetchone()
                    if row:
                        messages = _session_messages(int(sid))
                        current_agent = row._mapping.get("agent_slug")
                finally:
                    db.close()
            except (TypeError, ValueError):
                pass

        return chat_page(
            user_email=email,
            sessions=sessions,
            current_sid=str(sid) if sid else "",
            messages=messages,
            current_agent_slug=current_agent,
        )

    @rt("/app/chat", methods=["POST"])
    async def chat_stream(request: Request):
        sess = request.session
        form = await request.form()
        user_msg = (form.get("msg") or "").strip()
        sid_str = form.get("sid") or ""

        if not user_msg:
            return JSONResponse({"error": "empty message"}, status_code=400)

        # --- Free-query gate (bot / token-drain protection) ---------------
        free_limit = settings().free_query_limit
        signed_in = is_signed_in(sess)
        if not signed_in and get_anon_query_count(sess) >= free_limit:
            async def gate_stream():
                yield sse.event(sse.GATE, {
                    "limit": free_limit,
                    "message": ("You've reached the free preview limit. "
                                "Please sign in to continue chatting with Talk to Julian."),
                })
            return StreamingResponse(gate_stream(), media_type="text/event-stream")

        # Count this query (only for anonymous visitors). Mutate the session in the
        # handler body — not inside the generator — so the cookie is persisted.
        if not signed_in:
            increment_anon_query_count(sess)
            uid = _ensure_guest(sess)
        else:
            uid, _ = _ensure_user(sess)
            if not uid:
                uid = _ensure_guest(sess)

        session_id = _ensure_session(uid, sid_str, first_message=user_msg)

        from agents import router as agent_router
        from agents.registry import by_slug
        agent_slug = agent_router.route(user_msg)
        spec = by_slug(agent_slug)

        _persist_message(session_id, "user", user_msg)

        # CV request → return HTML with PDF + Word download buttons (no LLM call).
        from cv_export import is_cv_request, cv_response_html
        if is_cv_request(agent_router.strip_prefix(user_msg)):
            html = cv_response_html()
            _persist_message(session_id, "assistant", html, agent_slug=agent_slug)

            async def cv_stream():
                yield sse.event("session", {"sid": session_id})
                yield sse.event(sse.AGENT_ROUTE, {
                    "slug": agent_slug,
                    "agent": spec.name if spec else agent_slug,
                    "icon": spec.icon if spec else "*",
                })
                yield sse.event(sse.TOKEN, {"text": html})
                yield sse.event(sse.DONE, {"slug": agent_slug})

            return StreamingResponse(cv_stream(), media_type="text/event-stream")

        # "Book a call" request → return HTML with a Cal.com button (no LLM call).
        from scheduling import is_scheduling_request, scheduling_response_html
        if is_scheduling_request(agent_router.strip_prefix(user_msg)):
            html = scheduling_response_html()
            _persist_message(session_id, "assistant", html, agent_slug=agent_slug)

            async def sched_stream():
                yield sse.event("session", {"sid": session_id})
                yield sse.event(sse.AGENT_ROUTE, {
                    "slug": agent_slug,
                    "agent": spec.name if spec else agent_slug,
                    "icon": spec.icon if spec else "*",
                })
                yield sse.event(sse.TOKEN, {"text": html})
                yield sse.event(sse.DONE, {"slug": agent_slug})

            return StreamingResponse(sched_stream(), media_type="text/event-stream")

        history = _session_messages(session_id)[:-1]
        stripped_msg = agent_router.strip_prefix(user_msg)

        async def event_stream():
            yield sse.event("session", {"sid": session_id})
            yield sse.event(sse.AGENT_ROUTE, {
                "slug": agent_slug,
                "agent": spec.name if spec else agent_slug,
                "icon": spec.icon if spec else "*",
            })

            lc_messages = []
            for h in history[-20:]:
                if h["role"] == "user":
                    lc_messages.append(HumanMessage(content=h["content"]))
                elif h["role"] == "assistant":
                    lc_messages.append(AIMessage(content=h["content"]))
            lc_messages.append(HumanMessage(content=stripped_msg))

            accumulated = []

            try:
                from agents.base import cached_agent
                graph = cached_agent(agent_slug)

                async for event in graph.astream_events({"messages": lc_messages}, version="v2"):
                    kind = event["event"]
                    if kind == "on_chat_model_stream":
                        chunk = event["data"].get("chunk")
                        if chunk and hasattr(chunk, "content") and isinstance(chunk.content, str) and chunk.content:
                            if not getattr(chunk, "tool_call_chunks", None):
                                accumulated.append(chunk.content)
                                yield sse.event(sse.TOKEN, {"text": chunk.content})
            except Exception as e:
                log.exception("chat stream failed")
                yield sse.event(sse.ERROR, {"message": str(e)})

            final = "".join(accumulated) or "(no response)"
            _persist_message(session_id, "assistant", final, agent_slug=agent_slug)
            from sqlalchemy import text
            db = _get_db()
            try:
                db.execute(text("UPDATE chat_sessions SET agent_slug = :slug WHERE id = :sid"),
                           {"slug": agent_slug, "sid": session_id})
                db.commit()
            finally:
                db.close()

            # Stream any relevant chart(s) inline, after the text answer.
            try:
                from charts import detect_charts, build_chart
                for cname in detect_charts(stripped_msg):
                    c = build_chart(cname)
                    if c:
                        yield sse.event(sse.CHART, c)
            except Exception as e:
                log.warning("chart emit failed: %s", e)

            yield sse.event(sse.DONE, {"slug": agent_slug})

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    @rt("/app/auth/signin", methods=["POST"])
    async def signin(request: Request):
        form = await request.form()
        email = (form.get("email") or "").strip().lower()
        if "@" not in email:
            return JSONResponse({"ok": False, "error": "invalid email"}, status_code=400)
        set_user_email(request.session, email)
        _ensure_user(request.session)
        return JSONResponse({"ok": True, "email": email})

    @rt("/app/auth/signout", methods=["POST"])
    async def signout(request: Request):
        clear_user(request.session)
        return JSONResponse({"ok": True})

    @rt("/api/share/{sid}", methods=["POST"])
    async def share_session(request: Request, sid: str):
        sess = request.session
        uid, _ = _ensure_user(sess)
        if not uid:
            uid = get_user_id(sess)
        if not uid:
            return JSONResponse({"error": "not signed in"}, status_code=401)
        try:
            sid_int = int(sid)
        except (TypeError, ValueError):
            return JSONResponse({"error": "invalid session"}, status_code=400)
        from sqlalchemy import text
        db = _get_db()
        try:
            row = db.execute(
                text("SELECT share_token FROM chat_sessions WHERE id = :sid AND user_id = :uid"),
                {"sid": sid_int, "uid": uid},
            ).fetchone()
            if not row:
                return JSONResponse({"error": "session not found"}, status_code=404)
            token = row[0]
            if not token:
                import secrets
                token = secrets.token_urlsafe(32)
                db.execute(
                    text("UPDATE chat_sessions SET share_token = :token WHERE id = :sid"),
                    {"token": token, "sid": sid_int},
                )
                db.commit()
            return JSONResponse({"token": token, "url": f"/shared/{token}"})
        finally:
            db.close()

    @rt("/shared/{token}")
    def shared_chat(token: str):
        from sqlalchemy import text
        db = _get_db()
        try:
            row = db.execute(
                text("SELECT s.id, s.title, s.agent_slug, u.email "
                     "FROM chat_sessions s "
                     "JOIN chat_users u ON u.id = s.user_id "
                     "WHERE s.share_token = :token"),
                {"token": token},
            ).fetchone()
            if not row:
                from starlette.responses import HTMLResponse
                return HTMLResponse("<h2>Chat not found</h2>", status_code=404)
            sid = row[0]
            messages = _session_messages(sid)
        finally:
            db.close()

        from chat.layout import shared_chat_page
        return shared_chat_page(
            title=row[1] or "Shared Chat",
            messages=messages,
            agent_slug=row[2],
        )
