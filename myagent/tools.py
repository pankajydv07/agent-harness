import json
import subprocess
from .todos import write_todos, TODO_SCHEMA
from .skills import read_skill
from .context import note_read
from .history import cap
from . import sandbox
from . import permissions
from .ui import ui

def bash(command: str) -> str:
    try:
        result = sandbox.run(command, timeout=60)
        output = (result.stdout or "") + (result.stderr or "")
        return cap(output.strip() or "(no output)")
    except subprocess.TimeoutExpired:
        return "(no output: command timed out)"

def read_file(path: str) -> str:
    """Read a file and return its contents."""
    try:
        note_read(path)
        with open(path, "r", encoding="utf-8") as f:
            return cap(f.read())
    except Exception as e:
        return f"Error reading file: {e}"

def write_file(path: str, content: str) -> str:
    """Create a file, or overwrite it if it already exists."""
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Wrote {path}"
    except Exception as e:
        return f"Error writing file: {e}"

def str_replace(path: str, old_str: str, new_str: str, allow_multi_edit: bool = False) -> str:
    """Swap exact text in a file. old_str must match uniquely unless allow_multi_edit is True."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        count = content.count(old_str)
        if count == 0:
            return f"Error: old_str was not found in {path}"
        if count > 1 and not allow_multi_edit:
            return (
                f"Error: old_str matches {count} times in {path}. "
                "Add surrounding lines to make it unique, "
                "or set allow_multi_edit to true to replace them all."
            )

        new_content = content.replace(old_str, new_str)
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_content)
        return f"Replaced {count} match(es) in {path}"
    except Exception as e:
        return f"Error editing file: {e}"

def task(description: str) -> str:
    from .subagent import task as run_subagent
    return run_subagent(description)

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "bash",
            "description": "Run a shell command and return its output.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The shell command to run",
                    }
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a file and return its contents.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file to read",
                    }
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_skill",
            "description": "Read a skill and return its full instructions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Name of the skill to read",
                    }
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Create a file, or overwrite it if it already exists.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File to write"},
                    "content": {"type": "string", "description": "The full contents"},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "str_replace",
            "description": (
                "Replace exact text in a file. old_str must appear exactly once, "
                "so include surrounding lines if needed."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File to edit"},
                    "old_str": {"type": "string", "description": "Exact text to find"},
                    "new_str": {"type": "string", "description": "Text to put in its place"},
                    "allow_multi_edit": {
                        "type": "boolean",
                        "description": "Replace every match instead of failing",
                    },
                },
                "required": ["path", "old_str", "new_str"],
            },
        },
    },
    TODO_SCHEMA,
    {
        "type": "function",
        "function": {
            "name": "task",
            "description": (
                "Hand a self-contained exploration question to a fresh agent with its own "
                "isolated context window, and get back its findings. Use this to trace code "
                "and inspect files without cluttering your context."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "description": "The standalone exploration question to answer.",
                    }
                },
                "required": ["description"],
            },
        },
    },
]

TOOLS = {
    "bash": bash,
    "read_file": read_file,
    "write_file": write_file,
    "str_replace": str_replace,
    "read_skill": read_skill,
    "write_todos": write_todos,
    "task": task,
}

def execute(tool_call) -> tuple[dict, str]:
    """Universal executor enforcing permissions, sandbox, and capping."""
    args = json.loads(tool_call.function.arguments)
    func_name = tool_call.function.name

    action, reason = permissions.check(func_name, args)

    if action == "deny":
        result = f"Error: Action '{reason}' is blocked by security policy."
        ui.note(f"Blocked: {reason}")
    elif action == "ask" and not ui.confirm(reason or func_name):
        result = f"Error: User denied permission to {reason}."
        ui.note(f"Denied by user: {reason}")
    elif func_name in TOOLS:
        result = TOOLS[func_name](**args)
    else:
        result = f"Error: Tool '{func_name}' is not registered."

    return args, str(result)
