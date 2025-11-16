"""Lightweight SQLite helpers for structured watchdog logs."""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
import sqlite3
from typing import Iterable, Iterator, Sequence

from . import config

DB_PATH = config.BASE_DIR / "watchdog.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    command TEXT NOT NULL,
    output TEXT,
    session TEXT
);
"""

INDEXES = (
    "CREATE INDEX IF NOT EXISTS idx_logs_ts ON logs(ts)",
    "CREATE INDEX IF NOT EXISTS idx_logs_session ON logs(session)",
)


def _timestamp_from_session(session: str | None) -> str | None:
    if not session:
        return None
    stem = Path(session).stem
    parts = stem.split("-")
    if len(parts) < 2:
        return None
    candidate = f"{parts[0]}-{parts[1]}"
    try:
        return datetime.strptime(candidate, "%Y%m%d-%H%M%S").isoformat()
    except ValueError:
        return None


def _ensure_ts_value(ts: str | None, session: str | None) -> str:
    if ts:
        return ts
    derived = _timestamp_from_session(session)
    if derived:
        return derived
    return datetime.now().isoformat(timespec="seconds")


def _upgrade_schema(conn: sqlite3.Connection) -> None:
    """Ensure required columns exist and backfill timestamps."""
    cursor = conn.execute("PRAGMA table_info(logs)")
    columns = {row[1] for row in cursor.fetchall()}
    if not columns:
        return

    if "ts" not in columns:
        conn.execute("ALTER TABLE logs ADD COLUMN ts TEXT")

    rows = conn.execute("SELECT id, session FROM logs WHERE ts IS NULL OR ts = ''").fetchall()
    for row_id, session in rows:
        conn.execute(
            "UPDATE logs SET ts = ? WHERE id = ?",
            (_ensure_ts_value(None, session), row_id),
        )


def _ensure_db(reset: bool = False) -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        if reset:
            conn.execute("DROP TABLE IF EXISTS logs")
        conn.execute(SCHEMA)
        _upgrade_schema(conn)
        for stmt in INDEXES:
            conn.execute(stmt)


@contextmanager
def _connection() -> Iterator[sqlite3.Connection]:
    _ensure_db()
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db(reset: bool = False) -> None:
    """Initialize the database schema."""
    _ensure_db(reset=reset)


def insert_log(*, session: str, ts: str | None, command: str, output: str = "") -> None:
    """Insert a single log entry."""
    if not command.strip():
        return
    normalized_ts = _ensure_ts_value(ts, session)
    with _connection() as conn:
        conn.execute(
            "INSERT INTO logs (ts, command, output, session) VALUES (?, ?, ?, ?)",
            (normalized_ts, command, output, session),
        )


def insert_many(rows: Iterable[Sequence[str | None]]) -> None:
    """Bulk insert log entries as (ts, command, output, session) tuples."""
    prepared: list[tuple[str, str, str, str | None]] = []
    for ts, command, output, session in rows:
        if not command.strip():
            continue
        prepared.append(
            (
                _ensure_ts_value(ts, session),
                command,
                (output or ""),
                session,
            )
        )

    if not prepared:
        return

    with _connection() as conn:
        conn.executemany(
            "INSERT INTO logs (ts, command, output, session) VALUES (?, ?, ?, ?)",
            prepared,
        )


def search(
    query: str | None = None,
    after: str | None = None,
    before: str | None = None,
    session: str | None = None,
) -> list[tuple[str, str, str | None, str | None]]:
    """Return matching log entries."""
    clauses: list[str] = []
    params: list[str] = []

    if query:
        clauses.append("(command LIKE ? OR output LIKE ?)")
        like = f"%{query}%"
        params.extend([like, like])
    if after:
        clauses.append("ts >= ?")
        params.append(after)
    if before:
        clauses.append("ts <= ?")
        params.append(before)
    if session:
        clauses.append("session = ?")
        params.append(session)

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    sql = (
        f"SELECT ts, command, output, session FROM logs {where} "
        "ORDER BY ts DESC, id DESC"
    )

    with _connection() as conn:
        cursor = conn.execute(sql, params)
        return cursor.fetchall()


def list_sessions() -> list[tuple[str | None, str | None, int]]:
    """Return summary information for sessions."""
    sql = """
        SELECT
            session,
            MIN(ts),
            COUNT(*)
        FROM logs
        GROUP BY session
        ORDER BY MIN(ts) DESC
    """
    with _connection() as conn:
        cursor = conn.execute(sql)
        return cursor.fetchall()


def latest_entries(limit: int = 50) -> list[tuple[str, str, str | None, str | None]]:
    """Fetch the most recent entries for quick inspection."""
    with _connection() as conn:
        cursor = conn.execute(
            """
            SELECT ts, command, output, session
            FROM logs
            ORDER BY ts DESC, id DESC
            LIMIT ?
            """,
            (limit,),
        )
        return cursor.fetchall()


def fetch_all_entries() -> list[tuple[str, str, str | None, str | None]]:
    """Fetch every stored log entry, newest first."""
    _ensure_db()
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.execute(
            """
            SELECT ts, command, output, session
            FROM logs
            ORDER BY ts DESC, id DESC
            """
        )
        return cursor.fetchall()
    finally:
        conn.close()
