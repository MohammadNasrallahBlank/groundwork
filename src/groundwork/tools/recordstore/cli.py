import argparse
from pathlib import Path

from groundwork.core.cliparse import UsageParser
from groundwork.core.runner import ToolError, run_tool
from groundwork.tools.recordstore.records import (add_decision, add_event,
                                                  add_measurement, query,
                                                  timeline)

TOOL, VERSION = "recordstore", "0.1.0"


def _add_common(sp):
    sp.add_argument("--root", default=".")
    sp.add_argument("--tags")
    sp.add_argument("--at")


def handler(args: list[str]) -> dict:
    p = UsageParser(prog=f"groundwork {TOOL}", exit_on_error=False)
    sub = p.add_subparsers(dest="cmd", required=True)

    add = sub.add_parser("add")
    addsub = add.add_subparsers(dest="rtype", required=True)
    dec = addsub.add_parser("decision")
    dec.add_argument("--subject", required=True)
    dec.add_argument("--choice", required=True)
    dec.add_argument("--status", default="open")
    dec.add_argument("--rationale")
    _add_common(dec)
    mea = addsub.add_parser("measurement")
    mea.add_argument("--metric", required=True)
    mea.add_argument("--value", required=True)
    mea.add_argument("--unit")
    _add_common(mea)
    evt = addsub.add_parser("event")
    evt.add_argument("--name", required=True)
    evt.add_argument("--outcome")
    _add_common(evt)

    qp = sub.add_parser("query")
    qp.add_argument("--root", default=".")
    qp.add_argument("--type")
    qp.add_argument("--status")
    qp.add_argument("--label-like")
    qp.add_argument("--tag")
    qp.add_argument("--since")
    qp.add_argument("--until")
    qp.add_argument("--limit", type=int, default=100)
    tl = sub.add_parser("timeline")
    tl.add_argument("--root", default=".")
    tl.add_argument("--type")
    tl.add_argument("--since")
    tl.add_argument("--until")
    tl.add_argument("--desc", action="store_true")
    tl.add_argument("--limit", type=int, default=100)
    sub.add_parser("self-test")

    try:
        ns = p.parse_args(args)
    except argparse.ArgumentError as e:
        raise ToolError("USAGE", str(e), exit_code=2) from e

    if ns.cmd == "self-test":
        return _self_test()
    if ns.cmd == "query":
        root = _root(ns.root)
        return {"records": query(root, type=ns.type, status=ns.status,
                                 label_like=ns.label_like, tag=ns.tag,
                                 since=ns.since, until=ns.until, limit=ns.limit)}
    if ns.cmd == "timeline":
        root = _root(ns.root)
        return {"timeline": timeline(root, type=ns.type, since=ns.since,
                                     until=ns.until, desc=ns.desc, limit=ns.limit)}
    # add
    root = _root(ns.root)
    if ns.rtype == "decision":
        return add_decision(root, subject=ns.subject, choice=ns.choice,
                            status=ns.status, rationale=ns.rationale,
                            tags=ns.tags, at=ns.at)
    if ns.rtype == "measurement":
        return add_measurement(root, metric=ns.metric, value=ns.value,
                               unit=ns.unit, tags=ns.tags, at=ns.at)
    return add_event(root, name=ns.name, outcome=ns.outcome, tags=ns.tags,
                     at=ns.at)


def _root(root: str) -> Path:
    p = Path(root).resolve()
    if not p.is_dir():
        raise ToolError("NO_ROOT", f"not a directory: {p.as_posix()}", exit_code=2)
    return p


def _self_test() -> dict:
    """Add one of each type into a temp store, query it back."""
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        add_decision(root, subject="s", choice="c", status="accepted",
                     at="2026-01-01T00:00:00Z")
        add_measurement(root, metric="m", value=1.0, at="2026-01-01T00:00:01Z")
        add_event(root, name="e", outcome="ok", at="2026-01-01T00:00:02Z")
        recs = query(root)
        tl = timeline(root)
    if len(recs) != 3 or len(tl) != 3:
        raise ToolError("SELF_TEST", "record round trip failed",
                        detail={"records": len(recs), "timeline": len(tl)})
    return {"self_test": "pass"}


def main(args: list[str]) -> None:
    run_tool(TOOL, VERSION, handler, args)
