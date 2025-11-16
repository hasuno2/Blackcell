# Watchdog

Watchdog is a Python CLI that hooks into your interactive bash shells and records them for later review. It lives inside the [`Blackcell`](../README.md) umbrella repository as one of several utilities.

## Repository layout

```
watchdog/
|-- src/watchdog/      # CLI implementation
|-- pyproject.toml     # packaging metadata
|-- README.md          # this file
`-- .gitignore
```

The project uses the conventional `src/` layout. Editable installs (`pip install -e .`) must be executed from the `watchdog/` directory.

## Installation

```bash
cd watchdog
python -m venv .venv && source .venv/bin/activate  # optional but recommended
pip install -e .                                   # install watchdog locally
watchdog install                                   # append the snippet to ~/.bashrc
```

If you prefer not to install the package, run it directly with `PYTHONPATH=src python -m watchdog.cli <command>`.

## Usage

Common commands:

```bash
watchdog sessions            # list recorded sessions
watchdog show 1              # inspect session id 1
watchdog last                # instantly show the most recent session
watchdog search ssh          # grep across recorded sessions
watchdog doctor              # verify the install looks healthy
watchdog migrate --reset     # rebuild the SQLite index from raw logs
watchdog tui                 # launch the interactive Textual browser
watchdog uninstall           # remove the snippet
```

Run `watchdog --help` for the full command list.

### Textual TUI

```bash
cd watchdog
python -m venv .venv && source .venv/bin/activate
pip install -e .
watchdog tui      # or run `watchdog-tui`
```

## Configuration

By default logs are stored under `~/.watchdog/logs/YYYY/MM/DD`. Two environment variables let you customize behavior without editing the snippet:

- `WATCHDOG_LOG_ROOT` - override the root directory for logs (defaults to `$HOME/.watchdog/logs`).
- `WATCHDOG_MAX_LOG_SIZE` - maximum log size (in bytes) before pruning kicks in (defaults to `5000000` or ~5 MB).
- `WATCHDOG_SESSION` (auto-set) - unique identifier for the current shell session.

Set these variables before launching your terminal emulator to affect new shells. All shells must be interactive bash sessions; non-interactive shells exit early to avoid recursion.

## Structured database

In addition to raw `script` transcripts, Watchdog maintains a lightweight SQLite database at `~/.watchdog/watchdog.db` with columns:

```
logs(id INTEGER PK,
     ts TEXT,
     command TEXT,
     output TEXT,
     session TEXT)
```

Entries arrive in two ways:

1. **Real-time capture** via `PROMPT_COMMAND`, which forwards each completed bash command to `watchdog _realtime_log ...`.
2. **Bulk migration** of historical `.log` files. Use `watchdog migrate` (or `watchdog migrate --reset`) to rebuild the database from the text logs at any time.

Treat the plain-text logs as the source of truth -- you can always regenerate the SQLite index if it becomes stale.

## How it works

1. `watchdog install` creates `~/.watchdog/logs` (or your override) and injects a guarded snippet near the top of `~/.bashrc`.
2. Interactive bash shells detect the snippet, set `WATCHDOG_ACTIVE=1`, and start `script -af` with a timestamp/TTY/shell-based log filename.
3. On every prompt, `PROMPT_COMMAND` forwards the latest history entry to `watchdog _realtime_log ...`, feeding the SQLite index.
4. Each day gets its own folder, ~5 MB+ logs are pruned automatically, and non-interactive shells return immediately so nested scripts stay quiet.
5. When a terminal closes, the log remains on disk ready for `watchdog sessions`, `watchdog show <id>`, `watchdog last`, `watchdog search <keyword>`, the Textual browser, or `watchdog migrate`.

## Development

```bash
cd watchdog
python -m venv .venv && source .venv/bin/activate
pip install -e .
```

Use `PYTHONPATH=src python -m watchdog.cli <cmd>` for ad-hoc runs without reinstalling. Please keep docstrings and CLI help texts in sync with new functionality.

## License

Watchdog is distributed under the MIT License (see the repository-level [LICENSE](../LICENSE)).

