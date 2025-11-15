"""Configuration helpers for the watchdog CLI."""
from pathlib import Path
import os

HOME = Path(os.path.expanduser("~"))
BASE_DIR = HOME / ".watchdog"
LOG_DIR = BASE_DIR / "logs"
BASHRC_PATH = HOME / ".bashrc"

START_MARKER = "# >>> WATCHDOG START >>>"
END_MARKER = "# <<< WATCHDOG END <<<"

SNIPPET = (
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
    "    script -af \"$LOGDIR/$(date +%Y%m%d-%H%M%S)-${TTY_NAME}-${SHELL_NAME}.log\"\n"
    "    exit\n"
    "fi\n"
    f"{END_MARKER}\n"
)
