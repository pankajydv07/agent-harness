"""Subagents: exploration that happens in an isolated context window.

A subagent has its own message list that never outlives the call.
Only its concise final report crosses back to the parent agent.
"""

import os

MAX_TURNS = 12
WITHHELD = {"task", "write_todos", "str_replace", "write_file"}

SYSTEM_PROMPT = f"""
You are an exploration subagent. You were given one question by a lead agent and you answer it.
You cannot see the conversation that spawned you. Only your final message crosses back.

You are working in {os.getcwd()}.
- Use bash, read_file and read_skill to find out what is true.
- You are here to read and report, not to edit or mutate anything.
- Stop as soon as you can answer. Keep it concise (under 150 words): file paths, line numbers, exact findings.
"""

def toolset():
    """Every tool except withheld ones."""
    from .tools import TOOL_SCHEMAS
    return [s for s in TOOL_SCHEMAS if s["function"]["name"] not in WITHHELD]

def task(description: str) -> str:
    """Run a fresh agent on one exploration question and return only its final answer."""
    import json
    from .llm import call_llm
    from .tools import execute
    from .ui import ui

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": description},
    ]

    report = None
    for _ in range(MAX_TURNS):
        with ui.working("subagent exploring"):
            message, usage = call_llm(messages, tools=toolset())

        messages.append(message.model_dump(exclude_none=True))
        report = message.content or report

        if not message.tool_calls:
            return report or "(subagent returned no findings)"

        for tool_call in message.tool_calls:
            args, result = execute(tool_call)
            ui.tool(tool_call.function.name, args, result)
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result,
            })

    return report or "(subagent reached turn limit)"

TASK_SCHEMA = {
    "type": "function",
    "function": {
        "name": "task",
        "description": (
            "Hand a self-contained exploration question to a fresh agent with its own "
            "isolated context window, and get back its findings. Use this to trace code, "
            "search files, and inspect architecture without cluttering your context."
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
}
