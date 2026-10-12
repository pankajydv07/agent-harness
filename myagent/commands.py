from . import session
from . import compact
from . import config
from .ui import ui

COMMANDS = {
    "/help": "Show available commands",
    "/mcp": "Inspect & manage MCP servers and tools",
    "/config": "View and edit agent settings (model, API, thresholds)",
    "/sessions": "List and reopen past conversation sessions",
    "/rewind": "Step back to an earlier point in this conversation",
    "/clear": "Start a fresh conversation history",
    "/compact": "Summarize earlier context to free up tokens",
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


def handle_sessions(args: list[str], messages: list) -> list:
    sub = args[0].lower() if args else ""
    if sub == "new":
        ui.note("Started fresh conversation.")
        return [m for m in messages if m.get("role") == "system"]
    if sub == "list":
        return sessions(messages)

    # Interactive menu if no argument given
    choices = ["Open saved conversation", "Start fresh session", "Cancel"]
    choice_idx = ui.pick("Sessions", choices)
    if choice_idx == 0:
        return sessions(messages)
    elif choice_idx == 1:
        ui.note("Started fresh conversation.")
        return [m for m in messages if m.get("role") == "system"]
    return messages


def handle_compact(args: list[str], messages: list) -> list:
    sub = args[0].lower() if args else ""
    if sub == "thresholds":
        ui.note(
            f"Context Window: {config.CONTEXT_WINDOW:,} tokens\n"
            f"Compact Trigger: {int(config.COMPACT_AT * 100)}%\n"
            f"Target Size: {int(config.COMPACT_TO * 100)}%"
        )
        return messages

    if len(messages) <= 4:
        ui.note("Transcript is too short to compact.")
        return messages
    with ui.working("compacting context"):
        new_messages = compact.compact(messages)
    ui.note(f"Compacted {len(messages)} messages down to {len(new_messages)} messages.")
    return new_messages


def handle_mcp(args: list[str], messages: list) -> list:
    from .mcp import mcp_manager
    sub = args[0].lower() if args else ""

    if not sub:
        choices = [
            "View Status & Tools",
            "Reload MCP Servers",
            "Show Config Path",
            "Cancel",
        ]
        choice_idx = ui.pick("MCP Options", choices)
        if choice_idx == 0 or choice_idx is None:
            sub = "status"
        elif choice_idx == 1:
            sub = "reload"
        elif choice_idx == 2:
            sub = "config"
        else:
            return messages

    if sub == "reload":
        from .tools import TOOLS, TOOL_SCHEMAS
        mcp_manager.close()
        schemas, tools = mcp_manager.start(existing_names=set(TOOLS.keys()))
        TOOL_SCHEMAS.extend(schemas)
        TOOLS.update(tools)
        ui.note(f"MCP reloaded. {len(tools)} tools registered.")
        return messages

    if sub == "config":
        cfg = mcp_manager.config_path or "(none)"
        ui.note(f"Active MCP config: {cfg}")
        return messages

    if sub == "servers":
        servers = mcp_manager.get_status().get("servers", {})
        if not servers:
            ui.note("No MCP servers connected.")
        else:
            ui.note("\n".join(f"• {k}: {v}" for k, v in servers.items()))
        return messages

    if sub == "tools":
        tools = mcp_manager.get_status().get("tools", [])
        if not tools:
            ui.note("No MCP tools loaded.")
        else:
            ui.note("\n".join(f"• {t}" for t in tools))
        return messages

    # Default / status
    status = mcp_manager.get_status()
    cfg = status.get("config") or "(none)"
    servers = status.get("servers", {})
    tools = status.get("tools", [])

    lines = [f"MCP Config: {cfg}"]
    if not servers:
        lines.append("No active MCP servers connected.")
    else:
        lines.append("Servers:")
        for sname, sstatus in servers.items():
            lines.append(f"  • {sname}: {sstatus}")

    if tools:
        lines.append(f"Tools ({len(tools)}):")
        for t in tools:
            lines.append(f"  • {t}")
    else:
        lines.append("Tools: (none)")

    ui.note("\n".join(lines))
    return messages


def handle_config(args: list[str], messages: list) -> list:
    sub = args[0].lower() if args else ""
    val = " ".join(args[1:]).strip() if len(args) > 1 else ""

    if not sub:
        # Interactive configuration menu
        choices = [
            f"Model: {config.MODEL}",
            f"Base URL: {config.BASE_URL}",
            f"Context Window: {config.CONTEXT_WINDOW}",
            f"Compact Threshold: {int(config.COMPACT_AT * 100)}%",
            "Cancel",
        ]
        choice_idx = ui.pick("Agent Settings", choices)
        if choice_idx == 0:
            sub = "model"
        elif choice_idx == 1:
            sub = "base_url"
        elif choice_idx == 2:
            sub = "context_window"
        elif choice_idx == 3:
            sub = "compact_at"
        elif choice_idx is None:
            sub = "view"
        else:
            return messages

    if sub == "view":
        ui.note(
            f"Model: {config.MODEL}\n"
            f"Base URL: {config.BASE_URL}\n"
            f"Context Window: {config.CONTEXT_WINDOW:,}\n"
            f"Compact Trigger: {int(config.COMPACT_AT * 100)}%\n"
            f"Compact Target: {int(config.COMPACT_TO * 100)}%"
        )
        return messages

    if sub == "model":
        if not val:
            val = ui.prompt_text("Enter LLM model:", default=config.MODEL)
        if val:
            config.MODEL = val
            ui.note(f"Model updated to: {config.MODEL}")
        return messages

    if sub == "base_url":
        if not val:
            val = ui.prompt_text("Enter Base URL:", default=config.BASE_URL)
        if val:
            config.BASE_URL = val
            from .llm import client
            client.base_url = val
            ui.note(f"Base URL updated to: {config.BASE_URL}")
        return messages

    if sub == "context_window":
        if not val:
            val = ui.prompt_text("Enter context window size:", default=str(config.CONTEXT_WINDOW))
        if val.isdigit():
            config.CONTEXT_WINDOW = int(val)
            ui.note(f"Context window updated to: {config.CONTEXT_WINDOW:,}")
        return messages

    if sub == "compact_at":
        if not val:
            val = ui.prompt_text("Enter compaction threshold (0.1 - 0.95):", default=str(config.COMPACT_AT))
        try:
            f = float(val)
            if 0.0 < f < 1.0:
                config.COMPACT_AT = f
                ui.note(f"Compaction threshold set to: {int(config.COMPACT_AT * 100)}%")
        except ValueError:
            ui.note("Invalid threshold float.")
        return messages

    ui.note(f"Unknown config option '{sub}'. Use /config view to see settings.")
    return messages


def handle(command: str, messages: list) -> tuple[bool, list]:
    """Dispatch slash commands with argument parsing."""
    parts = command.strip().split()
    if not parts:
        return False, messages

    cmd = parts[0].lower()
    args = parts[1:]

    if cmd == "/rewind":
        return True, rewind(messages)
    if cmd == "/sessions":
        return True, handle_sessions(args, messages)
    if cmd == "/clear":
        ui.note("Started fresh conversation.")
        return True, [m for m in messages if m.get("role") == "system"]
    if cmd == "/compact":
        return True, handle_compact(args, messages)
    if cmd == "/mcp":
        return True, handle_mcp(args, messages)
    if cmd == "/config":
        return True, handle_config(args, messages)
    if cmd == "/help":
        ui.note("\n".join(f"{name:<12} - {help_text}" for name, help_text in COMMANDS.items()))
        return True, messages
    return False, messages
