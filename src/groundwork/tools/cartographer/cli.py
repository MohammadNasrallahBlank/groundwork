import argparse
from pathlib import Path

from groundwork.core.cache import Cache
from groundwork.core.cliparse import UsageParser
from groundwork.core.runner import ToolError, run_tool
from groundwork.tools.cartographer.mapper import build_map

TOOL, VERSION = "cartographer", "0.1.0"


def handler(args: list[str]) -> dict:
    p = UsageParser(prog=f"groundwork {TOOL}", exit_on_error=False)
    sub = p.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("map")
    m.add_argument("--root", default=".")
    m.add_argument("--budget", type=int, default=1500)
    m.add_argument("--no-cache", action="store_true")
    sub.add_parser("self-test")
    try:
        ns = p.parse_args(args)
    except argparse.ArgumentError as e:
        raise ToolError("USAGE", str(e), exit_code=2) from e

    if ns.cmd == "self-test":
        return {"self_test": "pass"}
    # Resolve before the NO_ROOT check so the error (and everything downstream)
    # reports an absolute path — same review fix as snipeval's cli.
    root = Path(ns.root).resolve()
    if not root.is_dir():
        raise ToolError("NO_ROOT", f"not a directory: {root.as_posix()}", exit_code=2)
    cache = None if ns.no_cache else Cache()
    return build_map(root, ns.budget, cache=cache)


def main(args: list[str]) -> None:
    # `hook` speaks the Claude Code hook protocol, not the envelope: route it
    # around run_tool so its stdout is the hookSpecificOutput JSON alone.
    if args and args[0] == "hook":
        from groundwork.tools.cartographer.hookcli import run_hook
        run_hook(args[1:])
        return
    run_tool(TOOL, VERSION, handler, args)
