import argparse
from pathlib import Path

from groundwork.core.cliparse import UsageParser
from groundwork.core.envelope import EXIT_ESCALATE
from groundwork.core.runner import ToolError, run_tool
from groundwork.tools.envprobe.snapshot import (build_snapshot, diff_env,
                                                load_baseline, render_digest,
                                                save_baseline)

TOOL, VERSION = "envprobe", "0.1.0"


def _root(ns) -> Path:
    root = Path(ns.root)
    if not root.is_dir():
        raise ToolError("NO_ROOT", f"not a directory: {root.as_posix()}", exit_code=2)
    return root


def handler(args: list[str]) -> dict:
    p = UsageParser(prog=f"groundwork {TOOL}", exit_on_error=False)
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("snapshot", "diff", "digest"):
        c = sub.add_parser(name)
        c.add_argument("--root", default=".")
    sub.add_parser("self-test")
    try:
        ns = p.parse_args(args)
    except argparse.ArgumentError as e:
        raise ToolError("USAGE", str(e), exit_code=2) from e

    if ns.cmd == "self-test":
        return {"self_test": "pass"}
    root = _root(ns)
    if ns.cmd == "snapshot":
        snap = build_snapshot(root)
        save_baseline(snap)
        return snap
    if ns.cmd == "digest":
        return {"digest": render_digest(build_snapshot(root))}
    baseline = load_baseline(root)
    if baseline is None:
        raise ToolError("NO_BASELINE",
                        f"no baseline for {root.resolve().as_posix()}; "
                        "run `groundwork envprobe snapshot` first",
                        exit_code=EXIT_ESCALATE)
    return diff_env(baseline, build_snapshot(root))


def main(args: list[str]) -> None:
    run_tool(TOOL, VERSION, handler, args)
