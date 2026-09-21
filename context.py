"""Late injection: a small block appended just before we send to the LLM.
It goes at the END of the message list so the stable prefix in front of it stays cached.
"""

import os
import subprocess
from datetime import datetime

SEEN = {}  # path -> mtime when the agent last read it

def note_read(path: str):
    try:
        SEEN[path] = os.path.getmtime(path)
    except OSError:
        pass

def stale_files() -> list[str]:
    stale = []
    for path, mtime in list(SEEN.items()):
        try:
            if os.path.getmtime(path) != mtime:
                stale.append(path)
        except OSError:
            pass
    return stale

def stale_note() -> str:
    """Warn about files that changed on disk since the agent read them."""
    changed = stale_files()
    if not changed:
        return ""
    return (
        "\n<system-reminder>\n"
        "These files changed on disk since you read them. Read them again "
        "before editing:\n" + "\n".join(changed) + "\n</system-reminder>"
    )

def git_branch() -> str:
    result = subprocess.run(
        "git branch --show-current", shell=True, capture_output=True, text=True
    )
    return result.stdout.strip() or "(detached)"

def reminder() -> dict:
    """The block we append to the messages on every turn."""
    return {
        "role": "user",
        "content": (
            "<env>\n"
            f"time: {datetime.now():%Y-%m-%d %H:%M}\n"
            f"git branch: {git_branch()}\n"
            "</env>" + stale_note()
        ),
    }

