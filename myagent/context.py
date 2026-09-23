"""Late injection: a small block appended just before we send to the LLM.
It goes at the END of the message list so the stable prefix in front of it stays cached.
"""

import os
import subprocess
from datetime import datetime
from .todos import todos_prompt

SEEN = {}  # path -> mtime when the agent last read it
LABELS = {"M": "modified", "D": "deleted", "A": "added", "??": "new"}

def note_read(path: str):
    """Record timestamp when file is read."""
    try:
        if os.path.exists(path):
            SEEN[path] = os.path.getmtime(path)
        else:
            SEEN.pop(path, None)
    except OSError:
        pass

def git(command: str) -> str:
    result = subprocess.run(
        f"git {command}", shell=True, capture_output=True, text=True
    )
    return result.stdout.strip()

def git_status() -> dict:
    """path -> status code from git status --porcelain."""
    raw = git("status --porcelain")
    status = {}
    for line in raw.splitlines():
        if len(line) >= 3:
            code = line[:2].strip()
            path = line[3:].strip()
            status[path] = code
    return status

LAST_STATUS = git_status()

def file_changes() -> dict:
    """What git sees as changed since the previous turn."""
    global LAST_STATUS
    now = git_status()
    changed = {p: c for p, c in now.items() if LAST_STATUS.get(p) != c}
    LAST_STATUS = now
    return changed

def changes_note() -> str:
    changed = file_changes()
    if not changed:
        return ""
    lines = [f"{LABELS.get(code, code)}: {path}" for path, code in changed.items()]
    return (
        "\n<system-reminder>\n"
        "These files changed since your last turn. Read them again before editing:\n"
        + "\n".join(lines)
        + "\n</system-reminder>"
    )

def reminder() -> dict:
    branch = git("branch --show-current") or "(detached)"
    return {
        "role": "user",
        "content": (
            "<env>\n"
            f"time: {datetime.now():%Y-%m-%d %H:%M}\n"
            f"git branch: {branch}\n"
            "</env>" + todos_note() + changes_note()
        ),
    }

def todos_note() -> str:
    plan = todos_prompt()
    return f"\n<todos>\n{plan}\n</todos>" if plan else ""
