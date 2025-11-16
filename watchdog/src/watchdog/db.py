"""Lightweight SQLite helpers for structured watchdog logs."""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
import sqlite3
from typing import Iterable, Iterator, Sequence

from . import config

DB_PATH = config.BASE_DIR / "watchdog.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT,
    command TEXT NOT NULL,
    output TEXT,
    session TEXT
);
"""

INDEXES = (
    "CREATE INDEX IF NOT EXISTS idx_logs_ts ON logs(ts)",
    "CREATE INDEX IF NOT EXISTS idx_logs_session ON logs(session)",
)


def _ensure_db(reset: bool = False) -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        if reset:
            conn.execute("DROP TABLE IF EXISTS logs")
        conn.execute(SCHEMA)
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


def insert_log(*, session: str, ts: str, command: str, output: str = "") -> None:
    """Insert a single log entry."""
    if not command.strip():
        return
    with _connection() as conn:
        conn.execute(
            "INSERT INTO logs (ts, command, output, session) VALUES (?, ?, ?, ?)",
            (ts, command, output, session),
        )


def insert_many(rows: Iterable[Sequence[str]]) -> None:
    """Bulk insert log entries as (ts, command, output, session) tuples."""
    rows = list(rows)
    if not rows:
        return
    with _connection() as conn:
        conn.executemany(
            "INSERT INTO logs (ts, command, output, session) VALUES (?, ?, ?, ?)",
            rows,
        )


def search(
    query: str | None = None,
    after: str | None = None,
    before: str | None = None,
    session: str | None = None,
) -> list[tuple[str | None, str, str | None, str | None]]:
    """Return matching log entries."""
    clauses: list[str] = []
    params: list[str] = []

    if query:
        clauses.append("(command LIKE ? OR output LIKE ?)")
        like = f"%{query}%"
        params.extend([like, like])
    if after:
        clauses.append("(ts IS NULL OR ts >= ?)")
        params.append(after)
    if before:
        clauses.append("(ts IS NULL OR ts <= ?)")
        params.append(before)
    if session:
        clauses.append("session = ?")
        params.append(session)

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    sql = (
        f"SELECT ts, command, output, session FROM logs {where} "
        "ORDER BY CASE WHEN ts IS NULL THEN 1 ELSE 0 END, ts DESC, id DESC"
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
        ORDER BY CASE WHEN MIN(ts) IS NULL THEN 1 ELSE 0 END, MIN(ts) DESC
    """
    with _connection() as conn:
        cursor = conn.execute(sql)
        return cursor.fetchall()


def latest_entries(limit: int = 50) -> list[tuple[str | None, str, str | None, str | None]]:
    """Fetch the most recent entries for quick inspection."""
    with _connection() as conn:
        cursor = conn.execute(
            """
            SELECT ts, command, output, session
            FROM logs
            ORDER BY CASE WHEN ts IS NULL THEN 1 ELSE 0 END, ts DESC, id DESC
            LIMIT ?
            """,
            (limit,),
        )
        return cursor.fetchall()
