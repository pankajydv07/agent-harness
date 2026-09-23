# My Agent Harness

A minimal coding agent harness built with Python, designed for LLM-powered agent interactions and tool execution.

## Features

- LLM integration (OpenAI compatible)
- Tool execution framework
- Rich-based terminal user interface
- Context compaction for long conversations
- Modular agent architecture
- Sandboxed tool execution
- Interactive prompts and command handling

## Project Structure

- `main.py` - Entry point
- `myagent/` - Core agent modules
  - `agent.py` - Main agent logic
  - `tools.py` - Tool definitions and execution
  - `sandbox.py` - Sandboxed tool execution
  - `ui.py` - Rich-based terminal UI
  - `prompt.py` - Prompt management and templating
  - `context.py` - Context handling and compaction
- `tests/` - Unit tests
- `scripts/` - Utility scripts

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/agent-harness.git
cd agent-harness

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .
```

## Configuration

Create a `.env` file based on `.env.example`:

```bash
cp .env.example .env
# Edit .env to add your API keys and configuration
```

## Usage

```bash
# Run the agent
python -m myagent
```

Or if installed as a package:

```bash
myagent
```

## Development

### Running Tests

```bash
# Install test dependencies
pip install -e ".[test]"

# Run tests
pytest
```

### Code Formatting

We use [Ruff](https://docs.astral.sh/ruff/) for linting and formatting:

```bash
# Check linting
ruff check .

# Format code
ruff format .
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [Rich](https://github.com/Textualize/rich) for beautiful terminal interfaces
- Inspired by various agent frameworks and LLM applications