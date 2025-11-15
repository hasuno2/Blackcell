"""Command-line interface for the watchdog utility."""
from __future__ import annotations

import argparse

from . import installer, sessions


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="watchdog",
        description="Log and review shell sessions.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("install", help="Install the watchdog shell snippet.")
    sub.add_parser("uninstall", help="Remove the watchdog shell snippet.")
    sub.add_parser("sessions", help="List recorded sessions.")

    show_parser = sub.add_parser("show", help="Display a recorded session by id.")
    show_parser.add_argument("id", type=int, help="Numeric id shown in `watchdog sessions`.")

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "install":
        installer.install()
    elif args.command == "uninstall":
        installer.uninstall()
    elif args.command == "sessions":
        sessions.list_sessions()
    elif args.command == "show":
        sessions.show_session(args.id)


if __name__ == "__main__":  # pragma: no cover - manual invocation helper
    main()
