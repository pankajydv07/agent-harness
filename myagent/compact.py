"""The compaction agent: summarizes transcripts when context window fills up."""

from . import config
from .history import estimate, strip
from .llm import client

SYSTEM_PROMPT = """
You are compacting the transcript of a coding session that has grown too large.
Write a structured handoff note so a fresh agent can continue work immediately without re-reading everything.

## Goal
What the user asked for.

## What happened
Decisions taken, approaches tried, and why abandoned dead-ends failed.

## Files
Touched files and what changed in them.

## State
What is working, what is broken.

## Next
Immediate next step.
"""

HANDOFF = """<summary>
Everything before this point has been compacted out of the context window to free up room.
{summary}
</summary>"""

def needed(usage: dict) -> bool:
    """Has the prompt grown past the threshold?"""
    prompt_tokens = usage.get("prompt_tokens", 0)
    return prompt_tokens > (config.CONTEXT_WINDOW * config.COMPACT_AT)

def render(messages: list) -> str:
    lines = []
    for msg in messages:
        if msg.get("role") == "system":
            continue
        content = msg.get("content") or ""
        for call in msg.get("tool_calls") or []:
            func = call["function"]
            content += f"\n[Tool {func['name']}: {func['arguments']}]"
        lines.append(f"{str(msg.get('role', 'user')).upper()}: {content}")
    return "\n\n".join(lines)

def summarize(messages: list) -> str:
    response = client.chat.completions.create(
        model=config.MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": render(messages)},
        ],
    )
    return response.choices[0].message.content or "No summary generated."

def compact(messages: list) -> list:
    if len(messages) <= 4:
        return messages
    
    cut_idx = max(2, int(len(messages) * (1 - config.COMPACT_TO)))
    summary_text = summarize(messages[1:cut_idx])
    
    kept = [
        messages[0],
        {"role": "user", "content": HANDOFF.format(summary=summary_text)},
        *messages[cut_idx:],
    ]
    strip(kept)
    return kept
