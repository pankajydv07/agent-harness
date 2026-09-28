import json
import sys
from pathlib import Path
import pytest
from myagent.mcp import MCPManager, parse_mcp_config


def test_parse_mcp_config(tmp_path: Path):
    config_file = tmp_path / "mcp.json"
    config_file.write_text(
        json.dumps({
            "mcpServers": {
                "test_srv": {
                    "command": "python",
                    "args": ["-c", "print('hello')"],
                    "env": {"TEST_VAR": "1"}
                }
            }
        }),
        encoding="utf-8",
    )

    parsed = parse_mcp_config(config_file)
    assert "test_srv" in parsed
    assert parsed["test_srv"]["command"] == "python"
    assert parsed["test_srv"]["env"]["TEST_VAR"] == "1"


def test_mcp_manager_no_config(tmp_path: Path):
    non_existent = tmp_path / "non_existent.json"
    manager = MCPManager(config_path=non_existent)
    schemas, tools = manager.start()
    assert schemas == []
    assert tools == {}
    status = manager.get_status()
    assert status["servers"] == {}


def test_mcp_integration(tmp_path: Path):
    # Create a minimal stdio MCP server script
    server_script = tmp_path / "dummy_server.py"
    server_script.write_text(
        """
from mcp.server.mcpserver import MCPServer

server = MCPServer("calculator")

@server.tool()
def add(a: int, b: int) -> int:
    '''Add two integers.'''
    return a + b

if __name__ == "__main__":
    server.run(transport="stdio")
""",
        encoding="utf-8",
    )

    config_file = tmp_path / "mcp.json"
    config_file.write_text(
        json.dumps({
            "mcpServers": {
                "calc": {
                    "command": sys.executable,
                    "args": [str(server_script)],
                }
            }
        }),
        encoding="utf-8",
    )

    manager = MCPManager(config_path=config_file)
    try:
        schemas, tools = manager.start()
        assert len(schemas) == 1
        assert "add" in tools

        schema = schemas[0]
        assert schema["type"] == "function"
        assert schema["function"]["name"] == "add"
        assert "parameters" in schema["function"]

        # Call the tool
        result = tools["add"](a=5, b=7)
        assert "12" in result

        # Check status
        status = manager.get_status()
        assert status["servers"].get("calc") == "connected"
        assert "add" in status["tools"]
    finally:
        manager.close()


def test_commands_mcp_handler():
    from myagent import commands
    messages = [{"role": "system", "content": "hi"}]
    handled, updated = commands.handle("/mcp", messages)
    assert handled is True
    assert updated == messages

