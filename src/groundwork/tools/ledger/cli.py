import argparse
from pathlib import Path

from groundwork.core.cliparse import UsageParser
from groundwork.core.runner import ToolError, run_tool
from groundwork.tools.ledger.report import build_report
from groundwork.tools.ledger.store import add_claim, record_run, resolve_claim

TOOL, VERSION = "ledger", "0.1.0"


def handler(args: list[str]) -> dict:
    p = UsageParser(prog=f"groundwork {TOOL}", exit_on_error=False)
    sub = p.add_subparsers(dest="cmd", required=True)
    cl = sub.add_parser("claim")
    cl.add_argument("--statement", required=True)
    cl.add_argument("--confidence", required=True)
    cl.add_argument("--source")
    cl.add_argument("--tags")
    cl.add_argument("--at")
    cl.add_argument("--root", default=".")
    rs = sub.add_parser("resolve")
    rs.add_argument("--id", type=int, required=True)
    rs.add_argument("--outcome", required=True)
    rs.add_argument("--at")
    rs.add_argument("--root", default=".")
    rc = sub.add_parser("record")
    rc.add_argument("--tool", required=True)
    rc.add_argument("--cache")
    rc.add_argument("--avoided", action="store_true")
    rc.add_argument("--caught", action="store_true")
    rc.add_argument("--at")
    rc.add_argument("--root", default=".")
    rp = sub.add_parser("report")
    rp.add_argument("--bins", type=int, default=5)
    rp.add_argument("--root", default=".")
    sub.add_parser("self-test")
    try:
        ns = p.parse_args(args)
    except argparse.ArgumentError as e:
        raise ToolError("USAGE", str(e), exit_code=2) from e

    if ns.cmd == "self-test":
        return _self_test()
    root = _root(ns.root)
    if ns.cmd == "claim":
        return add_claim(root, statement=ns.statement, confidence=ns.confidence,
                         source=ns.source, tags=ns.tags, at=ns.at)
    if ns.cmd == "resolve":
        if ns.outcome not in ("true", "false"):
            raise ToolError("USAGE", "--outcome must be true or false",
                            exit_code=2)
        return resolve_claim(root, ns.id, ns.outcome == "true", at=ns.at)
    if ns.cmd == "record":
        return record_run(root, tool=ns.tool, cache=ns.cache,
                          avoided=ns.avoided, caught=ns.caught, at=ns.at)
    return build_report(root, bins=ns.bins)


def _root(root: str) -> Path:
    p = Path(root).resolve()
    if not p.is_dir():
        raise ToolError("NO_ROOT", f"not a directory: {p.as_posix()}", exit_code=2)
    return p


def _self_test() -> dict:
    """A calibrated claim/resolve/report round trip in a temp ledger."""
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        add_claim(root, statement="s", confidence=1.0, source=None, tags=None,
                  at="2026-01-01T00:00:00Z")
        resolve_claim(root, 1, True, at="2026-01-01T00:00:00Z")
        rep = build_report(root, bins=5)
    if rep["calibration"]["brier"] != 0.0:
        raise ToolError("SELF_TEST", "brier of a perfect claim should be 0",
                        detail=rep)
    return {"self_test": "pass"}


def main(args: list[str]) -> None:
    run_tool(TOOL, VERSION, handler, args)
