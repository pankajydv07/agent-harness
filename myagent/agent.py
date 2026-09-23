import json
from . import commands
from . import session
from .context import reminder
from .llm import SYSTEM_PROMPT, call_llm
from .tools import execute
from .ui import ui
from .todos import active_form
from . import history
from . import compact

def main():
    ui.banner()
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    while True:
        user_input = ui.ask()
        if not user_input or user_input.lower() in ("exit", "quit", "q"):
            break

        # Intercept slash commands (/help, /rewind, /sessions, /clear, /compact)
        if user_input.startswith("/"):
            handled, messages = commands.handle(user_input, messages)
            if handled:
                continue

        messages.append({"role": "user", "content": user_input})
        last_usage = {}

        while True:
            try:
                with ui.working(active_form()):
                    message, usage = call_llm(messages + [reminder()])
                    last_usage = usage
            except Exception as e:
                ui.agent(f"API Error: {e}")
                break

            messages.append(message.model_dump(exclude_none=True))

            if message.content:
                ui.agent(message.content)

            ui.usage(usage)

            if not message.tool_calls:
                break

            for tool_call in message.tool_calls:
                args, result = execute(tool_call)
                ui.tool(tool_call.function.name, args, result)

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                })

        # End of turn maintenance: strip old tool outputs and sweep spilled files
        history.strip(messages)
        history.sweep()

        # Check for automatic context compaction threshold
        if compact.needed(last_usage):
            ui.note("Context window nearing limit. Compacting history...")
            messages = compact.compact(messages)
            ui.note("Context compaction complete.")

        # Persist new turns to session log on disk
        session.save(messages)

    ui.summary()

if __name__ == "__main__":
    main()

