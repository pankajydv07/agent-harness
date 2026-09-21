from context import reminder
import json
from llm import SYSTEM_PROMPT, call_llm
from tools import TOOLS
from ui import ui


def main():
    ui.banner()
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    while True:
        user_input = ui.ask()
        # Clean exit check for empty input or explicit exit commands
        if not user_input or user_input.lower() in ("exit", "quit", "/exit", "/quit", "q"):
            break

        messages.append({"role": "user", "content": user_input})

        while True:
            with ui.working():
                message, usage = call_llm(messages + [reminder()])


            messages.append(message.model_dump(exclude_none=True))

            if message.content:
                ui.agent(message.content)

            ui.usage(usage)

            if not message.tool_calls:
                break

            for tool_call in message.tool_calls:
                args = json.loads(tool_call.function.arguments)
                result = TOOLS[tool_call.function.name](**args)
                ui.tool(tool_call.function.name, args, result)

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(result),
                })

    ui.summary()

if __name__ == "__main__":
    main()
