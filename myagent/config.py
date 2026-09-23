"""Settings: real environment variables first, then ~/.agents/env or local .env."""

import os
from pathlib import Path
from dotenv import load_dotenv

# 1. Load local .env if present
load_dotenv()

# 2. Fall back to global ~/.agents/env if present
GLOBAL_ENV = Path.home() / ".agents" / "env"
if GLOBAL_ENV.exists():
    for line in GLOBAL_ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())

BASE_URL = os.getenv("BASE_URL", "https://openrouter.ai/api/v1")
API_KEY = os.getenv("API_KEY", "")
MODEL = os.getenv("MODEL", "deepseek/deepseek-chat")
