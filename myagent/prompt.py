"""The input line.

Terminal Keybindings:
- Enter: Submit message to agent
- Alt+Enter / Esc+Enter / Ctrl+J: Insert newline (multi-line prompt)
- Up / Down Arrow: Cycle persistent command history (~/.agents/history)
- Alt+Left / Alt+Right: Jump words
"""

from pathlib import Path
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style

HISTORY = Path.home() / ".agents" / "history"

STYLE = Style.from_dict({
    "prompt": "bold #9ece6a",
    "completion-menu.completion": "bg:#24283b fg:#c0caf5",
    "completion-menu.completion.current": "bg:#7aa2f7 fg:#1a1b26 bold",
    "completion-menu.meta.completion": "bg:#1f2335 fg:#7982a9 italic",
    "completion-menu.meta.completion.current": "bg:#7aa2f7 fg:#1a1b26 italic",
    "scrollbar.background": "bg:#1a1b26",
    "scrollbar.button": "bg:#565f89",
})

COMMAND_TREE = {
    "/help": {
        "desc": "Show available commands",
        "sub": {},
    },
    "/mcp": {
        "desc": "Inspect & manage MCP servers and tools",
        "sub": {
            "status": "Show server status and tools",
            "reload": "Reconnect & reload MCP servers",
            "servers": "List connected servers",
            "tools": "List loaded MCP tools",
        },
    },
    "/config": {
        "desc": "View & edit agent settings",
        "sub": {
            "view": "Show current configuration",
            "model": "Set active LLM model",
            "base_url": "Set API base URL",
            "compact_at": "Set compaction threshold (0.0 - 1.0)",
        },
    },
    "/sessions": {
        "desc": "Manage conversation sessions",
        "sub": {
            "list": "Open a saved conversation",
            "new": "Start a fresh session",
        },
    },
    "/rewind": {
        "desc": "Step back to an earlier turn",
        "sub": {},
    },
    "/clear": {
        "desc": "Start a fresh conversation history",
        "sub": {},
    },
    "/compact": {
        "desc": "Summarize context to free up tokens",
        "sub": {
            "now": "Compact conversation history immediately",
            "thresholds": "View auto-compaction trigger thresholds",
        },
    },
}


class SlashCommandCompleter(Completer):
    """Hierarchical completer for slash commands and child options."""

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        if not text.startswith("/"):
            return

        parts = text.split(" ")
        if len(parts) == 1:
            prefix = parts[0]
            for cmd, info in COMMAND_TREE.items():
                if cmd.startswith(prefix):
                    yield Completion(
                        cmd,
                        start_position=-len(prefix),
                        display=cmd,
                        display_meta=info["desc"],
                    )
        elif len(parts) >= 2:
            cmd = parts[0]
            sub_prefix = parts[1] if len(parts) == 2 else ""
            if cmd in COMMAND_TREE and COMMAND_TREE[cmd]["sub"]:
                sub_dict = COMMAND_TREE[cmd]["sub"]
                for sub_name, sub_desc in sub_dict.items():
                    if sub_name.startswith(sub_prefix):
                        yield Completion(
                            sub_name,
                            start_position=-len(sub_prefix),
                            display=sub_name,
                            display_meta=sub_desc,
                        )


bindings = KeyBindings()

@bindings.add("escape", "left")
def _word_left(event):
    doc = event.current_buffer.document
    event.current_buffer.cursor_position += doc.find_previous_word_beginning(count=1) or 0

@bindings.add("escape", "right")
def _word_right(event):
    doc = event.current_buffer.document
    event.current_buffer.cursor_position += doc.find_next_word_ending(count=1) or 0

# Multi-line newline bindings:
# Terminals send Alt+Enter as (escape, enter) and Ctrl+Enter/Shift+Enter as (c-j)
@bindings.add("escape", "enter")
def _newline_alt_enter(event):
    """Alt+Enter (Option+Enter) inserts a new line."""
    event.current_buffer.insert_text("\n")

@bindings.add("c-j")
def _newline_ctrl_j(event):
    """Ctrl+J / Shift+Enter (in supported terminals) inserts a new line."""
    event.current_buffer.insert_text("\n")

SESSION = None

def read(prompt_str: str = "> ") -> str:
    """Read one message with persistent history, completer, and keybindings."""
    global SESSION
    if SESSION is None:
        HISTORY.parent.mkdir(parents=True, exist_ok=True)
        SESSION = PromptSession(
            history=FileHistory(str(HISTORY)),
            key_bindings=bindings,
            style=STYLE,
            completer=SlashCommandCompleter(),
            complete_while_typing=True,
            multiline=False,
            enable_history_search=True,
        )
    return SESSION.prompt(HTML(f"<prompt>{prompt_str}</prompt>"))
