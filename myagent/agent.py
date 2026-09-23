import json
from . import commands
from . import session
from .context import reminder
from .llm import SYSTEM_PROMPT, call_llm
from .tools import TOOLS
from .ui import ui
from .todos import active_form
from . import permissions

def main():
    ui.banner()
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    while True:
        user_input = ui.ask()
        if not user_input or user_input.lower() in ("exit", "quit", "q"):
            break

        # Intercept slash commands (/help, /rewind, /sessions, /clear)
        if user_input.startswith("/"):
            handled, messages = commands.handle(user_input, messages)
            if handled:
                continue

        messages.append({"role": "user", "content": user_input})

        while True:
            try:
                with ui.working(active_form()):
                    message, usage = call_llm(messages + [reminder()])
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
                args = json.loads(tool_call.function.arguments)
                func_name = tool_call.function.name

                action, reason = permissions.check(func_name, args)

                if action == "deny":
                    result = f"Error: Action '{reason}' is blocked by security policy."
                    ui.note(f"Blocked: {reason}")
                elif action == "ask" and not ui.confirm(reason or func_name):
                    result = f"Error: User denied permission to {reason}."
                    ui.note(f"Denied by user: {reason}")
                elif func_name in TOOLS:
                    result = TOOLS[func_name](**args)
                else:
                    result = f"Error: Tool '{func_name}' is not registered."

                ui.tool(func_name, args, result)

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(result),
                })

        # Persist new turns to session log on disk
        session.save(messages)

    ui.summary()

if __name__ == "__main__":
    main()
