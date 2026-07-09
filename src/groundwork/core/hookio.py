"""Emit the JSON Claude Code hooks require to inject context.

This is deliberately NOT the tool envelope: SessionStart/PostCompact read a
hook's stdout as JSON and add `hookSpecificOutput.additionalContext` to the
session (re-verified against code.claude.com/docs/en/hooks at build time,
2026-07-08).
"""
import json


def emit_additional_context(event_name: str, text: str) -> None:
    """Print the hook context-injection JSON for ``event_name`` to stdout."""
    print(json.dumps({"hookSpecificOutput": {"hookEventName": event_name,
                                             "additionalContext": text}}))
