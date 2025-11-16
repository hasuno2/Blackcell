"""Utilities for migrating raw watchdog logs into SQLite."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Iterable, Iterator

from . import config, db


def _session_name(path: Path) -> str:
    try:
        return str(path.relative_to(config.LOG_DIR))
    except ValueError:
        return path.name


def _session_timestamp(session: str) -> str | None:
    stem = Path(session).stem
    parts = stem.split("-")
    if len(parts) < 2:
        return None
    value = f"{parts[0]}-{parts[1]}"
    try:
        dt = datetime.strptime(value, "%Y%m%d-%H%M%S")
        return dt.isoformat()
    except ValueError:
        return None


def _parse_log(path: Path) -> Iterator[tuple[str, str, str, str]]:
    session = _session_name(path)
    session_ts = _session_timestamp(session)
    if session_ts is None:
        session_ts = datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds")
    command: str | None = None
    output_lines: list[str] = []

    try:
        handle = path.open("r", encoding="utf-8", errors="replace")
    except OSError:
        return

    with handle:
        for raw_line in handle:
            line = raw_line.rstrip("\n")
            if line.startswith("$ "):
                if command is not None:
                    yield (session_ts, command, "\n".join(output_lines).rstrip(), session)
                command = line[2:].strip()
                output_lines = []
            else:
                if command is None:
                    continue
                output_lines.append(line)

        if command is not None:
            yield (session_ts, command, "\n".join(output_lines).rstrip(), session)


def _log_paths() -> Iterable[Path]:
    if not config.LOG_DIR.exists():
        return []
    return sorted(config.LOG_DIR.rglob("*.log"))


def migrate(*, reset: bool = False) -> None:
    """Rebuild the SQLite database by parsing existing text logs."""
    db.init_db(reset=reset)
    total_entries = 0
    total_sessions = 0

    for path in _log_paths():
        entries = list(_parse_log(path))
        if not entries:
            continue
        db.insert_many(entries)
        total_entries += len(entries)
        total_sessions += 1

    print(
        f"Migration complete. Imported {total_entries} commands from {total_sessions} session logs "
        f"into {db.DB_PATH}."
    )
