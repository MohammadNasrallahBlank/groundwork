"""`cartographer hook` — reads the hook event JSON on stdin, emits a map as
additionalContext. Never raises out to the session: any failure yields empty
context and exit 0, so a hook error can't disrupt a session."""
import argparse
import json
import sys
from pathlib import Path

from groundwork.core.cache import Cache
from groundwork.core.hookio import emit_additional_context

_EVENTS = {"session-start": "SessionStart", "post-compact": "PostCompact"}


def run_hook(argv: list[str]) -> None:
    """Read the hook stdin JSON, build a budgeted map for its cwd, emit it."""
    p = argparse.ArgumentParser(prog="groundwork cartographer hook")
    p.add_argument("--event", required=True, choices=sorted(_EVENTS))
    p.add_argument("--budget", type=int, default=1500)
    ns, _ = p.parse_known_args(argv)
    event_name = _EVENTS[ns.event]
    text = ""
    try:
        # Read bytes, not text: the event JSON is UTF-8 regardless of the
        # console locale (Windows text-mode stdin is cp1252), and utf-8-sig
        # strips the BOM that Windows PowerShell 5.1 pipes prepend.
        raw = sys.stdin.buffer.read().decode("utf-8-sig", errors="replace")
        payload = json.loads(raw or "{}")
        root = Path(payload.get("cwd") or ".")
        if root.is_dir():
            from groundwork.tools.cartographer.mapper import build_map
            text = build_map(root, ns.budget, cache=Cache())["map"]
    except Exception:  # a hook must never break the session
        text = ""
    emit_additional_context(event_name, text)
    raise SystemExit(0)
