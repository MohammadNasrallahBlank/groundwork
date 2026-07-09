import argparse
import subprocess
import sys
from pathlib import Path

from groundwork.core.cliparse import UsageParser
from groundwork.core.runner import ToolError, run_tool
from groundwork.tools.covdiff.diffparse import git_diff, parse_diff
from groundwork.tools.mutcheck.mutate import iter_mutants
from groundwork.tools.mutcheck.runner import check_file

TOOL, VERSION = "mutcheck", "0.1.0"


def _run_tests_factory(root: Path, cmd: str, timeout: int):
    import os
    parts = cmd.split()
    # PYTHONDONTWRITEBYTECODE: without it, a mutant run can import a stale .pyc
    # written by the baseline run (mtime resolution is coarse on Windows), so
    # every mutant would look "survived". Reading source fresh each run is the
    # fix (build-time finding). -B belt-and-braces for the pytest launcher.
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}

    def run_tests():
        try:
            proc = subprocess.run([sys.executable, "-B", "-m", *parts], cwd=root,
                                  capture_output=True, text=True, env=env,
                                  encoding="utf-8", errors="replace",
                                  timeout=timeout)
        except subprocess.TimeoutExpired:
            return None                          # indeterminate -> INVALID
        except OSError as e:
            raise ToolError("NO_TEST_CMD", f"cannot run {cmd!r}: {e}",
                            exit_code=3) from e
        return proc.returncode == 0

    return run_tests


def handler(args: list[str]) -> dict:
    p = UsageParser(prog=f"groundwork {TOOL}", exit_on_error=False)
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check")
    c.add_argument("--root", default=".")
    c.add_argument("--base", default="HEAD")
    c.add_argument("--staged", action="store_true")
    c.add_argument("--cmd", default="pytest -q")
    c.add_argument("--max-mutants", type=int, default=25)
    c.add_argument("--timeout", type=int, default=120)
    c.add_argument("--min-kill", type=float)
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
    run_tests = _run_tests_factory(root, ns.cmd, ns.timeout)

    # baseline must be green
    if run_tests() is not True:
        raise ToolError("BASELINE_RED",
                        "the test suite does not pass unmutated; fix it before "
                        "mutation testing", exit_code=4)

    diff_map = parse_diff(git_diff(root, base=ns.base, staged=ns.staged))
    files, errors = [], []
    total_killed = total_survived = 0
    for rel, lines in sorted(diff_map.items()):
        if not rel.endswith(".py") or not lines:
            continue
        fpath = root / rel
        if not fpath.is_file():
            continue
        try:
            iter_mutants(fpath.read_text(encoding="utf-8"), lines)
        except (ValueError, SyntaxError) as e:
            errors.append({"file": rel, "error": str(e)})
            continue
        rep = check_file(fpath, lines, run_tests, max_mutants=ns.max_mutants)
        if rep["mutants_total"]:
            files.append(rep)
            total_killed += rep["killed"]
            total_survived += rep["survived"]

    decided = total_killed + total_survived
    kill_ratio = round(total_killed / decided, 4) if decided else None
    out = {"files": files, "errors": errors,
           "summary": {"killed": total_killed, "survived": total_survived,
                       "kill_ratio": kill_ratio}}
    if ns.min_kill is not None:
        passed = kill_ratio is None or kill_ratio >= ns.min_kill
        out["min_kill"] = ns.min_kill
        out["passed"] = passed
        if not passed:
            out["_exit_override"] = 1
    return out


def _self_test() -> dict:
    """Mutate a synthetic source in memory; confirm a survivor vs a killer."""
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "m.py"
        f.write_text("def f(x):\n    return x < 10\n", encoding="utf-8",
                     newline="\n")
        weak = check_file(f, {2}, lambda: True)
        strong = check_file(f, {2},
                            lambda: "x < 10" in f.read_text(encoding="utf-8"))
    if weak["survived"] != 1 or strong["killed"] != 1:
        raise ToolError("SELF_TEST", "mutation classification wrong",
                        detail={"weak": weak, "strong": strong})
    return {"self_test": "pass"}


def main(args: list[str]) -> None:
    run_tool(TOOL, VERSION, handler, args)
