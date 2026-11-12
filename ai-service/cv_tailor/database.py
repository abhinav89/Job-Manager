"""Database configuration supporting both local SQLite and Cloud Postgres (Supabase)."""
import os
from contextvars import ContextVar
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from cv_tailor.config import configure, data_dir

configure()

# Default to local SQLite unless DATABASE_URL is provided (e.g. Supabase Postgres)
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///" + (data_dir() / "cv-tailor.sqlite3").as_posix()
elif DATABASE_URL.startswith("postgres://"):
    # SQLAlchemy 2.0 requires postgresql:// instead of postgres://
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

request_path = ContextVar("request_path", default="cli")
Base = declarative_base()


def make_engine(url):
    if url.startswith("sqlite"):
        result = create_engine(url, connect_args={"check_same_thread": False, "timeout": 5})
        @event.listens_for(result, "connect")
        def setup(connection, _):
            connection.execute("PRAGMA foreign_keys=ON")
            connection.execute("PRAGMA busy_timeout=5000")
        return result
    else:
        # Postgres (Supabase, Neon, etc.)
        return create_engine(
            url,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
            pool_recycle=300,
        )


engine = make_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def init_db():
    data_dir().mkdir(parents=True, exist_ok=True)
    if DATABASE_URL.startswith("sqlite"):
        from cv_tailor.schema_changes import apply_schema_changes
        apply_schema_changes(engine)
    else:
        # Create all tables on Postgres
        Base.metadata.create_all(bind=engine)


def get_db():
    with SessionLocal() as db:
        yield db


def set_request_path(path):
    return request_path.set(path)


def reset_request_path(token):
    request_path.reset(token)
