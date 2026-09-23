"""The input line.

Terminal Keybindings:
- Enter: Submit message to agent
- Alt+Enter / Esc+Enter / Ctrl+J: Insert newline (multi-line prompt)
- Up / Down Arrow: Cycle persistent command history (~/.agents/history)
- Alt+Left / Alt+Right: Jump words
"""

from pathlib import Path
from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style

HISTORY = Path.home() / ".agents" / "history"
STYLE = Style.from_dict({"prompt": "bold #9ece6a"})

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
    """Read one message with persistent history and keybindings."""
    global SESSION
    if SESSION is None:
        HISTORY.parent.mkdir(parents=True, exist_ok=True)
        SESSION = PromptSession(
            history=FileHistory(str(HISTORY)),
            key_bindings=bindings,
            style=STYLE,
            multiline=False,
            enable_history_search=True,
        )
    return SESSION.prompt(HTML(f"<prompt>{prompt_str}</prompt>"))
