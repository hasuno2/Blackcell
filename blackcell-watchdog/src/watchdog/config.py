"""Configuration helpers for the watchdog CLI."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable
import os

HOME = Path(os.path.expanduser("~"))
BASE_DIR = HOME / ".watchdog"
LOG_DIR = BASE_DIR / "logs"

START_MARKER = "# >>> WATCHDOG START >>>"
END_MARKER = "# <<< WATCHDOG END <<<"


@dataclass(frozen=True)
class ShellConfig:
    name: str
    rc_path: Path
    snippet_builder: Callable[[], str]


def _bash_snippet() -> str:
    return (
        f"{START_MARKER}\n"
        "if [ -t 1 ] && [ -z \"$WATCHDOG_ACTIVE\" ] && [ \"${SHELL##*/}\" = \"bash\" ]; then\n"
        "    case \"$-\" in\n"
        "    *i*) ;;\n"
        "    *) return ;;\n"
        "    esac\n"
        "    export WATCHDOG_ACTIVE=1\n"
        "    LOG_ROOT=\"${WATCHDOG_LOG_ROOT:-$HOME/.watchdog/logs}\"\n"
        "    LOGDIR=\"$LOG_ROOT/$(date +%Y/%m/%d)\"\n"
        "    mkdir -p \"$LOGDIR\"\n"
        "    MAXSIZE=\"${WATCHDOG_MAX_LOG_SIZE:-5000000}\"\n"
        "    find \"$LOG_ROOT\" -type f -size +\"${MAXSIZE}\"c -delete >/dev/null 2>&1 || true\n"
        "    TTY_NAME=\"$(tty 2>/dev/null | tr '/' '_' || echo 'notty')\"\n"
        "    SHELL_NAME=\"${SHELL##*/}\"\n"
        "    SESSION_NAME=\"$(date +%Y%m%d-%H%M%S)-${TTY_NAME}-${SHELL_NAME}\"\n"
        "    export WATCHDOG_SESSION=\"$SESSION_NAME\"\n"
        "    export WATCHDOG_LAST_HISTCMD=\"$HISTCMD\"\n"
        "    LOGFILE=\"$LOGDIR/${SESSION_NAME}.log\"\n"
        "    WATCHDOG_PROMPT_COMMAND='if [ \"$WATCHDOG_LAST_HISTCMD\" != \"$HISTCMD\" ]; then watchdog _realtime_log \"$(history 1)\"; WATCHDOG_LAST_HISTCMD=\"$HISTCMD\"; fi'\n"
        "    if [ -n \"$PROMPT_COMMAND\" ]; then\n"
        "        WATCHDOG_PROMPT_COMMAND=\"$WATCHDOG_PROMPT_COMMAND; $PROMPT_COMMAND\"\n"
        "    fi\n"
        "    export PROMPT_COMMAND=\"$WATCHDOG_PROMPT_COMMAND\"\n"
        "    script -af \"$LOGFILE\"\n"
        "    exit\n"
        "fi\n"
        f"{END_MARKER}\n"
    )


def _zsh_snippet() -> str:
    return (
        f"{START_MARKER}\n"
        "if [[ -t 1 && -z \"$WATCHDOG_ACTIVE\" && \"${SHELL##*/}\" = \"zsh\" ]]; then\n"
        "    case \"$-\" in\n"
        "    *i*) ;;\n"
        "    *) return ;;\n"
        "    esac\n"
        "    export WATCHDOG_ACTIVE=1\n"
        "    LOG_ROOT=\"${WATCHDOG_LOG_ROOT:-$HOME/.watchdog/logs}\"\n"
        "    LOGDIR=\"$LOG_ROOT/$(date +%Y/%m/%d)\"\n"
        "    mkdir -p \"$LOGDIR\"\n"
        "    MAXSIZE=\"${WATCHDOG_MAX_LOG_SIZE:-5000000}\"\n"
        "    find \"$LOG_ROOT\" -type f -size +\"${MAXSIZE}\"c -delete >/dev/null 2>&1 || true\n"
        "    TTY_NAME=\"$(tty 2>/dev/null | tr '/' '_' || echo 'notty')\"\n"
        "    SHELL_NAME=\"${SHELL##*/}\"\n"
        "    SESSION_NAME=\"$(date +%Y%m%d-%H%M%S)-${TTY_NAME}-${SHELL_NAME}\"\n"
        "    export WATCHDOG_SESSION=\"$SESSION_NAME\"\n"
        "    export WATCHDOG_LAST_COMMAND=\"\"\n"
        "    LOGFILE=\"$LOGDIR/${SESSION_NAME}.log\"\n"
        "    typeset -ga precmd_functions\n"
        "    function __watchdog_precmd() {\n"
        "        local cmd\n"
        "        cmd=\"$(fc -ln -1 2>/dev/null | tail -n 1 | sed -e 's/^[[:space:]]*//')\"\n"
        "        if [[ -n \"$cmd\" && \"$WATCHDOG_LAST_COMMAND\" != \"$cmd\" ]]; then\n"
        "            WATCHDOG_LAST_COMMAND=\"$cmd\"\n"
        "            watchdog _realtime_log \"$cmd\"\n"
        "        fi\n"
        "    }\n"
        "    if [[ -z \"${precmd_functions[(r)__watchdog_precmd]}\" ]]; then\n"
        "        precmd_functions+=(__watchdog_precmd)\n"
        "    fi\n"
        "    script -af \"$LOGFILE\"\n"
        "    exit\n"
        "fi\n"
        f"{END_MARKER}\n"
    )


def _fish_snippet() -> str:
    return (
        f"{START_MARKER}\n"
        "if status --is-interactive; and test -z \"$WATCHDOG_ACTIVE\"; and test (basename \"$SHELL\") = \"fish\"\n"
        "    set -gx WATCHDOG_ACTIVE 1\n"
        "    set -l log_root \"$HOME/.watchdog/logs\"\n"
        "    if set -q WATCHDOG_LOG_ROOT\n"
        "        set log_root $WATCHDOG_LOG_ROOT\n"
        "    end\n"
        "    set -l date_folder (date \"+%Y/%m/%d\")\n"
        "    set -l log_dir \"$log_root/$date_folder\"\n"
        "    mkdir -p $log_dir\n"
        "    set -l max_size 5000000\n"
        "    if set -q WATCHDOG_MAX_LOG_SIZE\n"
        "        set max_size $WATCHDOG_MAX_LOG_SIZE\n"
        "    end\n"
        "    set -l size_flag (string join \"\" \"+\" $max_size \"c\")\n"
        "    find $log_root -type f -size $size_flag -delete >/dev/null 2>&1; or true\n"
        "    set -l tty_name (tty 2>/dev/null | string replace -a \"/\" \"_\" )\n"
        "    if test -z \"$tty_name\"\n"
        "        set tty_name \"notty\"\n"
        "    end\n"
        "    set -l shell_name (basename \"$SHELL\")\n"
        "    set -l timestamp (date \"+%Y%m%d-%H%M%S\")\n"
        "    set -l session_name \"$timestamp-$tty_name-$shell_name\"\n"
        "    set -gx WATCHDOG_SESSION $session_name\n"
        "    set -l log_file \"$log_dir/$session_name.log\"\n"
        "    functions -q __watchdog_postexec; and functions -e __watchdog_postexec\n"
        "    function __watchdog_postexec --on-event fish_postexec\n"
        "        set -l last_cmd (history --max=1 | string trim)\n"
        "        if test -n \"$last_cmd\"\n"
        "            watchdog _realtime_log \"$last_cmd\"\n"
        "        end\n"
        "    end\n"
        "    script -af \"$log_file\"\n"
        "    exit\n"
        "end\n"
        f"{END_MARKER}\n"
    )


SHELL_CONFIGS: dict[str, ShellConfig] = {
    "bash": ShellConfig("bash", HOME / ".bashrc", _bash_snippet),
    "zsh": ShellConfig("zsh", HOME / ".zshrc", _zsh_snippet),
    "fish": ShellConfig("fish", HOME / ".config" / "fish" / "config.fish", _fish_snippet),
}


def detect_shell() -> str | None:
    """Detect the user's shell type."""
    override = os.environ.get("WATCHDOG_SHELL")
    if override:
        name = Path(override).name.lower()
        if name in SHELL_CONFIGS:
            return name
    shell = os.environ.get("SHELL", "")
    name = Path(shell).name.lower()
    if name in SHELL_CONFIGS:
        return name
    return None


def rc_path_for(shell: str) -> Path:
    """Return the RC file path for the provided shell type."""
    return SHELL_CONFIGS[shell].rc_path


def snippet_for(shell: str) -> str:
    """Return the snippet contents for the provided shell type."""
    return SHELL_CONFIGS[shell].snippet_builder()
