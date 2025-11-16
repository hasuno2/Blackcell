"""Setup and teardown helpers for installing the watchdog snippet."""
from __future__ import annotations

from pathlib import Path

from . import config


def _read_rc(path: Path) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def _write_rc(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _inject_snippet(content: str, snippet: str) -> str:
    if not content:
        return snippet

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

    lines.insert(insert_at, snippet)

    new_content = "".join(lines)
    if not new_content.endswith("\n"):
        new_content += "\n"
    return new_content


def install() -> None:
    """Create log directories and inject the watchdog snippet."""
    config.LOG_DIR.mkdir(parents=True, exist_ok=True)
    shell = config.detect_shell()
    if not shell:
        print("Could not detect a supported shell (bash, zsh, fish). Set WATCHDOG_SHELL to override.")
        return

    print(f"Detected shell: {shell}. If this looks wrong, set WATCHDOG_SHELL=<shell> and rerun.")
    rc_path = config.rc_path_for(shell)
    current = _read_rc(rc_path)
    if config.START_MARKER in current:
        print(f"Watchdog snippet already present in {rc_path}.")
        return

    updated = _inject_snippet(current, config.snippet_for(shell))
    _write_rc(rc_path, updated)
    if shell == "bash":
        _ensure_bash_profile_sources_bashrc()
    print(f"Installed snippet for {shell}. Open a new terminal to start logging.")


def uninstall() -> None:
    """Remove the watchdog snippet from all supported shell rc files."""
    removed_any = False
    for shell_cfg in config.SHELL_CONFIGS.values():
        if not shell_cfg.rc_path.exists():
            continue
        cleaned, removed = _remove_snippet(_read_rc(shell_cfg.rc_path))
        if removed:
            _write_rc(shell_cfg.rc_path, cleaned)
            print(f"Removed snippet from {shell_cfg.rc_path}.")
            removed_any = True

    if removed_any:
        print("Watchdog snippet removed.")
    else:
        print("Watchdog snippet not found; nothing changed.")


def _remove_snippet(content: str) -> tuple[str, bool]:
    lines = content.splitlines(keepends=True)
    start_idx = end_idx = None

    for idx, line in enumerate(lines):
        stripped = line.strip()
        if start_idx is None and stripped == config.START_MARKER:
            start_idx = idx
            continue
        if start_idx is not None and stripped == config.END_MARKER:
            end_idx = idx
            break

    if start_idx is None or end_idx is None:
        cleaned = content
        if cleaned and not cleaned.endswith("\n"):
            cleaned += "\n"
        return cleaned, False

    del lines[start_idx : end_idx + 1]
    cleaned = "".join(lines)
    if cleaned and not cleaned.endswith("\n"):
        cleaned += "\n"
    return cleaned, True


def _ensure_bash_profile_sources_bashrc() -> None:
    profile = config.HOME / ".bash_profile"
    source_line = 'if [ -f "$HOME/.bashrc" ]; then\n    source "$HOME/.bashrc"\nfi\n'
    marker = "# Added by Watchdog to ensure bash login shells load .bashrc"

    if profile.exists():
        try:
            content = profile.read_text(encoding="utf-8")
        except OSError:
            return
        if ".bashrc" in content:
            return
        addition = f"\n{marker}\n{source_line}"
        profile.write_text(content + addition, encoding="utf-8")
    else:
        profile.parent.mkdir(parents=True, exist_ok=True)
        profile.write_text(f"{marker}\n{source_line}", encoding="utf-8")
