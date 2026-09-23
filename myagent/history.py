"""Keeping transcript small enough to send: cap, strip, and fit."""

import json
import tempfile
from pathlib import Path
from . import config

CAP = 10_000   # Max chars of fresh tool result shown inline
STUB = 300     # Chars kept once the producing turn is over
TRIMMED = "[output trimmed:"
SUMMARY = "<summary>"
SPILLS = []

def spill(text: str) -> str:
    """Park large output in a temporary file."""
    handle = tempfile.NamedTemporaryFile(
        mode="w", prefix="myagent-", suffix=".txt", delete=False, encoding="utf-8"
    )
    handle.write(text)
    handle.close()
    SPILLS.append(Path(handle.name))
    return handle.name

def cap(text: str) -> str:
    """Trim fresh tool results and leave a pointer to full output."""
    if len(text) <= CAP:
        return text
    path = spill(text)
    return (
        text[:CAP] + f"\n\n{TRIMMED} {len(text) - CAP} of {len(text)} chars cut. "
        f"Full output saved at {path}.]"
    )

def sweep():
    """Delete temp spill files when turn finishes."""
    for path in SPILLS:
        path.unlink(missing_ok=True)
    SPILLS.clear()

def locked(messages: list) -> int:
    """Index of frozen compacted prefix so we never invalidate prompt cache."""
    for index in range(len(messages) - 1, -1, -1):
        if SUMMARY in str(messages[index].get("content") or ""):
            return index + 1
    return 0

def strip(messages: list) -> int:
    """Shrink historical tool outputs from finished turns to short stubs."""
    shrunk = 0
    for message in messages[locked(messages):]:
        content = message.get("content") or ""
        if message.get("role") != "tool" or TRIMMED in content or len(content) <= STUB:
            continue
        message["content"] = (
            content[:STUB] + f"\n\n{TRIMMED} {len(content) - STUB} more chars.]"
        )
        shrunk += 1
    return shrunk

def estimate(messages: list) -> int:
    """Rough token count estimation."""
    return sum(len(json.dumps(m)) for m in messages) // 4
