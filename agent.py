import json
from llm import SYSTEM_PROMPT, call_llm
from tools import TOOLS

def main():
    user_input = input("Enter your prompt > ")
    if not user_input.strip():
        return

    # 1. Initialize message history
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_input},
    ]

    # 2. The Agent Loop
    while True:
        # A. Call LLM with the full message history
        message, usage = call_llm(messages)

        # B. Append the assistant's response to history
        # (exclude_none ensures we don't send null fields back to the API)
        messages.append(message.model_dump(exclude_none=True))

        # C. If model produced text, print it
        if message.content:
            print("\nAgent:", message.content, "\n")

        # D. If no tool calls were requested, we are DONE!
        if not message.tool_calls:
            break

        # E. Execute each tool call requested by the model
        for tool_call in message.tool_calls:
            func_name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            
            print(f"[Running Tool] {func_name}({args})")
            result = TOOLS[func_name](**args)
            print(f"[Result]:\n{result}\n")

            # F. CRITICAL: Feed the tool result back to the model!
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": str(result),
            })

        print(f"[Usage]: {usage}")

if __name__ == "__main__":
    main()
