"""Session discovery and viewing helpers."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sys

from . import config


def _sorted_logs() -> list[Path]:
    if not config.LOG_DIR.exists():
        return []
    return sorted(config.LOG_DIR.glob("*.log"), key=lambda path: path.stat().st_mtime)


def _timestamp_for(path: Path) -> datetime:
    try:
        return datetime.strptime(path.stem, "%Y%m%d-%H%M%S")
    except ValueError:
        return datetime.fromtimestamp(path.stat().st_mtime)


def list_sessions() -> None:
    """Display the recorded sessions sorted by modification time."""
    logs = _sorted_logs()
    if not logs:
        print(f"No sessions found. Logs directory: {config.LOG_DIR}")
        return

    header = f"{'ID':<5}{'Timestamp':<20}File"
    print(header)
    for idx, path in enumerate(logs, start=1):
        timestamp = _timestamp_for(path)
        print(f"{idx:<5}{timestamp:%Y-%m-%d %H:%M:%S}  {path.name}")


def show_session(session_id: int | str) -> None:
    """Display the contents of a session log by its numeric id."""
    logs = _sorted_logs()
    if not logs:
        print("No sessions recorded yet.")
        return

    try:
        idx = int(session_id)
    except (TypeError, ValueError):
        print("Session id must be an integer.")
        return

    if idx < 1 or idx > len(logs):
        print(f"Session id must be between 1 and {len(logs)}.")
        return

    session_file = logs[idx - 1]
    print(f"Showing session {idx}: {session_file.name}\n")
    with session_file.open("r", encoding="utf-8", errors="replace") as handle:
        for chunk in handle:
            sys.stdout.write(chunk)
