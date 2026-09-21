import subprocess
from skills import read_skill

def bash(command: str) -> str:
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=60
        )
        output = (result.stdout or "") + (result.stderr or "")
        return output.strip() or "(no output)"
    except subprocess.TimeoutExpired:
        return "(no output: command timed out)"

def read_file(path: str) -> str:
    """Read a file and return its contents."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {e}"

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
]

TOOLS = {
    "bash": bash,
    "read_file": read_file,
    "read_skill": read_skill,
}
