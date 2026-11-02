"""One local workspace shared by the CLI and the optional dashboard."""
import os
from pathlib import Path


def data_dir() -> Path:
    return Path(os.environ.get("CV_TAILOR_HOME", Path.home() / ".cv-tailor")).expanduser().resolve()


def configure(directory=None):
    if directory:
        os.environ["CV_TAILOR_HOME"] = str(Path(directory).expanduser().resolve())
    from dotenv import load_dotenv
    load_dotenv(data_dir() / ".env")
    os.environ.setdefault("EXECUTION_BACKEND", "local")
    os.environ.setdefault("ENVIRONMENT", "development")


def ai_enabled() -> bool:
    return os.getenv("AI_MODE", "external").lower() == "api"


def capabilities() -> dict:
    api = ai_enabled()
    return {
        "mode": "api" if api else "external",
        "generation": api and bool(os.getenv("GEMINI_API_KEY") if os.getenv("AI_PROVIDER", "gemini") == "gemini" else os.getenv("OPENAI_API_KEY")),
        "assistant": api and bool(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")),
        "research": api and bool(os.getenv("GEMINI_API_KEY")),
        "ranking": api and bool(os.getenv("JEV_API_KEY") or os.getenv("TYPESAFE_API_KEY")),
    }


def require_ai():
    if not ai_enabled():
        raise ValueError("AI_MODE=external: run this task in your CLI agent using context export, then import its result. API AI is optional; opt in with AI_MODE=api.")
