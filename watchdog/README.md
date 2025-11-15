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
watchdog uninstall           # remove the snippet
```

Run `watchdog --help` for the full command list.

## Configuration

By default logs are stored under `~/.watchdog/logs/YYYY/MM/DD`. Two environment variables let you customize behavior without editing the snippet:

- `WATCHDOG_LOG_ROOT` - override the root directory for logs (defaults to `$HOME/.watchdog/logs`).
- `WATCHDOG_MAX_LOG_SIZE` - maximum log size (in bytes) before pruning kicks in (defaults to `5000000` or ~5 MB).

Set these variables before launching your terminal emulator to affect new shells. All shells must be interactive bash sessions; non-interactive shells exit early to avoid recursion.

## How it works

1. `watchdog install` creates `~/.watchdog/logs` (or your override) and injects a guarded snippet near the top of `~/.bashrc`.
2. Interactive bash shells detect the snippet, set `WATCHDOG_ACTIVE=1`, and start `script -af` with a timestamp/TTY/shell-based log filename.
3. Each day gets its own folder, ~5 MB+ logs are pruned automatically, and non-interactive shells return immediately so nested scripts stay quiet.
4. When a terminal closes, the log remains on disk ready for `watchdog sessions`, `watchdog show <id>`, `watchdog last`, or `watchdog search <keyword>`.

## Development

```bash
cd watchdog
python -m venv .venv && source .venv/bin/activate
pip install -e .
```

Use `PYTHONPATH=src python -m watchdog.cli <cmd>` for ad-hoc runs without reinstalling. Please keep docstrings and CLI help texts in sync with new functionality.

## License

Watchdog is distributed under the MIT License (see the repository-level [LICENSE](../LICENSE)).
