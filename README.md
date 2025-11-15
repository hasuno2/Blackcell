# Blackcell

Blackcell is an umbrella workspace for small command-line utilities. Each tool lives in its own subdirectory with an isolated Python packaging setup so you can work on them independently while sharing a single repo.

## Projects

- `watchdog/` - interactive bash session logger that records and replays shell histories. See [`watchdog/README.md`](watchdog/README.md) for detailed usage, configuration, and development notes.

More tools will land under this repository over time (for example, `docs/`, `other-tool/`, etc.).

## Getting Started

```bash
git clone <repo-url>
cd Blackcell/watchdog
pip install -e .  # install the watchdog CLI in editable mode
```

Once installed, run `watchdog --help` for the available commands or browse the project README for deeper guidance.

## Contributing

Issues and pull requests are welcome. Each sub-project contains its own tests and packaging metadata; please keep changes scoped to a single tool unless the update clearly spans multiple components.

1. Fork and clone the repository.
2. Create a feature branch off `main`.
3. Make changes (and add tests/docs where helpful).
4. Open a pull request describing the motivation and testing performed.

## License

Distributed under the MIT License. See [LICENSE](LICENSE) for details.

