"""Transcripts on disk. One JSONL file per chat."""

import json
from datetime import datetime
from pathlib import Path

SESSION_DIR = Path.home() / ".agents" / "sessions"
CURRENT = datetime.now().strftime("%Y%m%d-%H%M%S")
WRITTEN = 0  # Number of messages already flushed to disk

def path_for(session_id: str) -> Path:
    return SESSION_DIR / f"{session_id}.jsonl"

def save(messages: list):
    """Append only new messages to disk. Never rewrite unchanged history."""
    global WRITTEN
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    with path_for(CURRENT).open("a", encoding="utf-8") as f:
        for message in messages[WRITTEN:]:
            f.write(json.dumps(message) + "\n")
    WRITTEN = len(messages)

def rewind_to(count: int):
    """Record a rewind event so older messages are retained in raw log."""
    global WRITTEN
    with path_for(CURRENT).open("a", encoding="utf-8") as f:
        f.write(json.dumps({"rewind_to": count}) + "\n")
    WRITTEN = count

def load(session_id: str) -> list:
    """Replay log: accumulate messages and respect rewind cutbacks."""
    messages = []
    file_path = path_for(session_id)
    if not file_path.exists():
        return messages
    for line in file_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        entry = json.loads(line)
        if "rewind_to" in entry:
            del messages[entry["rewind_to"]:]
        else:
            messages.append(entry)
    return messages

def open_session(session_id: str) -> list:
    """Switch to a past chat and load its message history."""
    global CURRENT, WRITTEN
    CURRENT = session_id
    messages = load(session_id)
    WRITTEN = len(messages)
    return messages

def title(messages: list) -> str:
    for message in messages:
        if message.get("role") == "user":
            return " ".join(str(message.get("content", "")).split())[:60]
    return "(empty)"

def all_sessions() -> list[dict]:
    """Return all saved sessions sorted newest first."""
    if not SESSION_DIR.exists():
        return []
    files = sorted(SESSION_DIR.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
    return [{"id": p.stem, "title": title(load(p.stem))} for p in files]
