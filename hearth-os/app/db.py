from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    pass


_engine: Engine | None = None
SessionLocal: sessionmaker[Session] | None = None


def ensure_sqlite_parent(url: str) -> None:
    if not url.startswith("sqlite"):
        return
    rest = url.split(":///", 1)[-1]
    if not rest or rest == ":memory:":
        return
    path = Path(rest)
    if not path.is_absolute():
        path = Path.cwd() / path
    path.parent.mkdir(parents=True, exist_ok=True)


def get_engine() -> Engine:
    global _engine, SessionLocal
    if _engine is None:
        settings = get_settings()
        ensure_sqlite_parent(settings.DATABASE_URL)
        connect_args = {}
        if settings.DATABASE_URL.startswith("sqlite"):
            connect_args["check_same_thread"] = False
        _engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)

        @event.listens_for(_engine, "connect")
        def _sqlite_pragmas(dbapi_conn, _connection_record):  # type: ignore[no-untyped-def]
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.close()

        SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False)
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    get_engine()
    assert SessionLocal is not None
    return SessionLocal


def reset_engine() -> None:
    global _engine, SessionLocal
    if _engine is not None:
        _engine.dispose()
    _engine = None
    SessionLocal = None


def db_writable() -> bool:
    """True only if a SQLite write+read round-trip succeeds."""
    try:
        engine = get_engine()
        with engine.begin() as conn:
            conn.execute(text("CREATE TABLE IF NOT EXISTS _health_ping (k INTEGER)"))
            conn.execute(text("DELETE FROM _health_ping"))
            conn.execute(text("INSERT INTO _health_ping (k) VALUES (1)"))
            row = conn.execute(text("SELECT k FROM _health_ping LIMIT 1")).fetchone()
        return bool(row and row[0] == 1)
    except Exception:
        return False
