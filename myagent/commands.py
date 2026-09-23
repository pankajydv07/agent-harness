from . import session
from .ui import ui

COMMANDS = {
    "/help": "Show available commands",
    "/rewind": "Step back to an earlier point in this conversation",
    "/sessions": "List and reopen past conversation sessions",
    "/clear": "Start a fresh conversation history",
}

def rewind(messages: list) -> list:
    user_turns = [
        (i, m.get("content", "")) for i, m in enumerate(messages) if m.get("role") == "user"
    ]
    if not user_turns:
        ui.note("No turns to rewind.")
        return messages
    rows = [f"turn {i}: {content[:50]}" for i, content in user_turns]
    choice = ui.pick("Rewind to turn", rows)
    if choice is None:
        return messages
    target_idx = user_turns[choice][0]
    session.rewind_to(target_idx)
    ui.note(f"Rewound to turn {target_idx}")
    return messages[:target_idx]

def sessions(messages: list) -> list:
    saved = session.all_sessions()
    if not saved:
        ui.note("No saved chats yet.")
        return messages
    rows = [f"{s['id']}  {s['title']}" for s in saved]
    choice = ui.pick("Open saved chat", rows)
    if choice is None:
        return messages
    loaded = session.open_session(saved[choice]["id"])
    ui.resumed(loaded)
    return loaded

def handle(command: str, messages: list) -> tuple[bool, list]:
    """Returns (was_handled, updated_messages)"""
    cmd = command.strip().split()[0].lower()
    if cmd == "/rewind":
        return True, rewind(messages)
    if cmd == "/sessions":
        return True, sessions(messages)
    if cmd == "/clear":
        ui.note("Started fresh conversation.")
        return True, [m for m in messages if m.get("role") == "system"]
    if cmd == "/help":
        ui.note("\n".join(f"{name:<12} - {help_text}" for name, help_text in COMMANDS.items()))
        return True, messages
    return False, messages
