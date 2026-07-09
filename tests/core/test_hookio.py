import json

from groundwork.core.hookio import emit_additional_context


def test_emit_additional_context_shape(capsys):
    emit_additional_context("SessionStart", "hello map")
    out = json.loads(capsys.readouterr().out)
    assert out == {"hookSpecificOutput": {"hookEventName": "SessionStart",
                                          "additionalContext": "hello map"}}
