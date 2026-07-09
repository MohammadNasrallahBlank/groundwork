"""run_tool: call a handler, print exactly one envelope on stdout, exit correctly."""
import json
import os
import time
from pathlib import Path
from typing import Any, Callable

from groundwork.core import envelope as env

Handler = Callable[[list[str]], dict[str, Any]]


class ToolError(Exception):
    def __init__(self, code: str, message: str, *, exit_code: int = env.EXIT_ERROR,
                 detail: Any = None):
        super().__init__(message)
        self.code, self.exit_code, self.detail = code, exit_code, detail


def run_tool(tool: str, version: str, handler: Handler, args: list[str]) -> None:
    start = time.perf_counter()
    cache_state = "off"
    exit_override = None
    ok_run = False
    try:
        data = handler(args)
        cache_state = data.pop("_cache", "off") if isinstance(data, dict) else "off"
        exit_override = data.pop("_exit_override", None) if isinstance(data, dict) else None
        out = env.ok(data, tool=tool, version=version,
                     elapsed_ms=int((time.perf_counter() - start) * 1000), cache=cache_state)
        code = exit_override if exit_override is not None else env.EXIT_OK
        ok_run = True
    except ToolError as e:
        out = env.err(e.code, str(e), detail=e.detail, tool=tool, version=version,
                      elapsed_ms=int((time.perf_counter() - start) * 1000), cache=cache_state)
        code = e.exit_code
    except Exception as e:  # noqa: BLE001 — the contract demands JSON even on crashes
        out = env.err("INTERNAL", f"{type(e).__name__}: {e}", tool=tool, version=version,
                      elapsed_ms=int((time.perf_counter() - start) * 1000), cache=cache_state)
        code = env.EXIT_ERROR
    print(json.dumps(out))
    _maybe_record(tool, cache_state, ok=ok_run, exit_override=exit_override)
    raise SystemExit(code)


def _maybe_record(tool: str, cache: str, *, ok: bool, exit_override: Any) -> None:
    """Opt-in, best-effort proof-of-value feed.

    Off unless GROUNDWORK_LEDGER_ROOT is set — so this is a no-op for every
    existing caller and preserves the ledger's local-only, opt-in promise.
    Records nothing for the ledger tool itself (that would recurse and pollute
    its own dataset), and swallows every error: a recording failure must never
    turn a working tool into a broken one. Recorded after the envelope is
    printed so it never inflates the reported elapsed_ms.

    Semantics: a successful run did deterministic mechanical work in place of a
    model inference, so avoided=ok; a non-zero exit override on a success path
    is a verify/gate tool reporting a real problem it caught.
    """
    root = os.environ.get("GROUNDWORK_LEDGER_ROOT")
    if not root or tool == "ledger":
        return
    try:
        from groundwork.tools.ledger.store import record_run

        caught = bool(ok and exit_override not in (None, 0))
        record_run(Path(root), tool=tool, cache=cache, avoided=ok,
                   caught=caught, at=None)
    except Exception:  # noqa: BLE001 — recording must never break the tool
        pass
