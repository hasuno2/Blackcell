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
watchdog last                # instantly show the most recent session
watchdog search ssh          # grep across recorded sessions
watchdog doctor              # verify the install looks healthy
watchdog uninstall           # remove the snippet
```

If you prefer not to install the package, run the CLI directly from the repo with `PYTHONPATH=watchdog/src python -m watchdog.cli <command>`.

## How it works

1. `watchdog install` creates `~/.watchdog/logs` and injects a block near the top of `~/.bashrc`, before user commands run.
2. Interactive shells notice the block, set `WATCHDOG_ACTIVE=1`, and start `script -af ~/.watchdog/logs/YYYY/MM/DD/YYYYMMDD-HHMMSS-<tty>-<shell>.log`.
3. Each day gets its own folder, oversized (5MB+) logs are pruned on startup, and non-interactive shells return early so nested scripts stay quiet.
4. When a terminal closes, the logging session ends, leaving behind a readable log file ready for `watchdog sessions`, `watchdog show <id>`, `watchdog last`, or `watchdog search <keyword>`.
