"""Which tool calls need human approval.
Read-only commands run silently; risky commands stop and ask; dangerous ones are blocked.
"""

import re
from fnmatch import fnmatch
from pathlib import Path

PROJECT = Path.cwd().resolve()

# Catch-all is first; specific rules override below
BASH_RULES = {
    "*": "ask",
    # Read-only: allow automatically
    "ls*": "allow",
    "dir*": "allow",
    "pwd": "allow",
    "cd *": "allow",
    "echo *": "allow",
    "cat *": "allow",
    "head *": "allow",
    "tail *": "allow",
    "wc *": "allow",
    "which *": "allow",
    "grep *": "allow",
    "rg *": "allow",
    "find *": "allow",
    "git status*": "allow",
    "git diff*": "allow",
    "git log*": "allow",
    "git show*": "allow",
    "git ls-files*": "allow",
    "pytest*": "allow",
    "python -m pytest*": "allow",
    # Dangerous: blocked automatically
    "rm *": "deny",
    "rmdir *": "deny",
    "del *": "deny",
    "sudo *": "deny",
    "chmod *": "deny",
    "chown *": "deny",
    "git push*": "deny",
    "git reset*": "deny",
    "git clean*": "deny",
}

SEPARATORS = re.compile(r"&&|\|\||;|\|")

def decide(command: str) -> str:
    """Rate every sub-command; strictest verdict wins."""
    verdicts = []
    for part in SEPARATORS.split(command):
        action = "ask"
        for pattern, rule in BASH_RULES.items():
            if fnmatch(part.strip(), pattern):
                action = rule
        verdicts.append(action)

    for strictest in ("deny", "ask"):
        if strictest in verdicts:
            return strictest
    return "allow"

def inside_project(path: str) -> bool:
    try:
        resolved = Path(path).resolve()
        return PROJECT == resolved or PROJECT in resolved.parents
    except Exception:
        return False

def check(name: str, args: dict) -> tuple[str, str | None]:
    """Returns (action, reason). Action is 'allow', 'ask', or 'deny'."""
    if name == "bash":
        return decide(args.get("command", "")), f"run shell command: {args.get('command')}"

    if name in ("write_file", "str_replace"):
        target_path = args.get("path", "")
        if not inside_project(target_path):
            return "ask", f"{name} outside project root: {target_path}"

    return "allow", None
