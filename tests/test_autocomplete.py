from prompt_toolkit.document import Document
from myagent.prompt import SlashCommandCompleter, COMMAND_TREE
from myagent import commands
from myagent import config


def test_completer_top_level_all():
    completer = SlashCommandCompleter()
    doc = Document("/", cursor_position=1)
    completions = list(completer.get_completions(doc, None))
    completed_texts = [c.text for c in completions]

    for cmd in COMMAND_TREE:
        assert cmd in completed_texts


def test_completer_top_level_prefix():
    completer = SlashCommandCompleter()
    doc = Document("/mc", cursor_position=3)
    completions = list(completer.get_completions(doc, None))
    completed_texts = [c.text for c in completions]
    assert completed_texts == ["/mcp"]


def test_completer_child_options_mcp():
    completer = SlashCommandCompleter()
    doc = Document("/mcp ", cursor_position=5)
    completions = list(completer.get_completions(doc, None))
    completed_texts = [c.text for c in completions]

    assert "status" in completed_texts
    assert "reload" in completed_texts
    assert "servers" in completed_texts
    assert "tools" in completed_texts


def test_completer_child_options_config():
    completer = SlashCommandCompleter()
    doc = Document("/config mod", cursor_position=11)
    completions = list(completer.get_completions(doc, None))
    completed_texts = [c.text for c in completions]
    assert completed_texts == ["model"]


def test_command_config_set_model():
    original_model = config.MODEL
    try:
        handled, _ = commands.handle("/config model test-model-42", [])
        assert handled is True
        assert config.MODEL == "test-model-42"
    finally:
        config.MODEL = original_model


def test_command_compact_thresholds():
    handled, _ = commands.handle("/compact thresholds", [])
    assert handled is True
