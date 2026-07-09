import argparse
from pathlib import Path

from groundwork.core.cliparse import UsageParser
from groundwork.core.runner import ToolError, run_tool
from groundwork.tools.covdiff.analyze import analyze
from groundwork.tools.covdiff.covparse import load_coverage
from groundwork.tools.covdiff.diffparse import git_diff, parse_diff
from groundwork.tools.covdiff.runner import run_coverage

TOOL, VERSION = "covdiff", "0.1.0"


def handler(args: list[str]) -> dict:
    p = UsageParser(prog=f"groundwork {TOOL}", exit_on_error=False)
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check")
    c.add_argument("--root", default=".")
    c.add_argument("--base", default="HEAD")
    c.add_argument("--staged", action="store_true")
    c.add_argument("--coverage-json")
    c.add_argument("--cmd", default="pytest")
    c.add_argument("--min", type=float)
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
    diff_map = parse_diff(git_diff(root, base=ns.base, staged=ns.staged))
    cov_path = (Path(ns.coverage_json) if ns.coverage_json
                else run_coverage(root, ns.cmd))
    if not cov_path.is_absolute():
        cov_path = root / cov_path
    cov_map = load_coverage(cov_path, root)
    report = analyze(diff_map, cov_map)
    if ns.min is not None:
        ratio = report["summary"]["ratio"]
        passed = ratio is None or ratio >= ns.min
        report = {**report, "min": ns.min, "passed": passed}
        if not passed:
            report["_exit_override"] = 1
    return report


def _self_test() -> dict:
    """Analyze a synthetic diff against synthetic coverage - no git, no run."""
    out = analyze({"m.py": {2, 5}},
                  {"m.py": {"executed": {2}, "missing": {5}}})
    f = out["files"][0]
    if f["covered"] != [2] or f["uncovered"] != [5]:
        raise ToolError("SELF_TEST", "analyze produced wrong intersection",
                        detail=out)
    return {"self_test": "pass"}


def main(args: list[str]) -> None:
    run_tool(TOOL, VERSION, handler, args)
