import json
from contextlib import contextmanager
from rich.console import Console, Group
from rich.markdown import Markdown
from rich.padding import Padding
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

ACCENT = "#7aa2f7"
USER = "#9ece6a"
TOOL = "#e0af68"
MUTED = "#565f89"
MAX_TOOL_OUTPUT_LINES = 12

class UI:
    def __init__(self):
        self.console = Console()
        self._totals = {}

    def banner(self):
        self.console.print()
        self.console.print(Rule(Text(" coding agent ", style=f"bold {ACCENT}"), style=MUTED))
        self.console.print(Padding(Text("type 'exit' or press ctrl-d to quit", style=MUTED), (0, 0, 0, 2)))

    def ask(self) -> str:
        self.console.print()
        try:
            return self.console.input(f"[bold {USER}]>[/] ").strip()
        except (EOFError, KeyboardInterrupt):
            self.console.print()
            return ""

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

    @contextmanager
    def working(self):
        with self.console.status(Text("thinking", style=MUTED), spinner="dots", spinner_style=ACCENT):
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
