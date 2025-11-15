"""Command-line interface for the watchdog utility."""
from __future__ import annotations

import argparse

from . import doctor, installer, sessions


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

    show_parser = sub.add_parser("show", help="Display a recorded session by id.")
    show_parser.add_argument("id", type=int, help="Numeric id shown in `watchdog sessions`.")

    search_parser = sub.add_parser("search", help="Search session logs for a keyword.")
    search_parser.add_argument("keyword", help="Keyword to search for.")

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    commands = {
        "install": installer.install,
        "uninstall": installer.uninstall,
        "sessions": sessions.list_sessions,
        "show": lambda: sessions.show_session(args.id),
        "last": sessions.show_last_session,
        "search": lambda: sessions.search_sessions(args.keyword),
        "doctor": doctor.run_checks,
    }

    handler = commands.get(args.command)
    if handler is None:
        parser.error(f"Unknown command: {args.command}")
    handler()


if __name__ == "__main__":  # pragma: no cover - manual invocation helper
    main()
