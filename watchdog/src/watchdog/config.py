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
    "if [ -t 1 ] && [ -z \"$WATCHDOG_ACTIVE\" ]; then\n"
    "    export WATCHDOG_ACTIVE=1\n"
    "    mkdir -p \"$HOME/.watchdog/logs\"\n"
    "    script -af \"$HOME/.watchdog/logs/$(date +%Y%m%d-%H%M%S).log\"\n"
    "    exit\n"
    "fi\n"
    f"{END_MARKER}\n"
)
