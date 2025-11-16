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
    if not config.BASHRC_PATH.exists():
        return CheckResult(
            "Watchdog snippet present in ~/.bashrc",
            False,
            "No ~/.bashrc file found.",
        )

    try:
        content = config.BASHRC_PATH.read_text(encoding="utf-8")
    except OSError as exc:
        return CheckResult("Watchdog snippet present in ~/.bashrc", False, f"Failed to read ~/.bashrc: {exc}")

    present = config.START_MARKER in content and config.END_MARKER in content
    detail = "Markers detected." if present else "Markers missing."
    return CheckResult("Watchdog snippet present in ~/.bashrc", present, detail)


def _check_shell() -> CheckResult:
    shell = os.environ.get("SHELL", "")
    shell_name = shell.rsplit("/", 1)[-1] if shell else ""
    is_bash = shell_name.startswith("bash")
    detail = shell or "SHELL environment variable not set."
    return CheckResult("Current shell reports as bash", is_bash, detail)


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


def run_checks() -> None:
    """Run the doctor checks and print a short report."""
    checks = [
        _check_log_dir(),
        _check_snippet_present(),
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
