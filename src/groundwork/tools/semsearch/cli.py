import argparse
import sqlite3
from pathlib import Path

from groundwork.core.cliparse import UsageParser
from groundwork.core.runner import ToolError, run_tool
from groundwork.tools.semsearch import _DEFAULT_MODEL
from groundwork.tools.semsearch.embed import model_available, pull_model
from groundwork.tools.semsearch.index import (NO_EXT_MSG, build_index,
                                              loadable_extensions_available)
from groundwork.tools.semsearch.search import search

TOOL, VERSION = "semsearch", "0.1.0"


def handler(args: list[str]) -> dict:
    p = UsageParser(prog=f"groundwork {TOOL}", exit_on_error=False)
    sub = p.add_subparsers(dest="cmd", required=True)
    ix = sub.add_parser("index")
    ix.add_argument("--root", default=".")
    ix.add_argument("--model", default=_DEFAULT_MODEL)
    ix.add_argument("--rebuild", action="store_true")
    q = sub.add_parser("query")
    q.add_argument("--q", required=True)
    q.add_argument("--root", default=".")
    q.add_argument("--k", type=int, default=10)
    q.add_argument("--min-score", type=float)
    mo = sub.add_parser("models")
    msub = mo.add_subparsers(dest="mcmd")
    pull = msub.add_parser("pull")
    pull.add_argument("--model", default=_DEFAULT_MODEL)
    sub.add_parser("self-test")
    try:
        ns = p.parse_args(args)
    except argparse.ArgumentError as e:
        raise ToolError("USAGE", str(e), exit_code=2) from e

    if ns.cmd == "self-test":
        return _self_test()
    if ns.cmd == "models":
        if getattr(ns, "mcmd", None) == "pull":
            return pull_model(ns.model)
        return {"default_model": _DEFAULT_MODEL,
                "default_available": model_available(_DEFAULT_MODEL)}
    root = Path(ns.root).resolve()
    if not root.is_dir():
        raise ToolError("NO_ROOT", f"not a directory: {root.as_posix()}", exit_code=2)
    if ns.cmd == "index":
        return build_index(root, ns.model, rebuild=ns.rebuild)
    return search(root, ns.q, k=ns.k, min_score=ns.min_score)


def _self_test() -> dict:
    """Model-free: prove sqlite-vec loads and does a KNN round trip.

    On a Python without loadable-extension support the tool genuinely cannot
    run here — report that honestly as 'unsupported' (a clean, expected
    degradation) rather than crashing or claiming a pass."""
    if not loadable_extensions_available():
        return {"self_test": "unsupported", "reason": NO_EXT_MSG}
    import sqlite_vec
    conn = sqlite3.connect(":memory:")
    conn.enable_load_extension(True)
    try:
        sqlite_vec.load(conn)
    except Exception as e:
        raise ToolError("NO_VEC", f"sqlite-vec did not load: {e}", exit_code=3) from e
    conn.execute("create virtual table t using vec0(embedding float[3])")
    conn.execute("insert into t(rowid, embedding) values (1, ?)",
                 [sqlite_vec.serialize_float32([1.0, 0.0, 0.0])])
    row = conn.execute("select rowid from t where embedding match ? "
                       "order by distance limit 1",
                       [sqlite_vec.serialize_float32([1.0, 0.0, 0.0])]).fetchone()
    conn.close()
    if row[0] != 1:
        raise ToolError("SELF_TEST", "sqlite-vec KNN round trip failed")
    return {"self_test": "pass"}


def main(args: list[str]) -> None:
    run_tool(TOOL, VERSION, handler, args)
