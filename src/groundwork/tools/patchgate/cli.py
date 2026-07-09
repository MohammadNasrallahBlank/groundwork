import argparse
import sys
from pathlib import Path

from groundwork.core.cliparse import UsageParser
from groundwork.core.runner import ToolError, run_tool
from groundwork.tools.patchgate.checks import check_content
from groundwork.tools.patchgate.diffcheck import check_diff

TOOL, VERSION = "patchgate", "0.1.0"


def _read_arg_or_stdin(path_arg: str | None, what: str) -> str:
    if path_arg:
        p = Path(path_arg)
        if not p.is_file():
            raise ToolError("USAGE", f"no such {what}: {p.as_posix()}", exit_code=2)
        return p.read_text(encoding="utf-8")
    return sys.stdin.read()


def handler(args: list[str]) -> dict:
    p = UsageParser(prog=f"groundwork {TOOL}", exit_on_error=False)
    sub = p.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("check-diff")
    d.add_argument("--diff")
    d.add_argument("--root", default=".")
    c = sub.add_parser("check-content")
    c.add_argument("--file", required=True)
    c.add_argument("--content-file")
    sub.add_parser("self-test")
    try:
        ns = p.parse_args(args)
    except argparse.ArgumentError as e:
        raise ToolError("USAGE", str(e), exit_code=2) from e

    if ns.cmd == "self-test":
        return _self_test()
    if ns.cmd == "check-content":
        res = check_content(ns.file, _read_arg_or_stdin(ns.content_file, "content file"))
        if res["checked"] and not res["ok"]:
            res["_exit_override"] = 1
        return res
    root = Path(ns.root).resolve()
    if not root.is_dir():
        raise ToolError("NO_ROOT", f"not a directory: {root.as_posix()}", exit_code=2)
    return check_diff(root, _read_arg_or_stdin(ns.diff, "diff file"))


def _self_test() -> dict:
    """Prove the check ladder's verdicts are consistent - pure, no I/O."""
    good = check_content("a.py", "def f():\n    return 1\n")
    bad = check_content("a.py", "def f(:\n")
    if not good["ok"] or bad["ok"]:
        raise ToolError("SELF_TEST", "check ladder verdicts inconsistent",
                        detail={"good": good, "bad": bad})
    return {"self_test": "pass"}


def main(args: list[str]) -> None:
    # `hook` speaks the PreToolUse permission protocol, not the envelope:
    # route it around run_tool (the sanctioned hook exception, as cartographer).
    if args and args[0] == "hook":
        from groundwork.tools.patchgate.hookcli import run_hook
        run_hook(args[1:])
        return
    run_tool(TOOL, VERSION, handler, args)
