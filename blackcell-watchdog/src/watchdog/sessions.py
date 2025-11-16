"""Session discovery and viewing helpers."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sys

from . import config

GREEN = "\033[92m"
RESET = "\033[0m"
USE_COLOR = sys.stdout.isatty()


def _sorted_logs() -> list[Path]:
    if not config.LOG_DIR.exists():
        return []
    return sorted(config.LOG_DIR.rglob("*.log"), key=lambda path: path.stat().st_mtime)


def _timestamp_for(path: Path) -> datetime:
    stem_parts = path.stem.split("-")
    if len(stem_parts) >= 2:
        ts = f"{stem_parts[0]}-{stem_parts[1]}"
        try:
            return datetime.strptime(ts, "%Y%m%d-%H%M%S")
        except ValueError:
            pass
    return datetime.fromtimestamp(path.stat().st_mtime)


def _relative_name(path: Path) -> str:
    try:
        return str(path.relative_to(config.LOG_DIR))
    except ValueError:
        return path.name


def _display_session(logs: list[Path], idx: int) -> None:
    session_file = logs[idx - 1]
    print(f"Showing session {idx}: {_relative_name(session_file)}\n")
    with session_file.open("r", encoding="utf-8", errors="replace") as handle:
        for chunk in handle:
            print(chunk, end="")


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
        idx_text = f"{idx:<5}"
        if USE_COLOR:
            idx_text = f"{GREEN}{idx_text}{RESET}"
        print(f"{idx_text}{timestamp:%Y-%m-%d %H:%M:%S}  {_relative_name(path)}")


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

    _display_session(logs, idx)


def show_last_session() -> None:
    """Display the most recently modified session log."""
    logs = _sorted_logs()
    if not logs:
        print("No sessions recorded yet.")
        return
    _display_session(logs, len(logs))


def search_sessions(keyword: str) -> None:
    """Search across all sessions for the provided keyword."""
    if not keyword:
        print("Please provide a keyword to search for.")
        return

    logs = _sorted_logs()
    if not logs:
        print("No sessions recorded yet.")
        return

    matches = 0
    for path in logs:
        try:
            with path.open("r", encoding="utf-8", errors="replace") as handle:
                for line in handle:
                    if keyword in line:
                        print(f"{_relative_name(path)}: {line}", end="")
                        matches += 1
        except OSError as exc:
            print(f"Failed to read {_relative_name(path)}: {exc}")

    if matches == 0:
        print(f"No matches for '{keyword}'.")


def latest_log() -> Path | None:
    """Return the most recent log file if one exists."""
    logs = _sorted_logs()
    if not logs:
        return None
    return logs[-1]
