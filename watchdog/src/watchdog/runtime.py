"""Helpers for recording real-time shell activity."""
from __future__ import annotations

from datetime import datetime
import os

from . import db


def _normalize_history_line(line: str) -> str:
    text = line.strip()
    if not text:
        return ""

    parts = text.split(maxsplit=1)
    if len(parts) == 2 and parts[0].isdigit():
        return parts[1].strip()
    return text


def record_history_line(raw_line: str) -> None:
    """Record a single history line emitted via PROMPT_COMMAND."""
    command = _normalize_history_line(raw_line)
    if not command:
        return

    session = os.environ.get("WATCHDOG_SESSION", "unknown")
    timestamp = datetime.now().isoformat(timespec="seconds")
    db.insert_log(session=session, ts=timestamp, command=command)
