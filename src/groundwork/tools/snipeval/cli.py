import argparse
import sys
from pathlib import Path

from groundwork.core.cliparse import UsageParser
from groundwork.core.runner import ToolError, run_tool
from groundwork.tools.snipeval.engine import run_snippet

TOOL, VERSION = "snipeval", "0.1.0"


def handler(args: list[str]) -> dict:
    p = UsageParser(prog=f"groundwork {TOOL}", exit_on_error=False)
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--lang", required=True)
    r.add_argument("--root", default=".")
    r.add_argument("--timeout", type=int, default=30)
    r.add_argument("--code")
    sub.add_parser("self-test")
    try:
        ns = p.parse_args(args)
    except argparse.ArgumentError as e:
        raise ToolError("USAGE", str(e), exit_code=2) from e

    if ns.cmd == "self-test":
        return {"self_test": "pass"}
    # Review-fixed: resolve --root to an absolute path BEFORE the NO_ROOT check. A
    # root-relative path from python_interpreter(root) plus cwd=root in engine.py's
    # subprocess.run causes the child to re-resolve the interpreter path against root
    # a second time on POSIX -> FileNotFoundError. Resolving here makes every downstream
    # path (interpreter, cwd) absolute regardless of platform.
    root = Path(ns.root).resolve()
    if not root.is_dir():
        raise ToolError("NO_ROOT", f"not a directory: {root.as_posix()}", exit_code=2)
    code = ns.code if ns.code is not None else sys.stdin.read()
    return run_snippet(ns.lang, code, root, ns.timeout)


def main(args: list[str]) -> None:
    run_tool(TOOL, VERSION, handler, args)
