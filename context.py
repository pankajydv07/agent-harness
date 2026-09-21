"""Late injection: a small block appended just before we send to the LLM.
It goes at the END of the message list so the stable prefix in front of it stays cached.
"""

import subprocess
from datetime import datetime

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
            "</env>"
        ),
    }
