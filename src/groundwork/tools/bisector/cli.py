import argparse
from pathlib import Path

from groundwork.core.cliparse import UsageParser
from groundwork.core.runner import ToolError, run_tool
from groundwork.tools.bisector.runner import run_bisect

TOOL, VERSION = "bisector", "0.1.0"


def _skip_codes(spec: str | None) -> set[int]:
    if not spec:
        return {125}
    try:
        return {int(x) for x in spec.split(",") if x.strip()}
    except ValueError:
        raise ToolError("USAGE", f"--skip-codes must be comma-separated ints, "
                                 f"got {spec!r}", exit_code=2) from None


def handler(args: list[str]) -> dict:
    p = UsageParser(prog=f"groundwork {TOOL}", exit_on_error=False)
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--good", required=True)
    r.add_argument("--bad", required=True)
    r.add_argument("--oracle", default="groundwork verify run")
    r.add_argument("--root", default=".")
    r.add_argument("--skip-codes")
    sub.add_parser("self-test")
    try:
        ns = p.parse_args(args)
    except argparse.ArgumentError as e:
        raise ToolError("USAGE", str(e), exit_code=2) from e

    if ns.cmd == "self-test":
        return _self_test()
    root = Path(ns.root).resolve()
    if not root.is_dir():
        raise ToolError("NO_ROOT", f"not a directory: {root.as_posix()}", exit_code=2)
    return run_bisect(root, ns.good, ns.bad, ns.oracle,
                      skip_codes=_skip_codes(ns.skip_codes))


def _self_test() -> dict:
    """Pure verdict-mapping check - no git."""
    from groundwork.tools.bisector.bisect import map_verdict
    if (map_verdict(0, {125}), map_verdict(1, {125}),
            map_verdict(125, {125})) != ("good", "bad", "skip"):
        raise ToolError("SELF_TEST", "verdict mapping wrong")
    return {"self_test": "pass"}


def main(args: list[str]) -> None:
    run_tool(TOOL, VERSION, handler, args)
