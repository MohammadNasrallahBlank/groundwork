import argparse
from pathlib import Path

from groundwork.core.envelope import EXIT_ERROR, EXIT_MISSING_DEP
from groundwork.core.runner import ToolError, run_tool
from groundwork.tools.verify.adapters import detect_adapters, register
from groundwork.tools.verify.adapters.junit_ingest import ingest_junit_file
from groundwork.tools.verify.adapters.pytest_adapter import PytestAdapter
from groundwork.tools.verify.adapters.ruff_adapter import RuffAdapter
from groundwork.tools.verify.gitscope import changed_files
from groundwork.tools.verify.models import summarize

TOOL, VERSION = "verify", "0.1.0"
register(PytestAdapter())
register(RuffAdapter())


def handler(args: list[str]) -> dict:
    p = argparse.ArgumentParser(prog="groundwork verify", exit_on_error=False)
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--root", default=".")
    r.add_argument("--changed-only", action="store_true")
    r.add_argument("--junit", help="ingest an existing JUnit XML instead of running adapters")
    sub.add_parser("self-test")
    try:
        ns = p.parse_args(args)
    except (argparse.ArgumentError, SystemExit) as e:
        raise ToolError("USAGE", str(e), exit_code=2) from e

    if ns.cmd == "self-test":
        return {"self_test": "pass"}

    root = Path(ns.root).resolve()
    diags = []
    if ns.junit:
        diags = ingest_junit_file(Path(ns.junit))
    else:
        adapters = detect_adapters(root)
        if not adapters:
            raise ToolError("NO_ADAPTERS",
                            f"no verification adapters detected in {root.as_posix()}",
                            exit_code=EXIT_MISSING_DEP)
        changed = changed_files(root) if ns.changed_only else None
        for a in adapters:
            diags.extend(a.run(root, changed))

    summary = summarize(diags)
    result = {"summary": summary, "diagnostics": [d.to_dict() for d in diags]}
    if not summary["ok"]:
        # Verdict travels in the exit code; the envelope stays ok=True because the
        # tool itself succeeded. Raising ToolError here would hide the diagnostics,
        # so we return data and let run_tool exit 0 — then override via a sentinel.
        result["_exit_override"] = EXIT_ERROR
    return result


def main(args: list[str]) -> None:
    run_tool(TOOL, VERSION, handler, args)
