"""Setup and teardown helpers for installing the watchdog snippet."""
from __future__ import annotations

from . import config


def _read_bashrc() -> str:
    if config.BASHRC_PATH.exists():
        return config.BASHRC_PATH.read_text(encoding="utf-8")
    return ""


def _write_bashrc(content: str) -> None:
    config.BASHRC_PATH.write_text(content, encoding="utf-8")


def install() -> None:
    """Create log directories and inject the watchdog snippet."""
    config.LOG_DIR.mkdir(parents=True, exist_ok=True)
    config.BASHRC_PATH.parent.mkdir(parents=True, exist_ok=True)

    bashrc_content = _read_bashrc()
    if config.START_MARKER in bashrc_content:
        print("Watchdog snippet already present in ~/.bashrc.")
        return

    addition = config.SNIPPET
    if bashrc_content:
        prefix = "" if bashrc_content.endswith("\n") else "\n"
        addition = f"{prefix}{config.SNIPPET}"

    with config.BASHRC_PATH.open("a", encoding="utf-8") as bashrc:
        bashrc.write(addition)

    print("Installed. Open a new terminal to start logging.")


def uninstall() -> None:
    """Remove the watchdog snippet from ~/.bashrc."""
    if not config.BASHRC_PATH.exists():
        print("No ~/.bashrc file found; nothing to uninstall.")
        return

    cleaned, removed = _remove_snippet(_read_bashrc())
    if not removed:
        print("Watchdog snippet not found; nothing changed.")
        return

    _write_bashrc(cleaned)
    print("Watchdog snippet removed.")


def _remove_snippet(content: str) -> tuple[str, bool]:
    lines = content.splitlines()
    result: list[str] = []
    removing = False
    removed = False

    for line in lines:
        if not removing and line.strip() == config.START_MARKER:
            removing = True
            removed = True
            continue
        if removing and line.strip() == config.END_MARKER:
            removing = False
            continue
        if not removing:
            result.append(line)

    if removing:
        removed = True

    cleaned = "\n".join(result)
    if cleaned and not cleaned.endswith("\n"):
        cleaned += "\n"

    return cleaned, removed
