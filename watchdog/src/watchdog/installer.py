"""Setup and teardown helpers for installing the watchdog snippet."""
from __future__ import annotations

from . import config


def _read_bashrc() -> str:
    if config.BASHRC_PATH.exists():
        return config.BASHRC_PATH.read_text(encoding="utf-8")
    return ""


def _write_bashrc(content: str) -> None:
    config.BASHRC_PATH.write_text(content, encoding="utf-8")


def _inject_snippet(content: str) -> str:
    if not content:
        return config.SNIPPET

    lines = content.splitlines(keepends=True)
    insert_at = len(lines)
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            insert_at = idx
            break

    if lines and insert_at > 0 and not lines[insert_at - 1].endswith(("\n", "\r")):
        lines.insert(insert_at, "\n")
        insert_at += 1

    lines.insert(insert_at, config.SNIPPET)

    new_content = "".join(lines)
    if not new_content.endswith("\n"):
        new_content += "\n"
    return new_content


def install() -> None:
    """Create log directories and inject the watchdog snippet."""
    config.LOG_DIR.mkdir(parents=True, exist_ok=True)
    config.BASHRC_PATH.parent.mkdir(parents=True, exist_ok=True)

    bashrc_content = _read_bashrc()
    if config.START_MARKER in bashrc_content:
        print("Watchdog snippet already present in ~/.bashrc.")
        return

    updated = _inject_snippet(bashrc_content)
    _write_bashrc(updated)
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
