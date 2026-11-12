"""Optional localhost HTTP adapter and static dashboard server."""
import os
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

from cv_tailor.routers import database_routes, generate_routes, tracker_routes, interview_routes, code_routes, presets_routes, scraper_routes, assistant_routes, workspace_routes, feeder_routes, resume_routes
for router in (workspace_routes, database_routes, generate_routes, tracker_routes, interview_routes, code_routes, presets_routes, scraper_routes, assistant_routes, feeder_routes, resume_routes):
    api.include_router(router.router)

@api.get("/health")
def health():
    return {"status": "ok"}

app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None)

@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    from fastapi.responses import Response
    return Response(status_code=204)

@app.get("/workspace")
def root_workspace():
    from cv_tailor.routers.workspace_routes import workspace_status
    return workspace_status()

@app.get("/preferences")
def root_preferences():
    from cv_tailor.routers.workspace_routes import preferences
    return preferences()

@app.middleware("http")
async def local_access(request: Request, call_next):
    # Detect cloud deployment (Render, Docker container, external Postgres, or custom origins)
    is_cloud = bool(
        os.getenv("RENDER")
        or os.getenv("PORT")
        or (os.getenv("DATABASE_URL") and not os.getenv("DATABASE_URL", "").startswith("sqlite"))
        or os.getenv("ALLOWED_ORIGINS")
        or os.getenv("ENVIRONMENT") == "production"
    )

    if not is_cloud:
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
    allowed_origins = {
        str(request.base_url).rstrip("/"),
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:8005",
        "http://127.0.0.1:8005",
        "https://jobs.dealos.in",
        "http://jobs.dealos.in",
        "https://dealos.in",
    }
    env_origins = os.getenv("ALLOWED_ORIGINS")
    if env_origins:
        for o in env_origins.split(","):
            cleaned = o.strip()
            if cleaned:
                allowed_origins.add(cleaned)

    origin_allowed = False
    if origin:
        if "*" in allowed_origins or origin in allowed_origins:
            origin_allowed = True
        elif is_cloud and (origin.endswith(".dealos.in") or origin.endswith(".vercel.app") or origin.endswith(".onrender.com")):
            origin_allowed = True

    if origin and not origin_allowed and not is_cloud:
        return JSONResponse(status_code=403, content={"detail": "Cross-origin access is disabled."})

    cors_origin = origin if (origin_allowed or is_cloud) else (origin if origin in allowed_origins else None)

    if request.method == "OPTIONS":
        opt_res = Response(status_code=204)
        if cors_origin:
            opt_res.headers["Access-Control-Allow-Origin"] = cors_origin
            opt_res.headers["Access-Control-Allow-Credentials"] = "true"
            opt_res.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
            opt_res.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With, X-Auto-Fit-Fallback"
        return opt_res

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

    response = await call_next(request)
    if cors_origin:
        response.headers["Access-Control-Allow-Origin"] = cors_origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With, X-Auto-Fit-Fallback"
    return response

app.mount("/api", api)
from cv_tailor.dashboard import assets_dir
if assets_dir().joinpath("index.html").exists():
    app.mount("/", StaticFiles(directory=assets_dir(), html=True), name="dashboard")
else:
    @app.get("/")
    def missing_dashboard():
        return {"message": "Install the optional dashboard with cv-tailor dashboard install", "api": "/api/docs"}
