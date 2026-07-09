import argparse
from pathlib import Path

from groundwork.core.cliparse import UsageParser
from groundwork.core.runner import ToolError, run_tool
from groundwork.tools.scratchdb import store
from groundwork.tools.scratchdb.pad import (drop_view, list_views, load_file,
                                            query)

TOOL, VERSION = "scratchdb", "0.1.0"


def handler(args: list[str]) -> dict:
    p = UsageParser(prog=f"groundwork {TOOL}", exit_on_error=False)
    sub = p.add_subparsers(dest="cmd", required=True)
    lo = sub.add_parser("load")
    lo.add_argument("--name", required=True)
    lo.add_argument("--file", required=True)
    lo.add_argument("--as", dest="as_name")
    qp = sub.add_parser("q")
    qp.add_argument("--name", required=True)
    qp.add_argument("--sql", required=True)
    qp.add_argument("--limit", type=int, default=1000)
    tb = sub.add_parser("tables")
    tb.add_argument("--name", required=True)
    dr = sub.add_parser("drop")
    dr.add_argument("--name", required=True)
    dr.add_argument("--view")
    sub.add_parser("list")
    sub.add_parser("self-test")
    try:
        ns = p.parse_args(args)
    except argparse.ArgumentError as e:
        raise ToolError("USAGE", str(e), exit_code=2) from e

    if ns.cmd == "self-test":
        return _self_test()
    if ns.cmd == "list":
        return {"pads": store.list_pads()}
    if ns.cmd == "load":
        return load_file(ns.name, Path(ns.file), as_name=ns.as_name)
    if ns.cmd == "q":
        return query(ns.name, ns.sql, limit=ns.limit)
    if ns.cmd == "tables":
        return {"pad": ns.name, "tables": list_views(ns.name)}
    # drop
    if ns.view:
        return drop_view(ns.name, ns.view)
    if not store.drop_pad(ns.name):
        raise ToolError("NO_PAD", f"no scratchpad {ns.name!r}; "
                                  f"existing: {store.list_pads()}", exit_code=4)
    return {"dropped_pad": ns.name}


def _self_test() -> dict:
    """Load a synthesized CSV into a temp pad, query it, drop it."""
    import os
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        prev = os.environ.get("GROUNDWORK_DATA_DIR")
        os.environ["GROUNDWORK_DATA_DIR"] = str(Path(td) / "data")
        try:
            csv = Path(td) / "st.csv"
            csv.write_text("a,b\n1,2\n3,4\n", encoding="utf-8")
            load_file("_selftest", csv, as_name="t")
            out = query("_selftest", "select sum(b) s from t")
            store.drop_pad("_selftest")
        finally:
            if prev is None:
                os.environ.pop("GROUNDWORK_DATA_DIR", None)
            else:
                os.environ["GROUNDWORK_DATA_DIR"] = prev
    if out["rows"][0][0] != 6:
        raise ToolError("SELF_TEST", "scratchpad round trip failed", detail=out)
    return {"self_test": "pass"}


def main(args: list[str]) -> None:
    run_tool(TOOL, VERSION, handler, args)
