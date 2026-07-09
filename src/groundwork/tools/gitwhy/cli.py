import argparse
import re
from pathlib import Path

from groundwork.core.cliparse import UsageParser
from groundwork.core.runner import ToolError, run_tool
from groundwork.tools.gitwhy.archaeology import explain
from groundwork.tools.gitwhy.churn import churn_report

TOOL, VERSION = "gitwhy", "0.1.0"


def _parse_lines(spec: str) -> tuple[int, int]:
    m = re.fullmatch(r"(\d+)(?:-(\d+))?", spec)
    if not m:
        raise ToolError("USAGE", f"--lines must be N or N-M, got {spec!r}",
                        exit_code=2)
    start = int(m.group(1))
    end = int(m.group(2)) if m.group(2) else start
    if end < start:
        raise ToolError("USAGE", f"--lines end < start: {spec!r}", exit_code=2)
    return start, end


def handler(args: list[str]) -> dict:
    p = UsageParser(prog=f"groundwork {TOOL}", exit_on_error=False)
    sub = p.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("explain")
    e.add_argument("--file", required=True)
    e.add_argument("--lines", required=True)
    e.add_argument("--root", default=".")
    c = sub.add_parser("churn")
    c.add_argument("--root", default=".")
    c.add_argument("--since")
    c.add_argument("--count", type=int, default=200)
    c.add_argument("--top", type=int, default=20)
    c.add_argument("--coverage-json")
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
    if ns.cmd == "explain":
        start, end = _parse_lines(ns.lines)
        return explain(root, ns.file, start, end)
    return churn_report(root, since=ns.since, count=ns.count, top=ns.top,
                        coverage_json=ns.coverage_json)


def _self_test() -> dict:
    """Parse a synthetic blame + refs in memory - no git needed."""
    from groundwork.tools.gitwhy.blame import parse_porcelain, unique_commits
    from groundwork.tools.gitwhy.refs import extract_refs

    porc = ("abc123 1 1 1\nauthor A\nauthor-time 1700000000\n"
            "summary fix: x (#5)\nfilename m.py\n\tcode\n")
    commits = unique_commits(parse_porcelain(porc))
    refs = extract_refs("Fixes #5")
    if len(commits) != 1 or refs != [{"number": 5, "closing": True}]:
        raise ToolError("SELF_TEST", "parsers inconsistent",
                        detail={"commits": commits, "refs": refs})
    return {"self_test": "pass"}


def main(args: list[str]) -> None:
    run_tool(TOOL, VERSION, handler, args)
