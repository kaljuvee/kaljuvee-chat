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

# --- CV download routes (/cv.pdf, /cv.docx) ---

from cv_export import register_cv_routes
register_cv_routes(rt)

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
