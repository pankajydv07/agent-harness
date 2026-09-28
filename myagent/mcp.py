"""MCP (Model Context Protocol) client manager for myagent.

Discovers local MCP servers from mcp.json, connects via stdio,
and exposes tools dynamically to the agent with minimal overhead.
"""

import asyncio
import atexit
import contextlib
import json
import os
import threading
from pathlib import Path
from typing import Any, Callable

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False


def find_mcp_config() -> Path | None:
    """Find mcp.json in workspace or fallback to ~/.agents/mcp.json."""
    candidates = [
        Path.cwd() / "mcp.json",
        Path.home() / ".agents" / "mcp.json",
    ]
    for path in candidates:
        if path.is_file():
            return path
    return None


def parse_mcp_config(path: Path) -> dict[str, dict]:
    """Load and normalize server configs from JSON."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        servers = data.get("mcpServers", data)
        return {
            name: cfg
            for name, cfg in servers.items()
            if isinstance(cfg, dict) and "command" in cfg
        }
    except Exception:
        return {}


class MCPManager:
    """Manages persistent MCP client sessions over a background event loop."""

    def __init__(self, config_path: Path | None = None):
        self.config_path = config_path or find_mcp_config()
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.exit_stack: contextlib.AsyncExitStack | None = None
        self.sessions: dict[str, ClientSession] = {}
        self.server_status: dict[str, str] = {}
        self.tool_map: dict[str, tuple[str, str]] = {}  # full_name -> (server, orig_name)
        self.tool_schemas: list[dict[str, Any]] = []
        self._started = False

    def _run_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def start(self, existing_names: set[str] | None = None) -> tuple[list[dict], dict[str, Callable]]:
        """Start loop, connect to configured servers, and return (schemas, tools_dict)."""
        if not MCP_AVAILABLE or not self.config_path:
            return [], {}

        server_configs = parse_mcp_config(self.config_path)
        if not server_configs:
            return [], {}

        self.thread.start()
        self._started = True
        atexit.register(self.close)

        future = asyncio.run_coroutine_threadsafe(
            self._init_servers(server_configs, existing_names or set()),
            self.loop,
        )
        try:
            future.result(timeout=30)
        except Exception as e:
            self.server_status["_init"] = f"Failed to initialize: {e}"

        tools_dict = {
            name: self._make_tool_caller(name)
            for name in self.tool_map
        }
        return self.tool_schemas, tools_dict

    async def _init_servers(self, configs: dict[str, dict], existing_names: set[str]):
        self.exit_stack = contextlib.AsyncExitStack()
        multi_server = len(configs) > 1

        for name, cfg in configs.items():
            try:
                env = {**os.environ, **cfg.get("env", {})}
                params = StdioServerParameters(
                    command=cfg["command"],
                    args=cfg.get("args", []),
                    env=env,
                )
                read_stream, write_stream = await self.exit_stack.enter_async_context(
                    stdio_client(params)
                )
                session = await self.exit_stack.enter_async_context(
                    ClientSession(read_stream, write_stream)
                )
                await session.initialize()
                self.sessions[name] = session
                self.server_status[name] = "connected"

                tools_resp = await session.list_tools()
                for tool in tools_resp.tools:
                    # Prefix with server name if multiple servers or if collision exists
                    tool_name = (
                        f"{name}__{tool.name}"
                        if (multi_server or tool.name in existing_names)
                        else tool.name
                    )
                    self.tool_map[tool_name] = (name, tool.name)
                    params_schema = (
                        getattr(tool, "input_schema", None)
                        or getattr(tool, "inputSchema", None)
                        or {"type": "object", "properties": {}}
                    )
                    self.tool_schemas.append({
                        "type": "function",
                        "function": {
                            "name": tool_name,
                            "description": tool.description or f"MCP tool from {name}",
                            "parameters": params_schema,
                        },
                    })
            except Exception as e:
                self.server_status[name] = f"Error: {e}"

    def _make_tool_caller(self, full_name: str) -> Callable[..., str]:
        def caller(**kwargs) -> str:
            return self.call_tool(full_name, kwargs)
        return caller

    async def _async_call_tool(self, server_name: str, orig_name: str, arguments: dict) -> str:
        session = self.sessions.get(server_name)
        if not session:
            return f"Error: Server '{server_name}' not connected."
        res = await session.call_tool(orig_name, arguments=arguments)
        parts = []
        for item in getattr(res, "content", []):
            if hasattr(item, "text"):
                parts.append(item.text)
            else:
                parts.append(str(item))
        return "\n".join(parts) if parts else "(no output)"

    def call_tool(self, full_name: str, arguments: dict) -> str:
        """Call an MCP tool synchronously with timeout."""
        if full_name not in self.tool_map:
            return f"Error: Tool '{full_name}' not registered."
        server_name, orig_name = self.tool_map[full_name]
        fut = asyncio.run_coroutine_threadsafe(
            self._async_call_tool(server_name, orig_name, arguments),
            self.loop,
        )
        try:
            return fut.result(timeout=60)
        except Exception as e:
            return f"Error running MCP tool '{full_name}': {e}"

    def get_status(self) -> dict[str, Any]:
        """Summary for /mcp command."""
        return {
            "config": str(self.config_path) if self.config_path else None,
            "servers": self.server_status,
            "tools": list(self.tool_map.keys()),
        }

    def close(self):
        """Clean shutdown of client sessions and event loop."""
        if not self._started:
            return
        self._started = False
        try:
            if self.exit_stack:
                fut = asyncio.run_coroutine_threadsafe(self.exit_stack.aclose(), self.loop)
                fut.result(timeout=5)
        except Exception:
            pass
        finally:
            self.loop.call_soon_threadsafe(self.loop.stop)


# Global instance
mcp_manager = MCPManager()
