"""Textual application for browsing structured watchdog logs."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import csv

from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widgets import Button, DataTable, Footer, Header, Input, Static, TextArea

from .. import config, db


@dataclass
class LogEntry:
    ts: str
    command: str
    output: str
    session: str


class PromptScreen(ModalScreen[str | None]):
    """Reusable dialog for gathering text input."""

    def __init__(self, title: str, initial: str = "") -> None:
        super().__init__()
        self._title = title
        self._initial = initial

    def compose(self) -> ComposeResult:
        yield Container(
            Static(self._title, id="prompt-title"),
            Input(value=self._initial, id="prompt-input"),
            Horizontal(
                Button("Submit", id="prompt-submit", variant="success"),
                Button("Cancel", id="prompt-cancel"),
                id="prompt-buttons",
            ),
            id="prompt-container",
        )

    def on_mount(self) -> None:
        self.query_one(Input).focus()
        self.query_one(Input).cursor_end()

    def _finish(self, value: str | None) -> None:
        self.dismiss(value)

    @on(Input.Submitted)
    def handle_submit(self, event: Input.Submitted) -> None:
        self._finish(event.value)

    @on(Button.Pressed)
    def handle_button(self, event: Button.Pressed) -> None:
        if event.button.id == "prompt-submit":
            self._finish(self.query_one(Input).value)
        elif event.button.id == "prompt-cancel":
            self._finish(None)

    def on_key(self, event) -> None:
        if event.key == "escape":
            self._finish(None)


class DetailScreen(ModalScreen[None]):
    """Modal showing full command/output details."""

    def __init__(self, entry: LogEntry) -> None:
        super().__init__()
        self.entry = entry

    def compose(self) -> ComposeResult:
        yield Container(
            Static(f"Command: {self.entry.command}", id="detail-command"),
            TextArea(value=self.entry.output or "<no output>", read_only=True, id="detail-output"),
            Static("Press Esc or b to return.", id="detail-hint"),
            id="detail-container",
        )

    def on_key(self, event) -> None:
        if event.key in ("escape", "b"):
            self.dismiss(None)


class LogTableApp(App[None]):
    """Textual UI for browsing watchdog logs."""

    CSS = """
    #log-table {
        height: 1fr;
    }

    #status {
        padding: 1 2;
        border-top: solid #666;
    }

    #prompt-container, #detail-container {
        width: 80%;
        max-width: 120;
        margin: 2 auto;
        padding: 1 2;
        border: round #AAA;
        background: $surface;
    }

    #detail-output {
        height: 15;
        margin-top: 1;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("/", "search", "Search"),
        Binding("d", "filter_date", "Date"),
        Binding("r", "reload", "Reload"),
        Binding("c", "clear_filters", "Clear Filters"),
        Binding("enter", "detail", "Detail"),
        Binding("e", "export", "Export"),
    ]

    search_term = reactive("")
    date_filter = reactive("")

    def __init__(self) -> None:
        super().__init__()
        self.entries: list[LogEntry] = []
        self.filtered: list[LogEntry] = []

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield DataTable(id="log-table", zebra_stripes=True)
        yield Static("", id="status")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("Timestamp", "Command", "Output", "Session")
        self._load_entries()

    def _load_entries(self) -> None:
        rows = db.fetch_all_entries()
        self.entries = [
            LogEntry(ts=ts, command=cmd, output=output or "", session=session or "")
            for ts, cmd, output, session in rows
        ]
        self._apply_filters()
        self._set_status("Loaded log entries.")

    def _apply_filters(self) -> None:
        filtered = self.entries
        if self.search_term:
            needle = self.search_term.lower()
            filtered = [
                entry
                for entry in filtered
                if needle in entry.command.lower() or needle in entry.output.lower()
            ]
        if self.date_filter:
            filtered = [entry for entry in filtered if entry.ts.startswith(self.date_filter)]

        self.filtered = filtered
        self._refresh_table()

    def _refresh_table(self) -> None:
        table = self.query_one(DataTable)
        table.clear(columns=False)
        for idx, entry in enumerate(self.filtered):
            preview = entry.output.replace("\n", " ")
            if len(preview) > 50:
                preview = preview[:50].rstrip() + "…"
            table.add_row(entry.ts, entry.command, preview, entry.session, key=str(idx))

        if self.filtered:
            table.focus()
            table.cursor_coordinate = (0, 0)

        summary = f"{len(self.filtered)} entries"
        if self.search_term:
            summary += f" | search='{self.search_term}'"
        if self.date_filter:
            summary += f" | date={self.date_filter}"
        self._set_status(summary)

    def _current_entry(self) -> LogEntry | None:
        table = self.query_one(DataTable)
        if table.row_count == 0:
            return None
        key = table.cursor_row_key
        if key is None:
            return None
        try:
            return self.filtered[int(key)]
        except (ValueError, IndexError):
            return None

    def action_search(self) -> None:
        self.push_screen(PromptScreen("Search (leave blank to clear)", self.search_term), self._update_search)

    def _update_search(self, value: str | None) -> None:
        if value is None:
            return
        self.search_term = value.strip()
        self._apply_filters()

    def action_filter_date(self) -> None:
        self.push_screen(
            PromptScreen("Date filter (YYYY-MM-DD, blank to clear)", self.date_filter),
            self._update_date,
        )

    def _update_date(self, value: str | None) -> None:
        if value is None:
            return
        self.date_filter = value.strip()
        self._apply_filters()

    def action_clear_filters(self) -> None:
        self.search_term = ""
        self.date_filter = ""
        self._apply_filters()

    def action_reload(self) -> None:
        self._load_entries()

    def action_detail(self) -> None:
        entry = self._current_entry()
        if entry:
            self.push_screen(DetailScreen(entry))

    def action_export(self) -> None:
        if not self.filtered:
            self._set_status("No rows to export.")
            return

        export_dir = config.BASE_DIR / "exports"
        export_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        path = export_dir / f"{stamp}-logs.csv"
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["ts", "session", "command", "output"])
            for row in self.filtered:
                writer.writerow([row.ts, row.session, row.command, row.output])
        self._set_status(f"Exported {len(self.filtered)} rows to {path}.")

    def _set_status(self, message: str) -> None:
        self.query_one("#status", Static).update(message)


def run() -> None:
    """Launch the Textual UI."""
    LogTableApp().run()
