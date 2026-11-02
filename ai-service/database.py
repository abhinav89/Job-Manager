from contextvars import ContextVar, Token
import logging
from time import perf_counter

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/cv_tailor")
logger = logging.getLogger("cv_tailor.database")
request_path: ContextVar[str] = ContextVar("request_path", default="background")

def normalize_database_url(url: str) -> str:
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)

    parsed = urlsplit(url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    host = parsed.hostname or ""

    if "supabase.co" in host and "sslmode" not in query:
        query["sslmode"] = "require"

    return urlunsplit(parsed._replace(query=urlencode(query)))

DATABASE_URL = normalize_database_url(DATABASE_URL)

def positive_int_env(name: str, default: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except ValueError:
        return default
    return value if value > 0 else default


def nonnegative_int_env(name: str, default: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except ValueError:
        return default
    return value if value >= 0 else default


def set_request_path(path: str) -> Token[str]:
    return request_path.set(path)


def reset_request_path(token: Token[str]) -> None:
    request_path.reset(token)


engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=positive_int_env("DB_POOL_SIZE", 5),
    max_overflow=nonnegative_int_env("DB_MAX_OVERFLOW", 5),
    pool_recycle=positive_int_env("DB_POOL_RECYCLE_SECONDS", 1800),
    pool_timeout=positive_int_env("DB_POOL_TIMEOUT_SECONDS", 5),
    connect_args={
        "connect_timeout": positive_int_env("DB_CONNECT_TIMEOUT_SECONDS", 5),
        "application_name": "cv_tailor",
        "options": f"-c statement_timeout={positive_int_env('DB_STATEMENT_TIMEOUT_MS', 15000)}",
    },
)

SLOW_QUERY_MS = positive_int_env("DB_SLOW_QUERY_MS", 500)


@event.listens_for(engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    context.cv_tailor_started_at = perf_counter()


@event.listens_for(engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    started_at = getattr(context, "cv_tailor_started_at", None)
    if started_at is None:
        return
    duration_ms = (perf_counter() - started_at) * 1000
    if duration_ms < SLOW_QUERY_MS:
        return
    statement_shape = " ".join(statement.split())[:500]
    logger.warning(
        "slow_db_query duration_ms=%.1f route=%s statement=%s",
        duration_ms,
        request_path.get(),
        statement_shape,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    from schema_changes import apply_schema_changes
    apply_schema_changes(engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
