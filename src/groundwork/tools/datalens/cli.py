import argparse
from pathlib import Path

from groundwork.core.cliparse import UsageParser
from groundwork.core.runner import ToolError, run_tool
from groundwork.tools.datalens.compare import compare_datasets
from groundwork.tools.datalens.profile import profile_dataset

TOOL, VERSION = "datalens", "0.1.0"


def handler(args: list[str]) -> dict:
    p = UsageParser(prog=f"groundwork {TOOL}", exit_on_error=False)
    sub = p.add_subparsers(dest="cmd", required=True)
    pr = sub.add_parser("profile")
    pr.add_argument("--file", required=True)
    pr.add_argument("--table")
    pr.add_argument("--balance-max", type=int, default=20)
    cm = sub.add_parser("compare")
    cm.add_argument("--a", required=True)
    cm.add_argument("--b", required=True)
    cm.add_argument("--table-a")
    cm.add_argument("--table-b")
    cm.add_argument("--bins", type=int, default=10)
    sub.add_parser("self-test")
    try:
        ns = p.parse_args(args)
    except argparse.ArgumentError as e:
        raise ToolError("USAGE", str(e), exit_code=2) from e

    if ns.cmd == "self-test":
        return _self_test()
    if ns.cmd == "profile":
        return profile_dataset(Path(ns.file), table=ns.table,
                               balance_max=ns.balance_max)
    return compare_datasets(Path(ns.a), Path(ns.b), table_a=ns.table_a,
                            table_b=ns.table_b, bins=ns.bins)


def _self_test() -> dict:
    """Profile a synthesized CSV via a temp file; no external inputs."""
    import tempfile

    content = "id,score,cat\n1,10.0,x\n2,20.0,y\n3,,x\n"
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "selftest.csv"
        p.write_text(content, encoding="utf-8")
        out = profile_dataset(p)
    if out["rows"] != 3 or out["columns"] != 3:
        raise ToolError("SELF_TEST", "profile shape unexpected", detail=out)
    return {"self_test": "pass"}


def main(args: list[str]) -> None:
    run_tool(TOOL, VERSION, handler, args)
