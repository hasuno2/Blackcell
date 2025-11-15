# Blackcell

Blackcell houses **watchdog**, a Python CLI that hooks into your login shell and records every interactive bash session for later review.

## Repository layout
- `watchdog/` – source code and packaging metadata for the watchdog CLI.

## Getting started

```bash
pip install -e watchdog      # install watchdog locally
watchdog install             # append the snippet to ~/.bashrc
watchdog sessions            # list recorded sessions
watchdog show 1              # inspect session id 1
watchdog uninstall           # remove the snippet
```

If you prefer not to install the package, run the CLI directly from the repo with `PYTHONPATH=watchdog/src python -m watchdog.cli <command>`.

## How it works

1. `watchdog install` creates `~/.watchdog/logs` and appends a small block to `~/.bashrc`.
2. New shells notice the block, set `WATCHDOG_ACTIVE=1`, and start `script -af ~/.watchdog/logs/<timestamp>.log`.
3. When a terminal closes, the logging session ends, leaving behind a readable log file ready for `watchdog sessions` / `watchdog show <id>`.
