"""The plan. Lives here in state, not lost in transcript, and is re-injected every turn."""

MARKS = {"pending": "[ ]", "in_progress": "[~]", "done": "[x]"}

TODOS = []  # [{"content": ..., "activeForm": ..., "status": ...}]

def write_todos(todos: list) -> str:
    """Replace the whole list. Exactly one task may be in_progress."""
    active = [t for t in todos if t["status"] == "in_progress"]
    if len(active) > 1:
        return f"Error: {len(active)} tasks are in_progress. Only one may be in_progress at a time."

    TODOS[:] = todos
    return todos_prompt() or "Todo list cleared."

def todos_prompt() -> str:
    return "\n".join(f"{MARKS.get(t['status'], '[ ]')} {t['content']}" for t in TODOS)

def active_form() -> str:
    """What the agent is doing right now, for the dynamic spinner."""
    for todo in TODOS:
        if todo.get("status") == "in_progress":
            return todo.get("activeForm", "working")
    return "thinking"

TODO_SCHEMA = {
    "type": "function",
    "function": {
        "name": "write_todos",
        "description": (
            "Record the plan for a multi-step task. Send the whole list every "
            "time. Keep exactly one task in_progress and update it as you go."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "todos": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "content": {
                                "type": "string",
                                "description": "The task, imperative: 'Fix the parser'",
                            },
                            "activeForm": {
                                "type": "string",
                                "description": "Present continuous: 'Fixing the parser'",
                            },
                            "status": {
                                "type": "string",
                                "enum": ["pending", "in_progress", "done"],
                            },
                        },
                        "required": ["content", "activeForm", "status"],
                    },
                }
            },
            "required": ["todos"],
        },
    },
}
