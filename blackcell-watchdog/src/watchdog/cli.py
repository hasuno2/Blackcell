"""Command-line interface for the watchdog utility."""
from __future__ import annotations

import argparse

from . import doctor, installer, migrate, runtime, sessions


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="watchdog",
        description="Log and review shell sessions.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("install", help="Install the watchdog shell snippet.")
    sub.add_parser("uninstall", help="Remove the watchdog shell snippet.")
    sub.add_parser("sessions", help="List recorded sessions.")
    sub.add_parser("last", help="Show the most recent session log.")
    sub.add_parser("doctor", help="Run installation health checks.")
    sub.add_parser("tui", help="Launch the interactive Textual browser.")

    migrate_parser = sub.add_parser("migrate", help="Rebuild the SQLite database from raw logs.")
    migrate_parser.add_argument(
        "--reset",
        action="store_true",
        help="Drop and recreate the logs table before importing.",
    )

    show_parser = sub.add_parser("show", help="Display a recorded session by id.")
    show_parser.add_argument("id", type=int, help="Numeric id shown in `watchdog sessions`.")

    search_parser = sub.add_parser("search", help="Search session logs for a keyword.")
    search_parser.add_argument("keyword", help="Keyword to search for.")

    return parser


def main(argv: list[str] | None = None) -> None:
    import sys

    if argv is None:
        argv = sys.argv[1:]

    if argv and argv[0] == "_realtime_log":
        raw = argv[1] if len(argv) > 1 else ""
        runtime.record_history_line(raw)
        return

    parser = _build_parser()
    args = parser.parse_args(argv)

    def _launch_tui() -> None:
        from .tui import app as tui_app  # expensive import, keep local

        tui_app.run()

    commands = {
        "install": installer.install,
        "uninstall": installer.uninstall,
        "sessions": sessions.list_sessions,
        "show": lambda: sessions.show_session(args.id),
        "last": sessions.show_last_session,
        "search": lambda: sessions.search_sessions(args.keyword),
        "doctor": doctor.run_checks,
        "tui": _launch_tui,
        "migrate": lambda: migrate.migrate(reset=getattr(args, "reset", False)),
    }

    handler = commands.get(args.command)
    if handler is None:
        parser.error(f"Unknown command: {args.command}")
    handler()


if __name__ == "__main__":  # pragma: no cover - manual invocation helper
    main()
