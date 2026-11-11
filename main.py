import os

from fasthtml.common import fast_app, serve
from starlette.responses import RedirectResponse, JSONResponse
from starlette.staticfiles import StaticFiles

from db import init_db

app, rt = fast_app(
    hdrs=(),
    secret_key=os.environ.get('APP_SECRET', 'ask-julian-2026'),
)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/img", StaticFiles(directory="img"), name="img")


@rt("/health")
def health():
    return JSONResponse({"status": "ok"})


@rt("/")
def index():
    return RedirectResponse("/app", status_code=303)


# --- Chat routes ---

from chat.routes import register_chat_routes
register_chat_routes(rt)

# --- CV download routes (/cv/pdf, /cv/docx) ---

from cv_export import register_cv_routes
register_cv_routes(rt)

# --- Visuals dashboard (/visuals) ---

from visuals import register_visuals_routes
register_visuals_routes(rt)

# --- Research papers (/research, /research/<slug>) ---

from research_pages import register_research_routes, register_llms_txt
register_research_routes(rt)
register_llms_txt(rt)

# FastHTML registers a catch-all static route (`/{fname:path}.{ext:static}`) that would
# swallow /llms.txt and /research/<slug>.pdf; move our explicit routes in front of it.
_mine = [r for r in app.router.routes
         if getattr(r, "path", "") in ("/llms.txt", "/research", "/research/{slug}")]
app.router.routes[:] = _mine + [r for r in app.router.routes if r not in _mine]

# --- Voice mode (WebSocket proxy to x.ai realtime agent) ---

from voice import register_voice_routes
register_voice_routes(app)

# --- Auth routes ---

from auth.routes import register_auth_routes
register_auth_routes(rt)


@app.on_event("startup")
async def startup():
    try:
        init_db()
    except Exception as e:
        print(f"DB init warning: {e}")


serve(port=int(os.environ.get('PORT', 5011)), reload=False)
