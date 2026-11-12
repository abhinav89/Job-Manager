"""Optional localhost HTTP adapter and static dashboard server."""
from contextlib import asynccontextmanager
import ipaddress
import re
from urllib.parse import urlsplit
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError
from sqlalchemy.exc import OperationalError
from slowapi.errors import RateLimitExceeded
from cv_tailor.config import configure, capabilities
from cv_tailor.database import init_db
from cv_tailor.limiter import limiter
from cv_tailor.workspace import WorkspaceError

configure()

@asynccontextmanager
async def lifespan(app):
    init_db()
    yield

api = FastAPI(title="CV Tailor local API")
api.state.limiter = limiter

@api.exception_handler(WorkspaceError)
async def workspace_error(request, exc):
    return JSONResponse(status_code=exc.status, content={"detail": str(exc), "code": exc.code})

@api.exception_handler(ValueError)
async def input_error(request, exc):
    return JSONResponse(status_code=422, content={"detail": str(exc)})

@api.exception_handler(OperationalError)
async def busy_error(request, exc):
    return JSONResponse(status_code=503, content={"detail": "Workspace is busy. Refresh before retrying a write."})

@api.exception_handler(RateLimitExceeded)
async def limited(request, exc):
    return JSONResponse(status_code=429, content={"detail": "Too many requests. Try again shortly."})

from cv_tailor.routers import database_routes, generate_routes, tracker_routes, interview_routes, code_routes, presets_routes, scraper_routes, assistant_routes, workspace_routes
for router in (workspace_routes, database_routes, generate_routes, tracker_routes, interview_routes, code_routes, presets_routes, scraper_routes, assistant_routes):
    api.include_router(router.router)

@api.get("/health")
def health():
    return {"status": "ok"}

app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None)

@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    from fastapi.responses import Response
    return Response(status_code=204)

@app.middleware("http")
async def local_access(request: Request, call_next):
    host = request.url.hostname
    if host not in {"localhost", "127.0.0.1", "::1", "testserver"}:
        return JSONResponse(status_code=403, content={"detail": "CV Tailor accepts localhost requests only."})
    client = request.client.host if request.client else ""
    if client != "testclient":
        try:
            if not ipaddress.ip_address(client).is_loopback:
                raise ValueError()
        except ValueError:
            return JSONResponse(status_code=403, content={"detail": "Local connections only."})
    origin = request.headers.get("origin")
    if origin and origin != str(request.base_url).rstrip("/"):
        return JSONResponse(status_code=403, content={"detail": "Cross-origin access is disabled."})
    path = request.url.path.removeprefix("/api")
    if request.method == "POST":
        category = None
        if re.search(r"/assistant/conversations/\d+/messages(?:/stream)?$", path):
            category = "assistant"
        elif path.startswith("/interview/") or path in {"/code/hint", "/code/review", "/code/explain-error", "/code/generate", "/generate", "/generate/cv", "/generate/pdf", "/generate/ats-check", "/generate/cover-letter", "/generate/spot-edit", "/tracker/fetch-job-details"} or re.search(r"/tracker/\d+/generate-(pdf|cover-letter)$", path):
            category = "generation"
        if category and not capabilities()[category]:
            return JSONResponse(status_code=409, content={"detail": "Use Copy agent prompt to run this task in your CLI agent, then save its result with cv-tailor. Built-in API AI is optional.", "code": "agent_handoff_required"})
    # Next's client router can request a full RSC payload at the page URL,
    # including fallback navigation after segment prefetch. StaticFiles would
    # otherwise return HTML and leave the old page mounted indefinitely.
    if request.method == "GET" and request.headers.get("rsc") == "1" and not request.url.path.startswith("/api/"):
        root = assets_dir().resolve()
        payload = (root / request.url.path.lstrip("/") / "index.txt").resolve()
        if payload.is_relative_to(root) and payload.is_file():
            return FileResponse(payload, media_type="text/x-component")
    return await call_next(request)

app.mount("/api", api)
from cv_tailor.dashboard import assets_dir
if assets_dir().joinpath("index.html").exists():
    app.mount("/", StaticFiles(directory=assets_dir(), html=True), name="dashboard")
else:
    @app.get("/")
    def missing_dashboard():
        return {"message": "Install the optional dashboard with cv-tailor dashboard install", "api": "/api/docs"}
