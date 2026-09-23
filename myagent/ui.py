import json
from contextlib import contextmanager
import questionary
from rich.console import Console, Group
from rich.markdown import Markdown
from rich.padding import Padding
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text
from . import sandbox
from . import prompt
ACCENT = "#7aa2f7"
USER = "#9ece6a"
TOOL = "#e0af68"
MUTED = "#565f89"
MAX_TOOL_OUTPUT_LINES = 12

CUSTOM_STYLE = questionary.Style([
    ("qmark", "fg:#e0af68 bold"),
    ("question", "bold"),
    ("answer", "fg:#9ece6a bold"),
    ("pointer", "fg:#7aa2f7 bold"),
    ("highlighted", "fg:#7aa2f7 bold"),
    ("selected", "fg:#9ece6a"),
])

class UI:
    def __init__(self):
        self.console = Console()
        self._totals = {}

    def banner(self):
        self.console.print()
        self.console.print(Rule(Text(f" coding agent · sandbox: {sandbox.name()} ", style=f"bold {ACCENT}"), style=MUTED))
        self.console.print(Padding(Text("type 'exit', '/help' or press ctrl-d to quit", style=MUTED), (0, 0, 0, 2)))

    def ask(self) -> str:
        self.console.print()
        try:
            return prompt.read("> ").strip()
        except (EOFError, KeyboardInterrupt):
            self.console.print()
            return ""


    def confirm(self, prompt: str) -> bool:
        """Interactive arrow-key confirmation menu (Use Up/Down + Enter)."""
        self.console.print(Padding(Text(f"Approval Required: {prompt}", style=f"bold {TOOL}"), (1, 0, 0, 2)))
        try:
            choice = questionary.select(
                "Authorize execution?",
                choices=[
                    "Yes, allow",
                    "No, deny",
                ],
                style=CUSTOM_STYLE,
                use_indicator=True,
            ).ask()
            return choice == "Yes, allow"
        except (EOFError, KeyboardInterrupt):
            return False

    def pick(self, title: str, rows: list) -> int | None:
        """Interactive arrow-key selection list for sessions and rewind."""
        if not rows:
            return None
        self.console.print()
        try:
            choice = questionary.select(
                title,
                choices=rows,
                style=CUSTOM_STYLE,
                use_indicator=True,
            ).ask()
            if choice is None:
                return None
            return rows.index(choice)
        except (EOFError, KeyboardInterrupt):
            return None

    def user(self, text: str):
        self.console.print(Padding(Text(text.strip(), style=f"bold {USER}"), (1, 0, 0, 2)))

    def agent(self, text: str):
        self.console.print(
            Padding(
                Group(
                    Text("<<", style=f"bold {ACCENT}"),
                    Padding(Markdown(text.strip()), (1, 0, 0, 0)),
                ),
                (1, 2, 0, 2),
            )
        )

    def tool(self, name: str, args: dict, result: str):
        header = Text.assemble(
            (f"{name} ", f"bold {TOOL}"),
            (self._format_args(args), MUTED),
        )
        self.console.print(
            Padding(
                Panel(
                    Group(header, Rule(style=MUTED), self._format_result(result)),
                    border_style=MUTED,
                    padding=(0, 1),
                ),
                (1, 2, 0, 2),
            )
        )

    def resumed(self, messages: list):
        turns = sum(1 for m in messages if m.get("role") == "user")
        self.console.print(
            Padding(Text(f"resumed · {len(messages)} messages · {turns} turns", style=MUTED), (1, 0, 0, 2))
        )

    def note(self, text: str):
        self.console.print(Padding(Text(text, style=MUTED), (1, 0, 0, 2)))

    @contextmanager
    def working(self, label="thinking"):
        with self.console.status(Text(label, style=MUTED), spinner="dots", spinner_style=ACCENT):
            yield

    def usage(self, stats: dict):
        for key, value in stats.items():
            self._totals[key] = self._totals.get(key, 0) + (value or 0)

        parts = " · ".join(
            f"{value:,} {key.replace('_tokens', '')}"
            for key, value in stats.items()
            if value
        )
        if parts:
            self.console.print(Padding(Text(parts, style=MUTED), (1, 0, 0, 2)))

    def summary(self):
        self.console.print()
        if not self._totals:
            self.console.print(Padding(Text("Goodbye! 👋", style=f"bold {USER}"), (0, 2)))
            return

        table = Table.grid(padding=(0, 2))
        table.add_column(style=MUTED)
        table.add_column(style=f"bold {ACCENT}", justify="right")
        for key, value in self._totals.items():
            table.add_row(key.replace("_", " "), f"{value:,}")

        self.console.print(Rule(Text(" session summary ", style=f"bold {ACCENT}"), style=MUTED))
        self.console.print(Padding(table, (1, 2)))
        self.console.print(Padding(Text("Goodbye! 👋", style=f"bold {USER}"), (0, 2)))
        self.console.print(Rule(style=MUTED))
        self.console.print()

    def _format_args(self, args: dict) -> str:
        if len(args) == 1:
            return str(next(iter(args.values())))
        return json.dumps(args)

    def _format_result(self, result: str) -> Text:
        lines = result.strip().splitlines() or ["(no output)"]
        shown = lines[:MAX_TOOL_OUTPUT_LINES]
        body = Text("\n".join(shown), style=MUTED)
        hidden = len(lines) - len(shown)
        if hidden > 0:
            body.append(f"\n… {hidden} more lines", style=f"italic {TOOL}")
        return body

ui = UI()
