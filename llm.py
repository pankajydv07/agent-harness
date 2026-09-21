import os
import sys
from dotenv import load_dotenv
from openai import OpenAI
from tools import TOOL_SCHEMAS
from skills import skills_prompt

load_dotenv()

BASE_URL = os.getenv("BASE_URL", "https://openrouter.ai/api/v1")
API_KEY = os.getenv("API_KEY")
MODEL = os.getenv("MODEL", "deepseek/deepseek-chat")

client = OpenAI(
    base_url=BASE_URL,
    api_key=API_KEY or "dummy-key",
)

SYSTEM_PROMPT = f"""
You are a coding agent. Your job is to code. Always code.
Use the bash tool to inspect files or run commands.
Use read_file to read file contents.
Use write_file to create new files.
Use str_replace to make targeted edits to existing files.
Use read_skill to load instructions for a specific skill.
Answer back to the user once your work is done.

Your current working directory is: {os.getcwd()}

Available skills:
{skills_prompt() or "(no skills available)"}
"""



def extract_usage(response) -> dict:
    usage = response.usage
    if not usage:
        return {}
    completion_details = getattr(usage, "completion_tokens_details", None)
    prompt_details = getattr(usage, "prompt_tokens_details", None)
    return {
        "prompt_tokens": getattr(usage, "prompt_tokens", 0),
        "completion_tokens": getattr(usage, "completion_tokens", 0),
        "total_tokens": getattr(usage, "total_tokens", 0),
        "reasoning_tokens": getattr(completion_details, "reasoning_tokens", None) if completion_details else None,
        "cached_tokens": getattr(prompt_details, "cached_tokens", None) if prompt_details else None,
    }

def call_llm(messages):
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=TOOL_SCHEMAS,
    )
    message = response.choices[0].message
    usage = extract_usage(response)
    return message, usage
