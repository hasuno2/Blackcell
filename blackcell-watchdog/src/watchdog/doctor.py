"""System checks for verifying a watchdog installation."""
from __future__ import annotations

from dataclasses import dataclass
import os
import shutil

from . import config, db, sessions


@dataclass
class CheckResult:
    description: str
    ok: bool
    detail: str = ""


def _check_log_dir() -> CheckResult:
    exists = config.LOG_DIR.exists()
    detail = str(config.LOG_DIR)
    return CheckResult("Log directory exists", exists, detail)


def _check_snippet_present() -> CheckResult:
    shell = config.detect_shell()
    if not shell:
        return CheckResult(
            "Watchdog snippet present for current shell",
            False,
            "Unsupported or undetected shell.",
        )

    rc_path = config.rc_path_for(shell)
    if not rc_path.exists():
        return CheckResult(
            f"Watchdog snippet present in {rc_path}",
            False,
            f"No RC file at {rc_path}.",
        )

    try:
        content = rc_path.read_text(encoding="utf-8")
    except OSError as exc:
        return CheckResult(f"Watchdog snippet present in {rc_path}", False, f"Failed to read RC file: {exc}")

    present = config.START_MARKER in content and config.END_MARKER in content
    detail = "Markers detected." if present else "Markers missing."
    return CheckResult(f"Watchdog snippet present in {rc_path}", present, detail)


def _check_shell() -> CheckResult:
    shell_env = os.environ.get("SHELL", "")
    detected = config.detect_shell()
    if detected:
        return CheckResult("Supported shell detected", True, detected)
    detail = shell_env or "SHELL environment variable not set."
    return CheckResult("Supported shell detected (bash, zsh, fish)", False, detail)


def _check_script_binary() -> CheckResult:
    script_path = shutil.which("script")
    if script_path:
        return CheckResult("`script` binary available", True, script_path)
    return CheckResult("`script` binary available", False, "Command not found in PATH.")


def _check_latest_log() -> CheckResult:
    log = sessions.latest_log()
    if not log:
        return CheckResult("Recent log file exists", False, "No logs recorded yet.")

    size = log.stat().st_size
    ok = size > 0
    detail = f"{log} ({size} bytes)"
    return CheckResult("Recent log file exists", ok, detail)


def _check_database() -> CheckResult:
    try:
        db.init_db()
    except Exception as exc:  # pragma: no cover - defensive
        return CheckResult("SQLite database reachable", False, f"Failed to init: {exc}")

    exists = db.DB_PATH.exists()
    detail = str(db.DB_PATH)
    return CheckResult("SQLite database reachable", exists, detail)


def _check_shell_hook() -> CheckResult:
    shell = config.detect_shell()
    if not shell:
        return CheckResult("Shell hook configured", False, "Unsupported or undetected shell.")

    rc_path = config.rc_path_for(shell)
    if not rc_path.exists():
        return CheckResult("Shell hook configured", False, f"{rc_path} not found.")

    try:
        content = rc_path.read_text(encoding="utf-8")
    except OSError as exc:
        return CheckResult("Shell hook configured", False, f"Failed to read {rc_path}: {exc}")

    hook_markers = {
        "bash": "WATCHDOG_PROMPT_COMMAND",
        "zsh": "__watchdog_precmd",
        "fish": "__watchdog_postexec",
    }

    marker = hook_markers.get(shell, "watchdog _realtime_log")
    if marker in content:
        return CheckResult("Shell hook configured", True, f"{marker} detected in {rc_path}")
    return CheckResult("Shell hook configured", False, f"{marker} missing in {rc_path}")


def run_checks() -> None:
    """Run the doctor checks and print a short report."""
    checks = [
        _check_log_dir(),
        _check_snippet_present(),
        _check_shell_hook(),
        _check_shell(),
        _check_script_binary(),
        _check_latest_log(),
        _check_database(),
    ]
    total = len(checks)
    passed = 0

    for result in checks:
        status = "OK" if result.ok else "FAIL"
        detail = f" - {result.detail}" if result.detail else ""
        print(f"[{status}] {result.description}{detail}")
        if result.ok:
            passed += 1

    if passed == total:
        print("All checks passed. Watchdog looks healthy.")
    else:
        print(f"{passed}/{total} checks passed. Investigate the failures above.")
