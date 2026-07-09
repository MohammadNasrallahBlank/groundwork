import argparse
from pathlib import Path

from groundwork.core.cliparse import UsageParser
from groundwork.core.runner import ToolError, run_tool
from groundwork.tools.propcheck.generate import generate_property
from groundwork.tools.propcheck.run import run_property_file

TOOL, VERSION = "propcheck", "0.1.0"


def handler(args: list[str]) -> dict:
    p = UsageParser(prog=f"groundwork {TOOL}", exit_on_error=False)
    sub = p.add_subparsers(dest="cmd", required=True)
    n = sub.add_parser("new")
    n.add_argument("--invariant", required=True)
    n.add_argument("--module", required=True)
    n.add_argument("--func", required=True)
    n.add_argument("--strategy", required=True)
    n.add_argument("--inverse")
    n.add_argument("--reference")
    n.add_argument("--name")
    n.add_argument("--out", required=True)
    n.add_argument("--force", action="store_true")
    r = sub.add_parser("run")
    r.add_argument("--file", required=True)
    sub.add_parser("self-test")
    try:
        ns = p.parse_args(args)
    except argparse.ArgumentError as e:
        raise ToolError("USAGE", str(e), exit_code=2) from e

    if ns.cmd == "self-test":
        return _self_test()
    if ns.cmd == "run":
        out = run_property_file(Path(ns.file))
        if not out["passed"]:
            out["_exit_override"] = 1
        return out
    # new
    src = generate_property(invariant=ns.invariant, module=ns.module,
                            func=ns.func, strategy=ns.strategy,
                            inverse=ns.inverse, reference=ns.reference,
                            name=ns.name)
    out_path = Path(ns.out)
    if out_path.exists() and not ns.force:
        raise ToolError("EXISTS", f"{out_path.as_posix()} exists; use --force",
                        exit_code=2)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(src, encoding="utf-8", newline="\n")
    return {"out": out_path.as_posix(), "invariant": ns.invariant,
            "lines": src.count("\n")}


def _self_test() -> dict:
    """Generate a roundtrip property source and confirm it compiles."""
    src = generate_property(invariant="roundtrip", module="json", func="dumps",
                            inverse="json.loads", strategy="int")
    compile(src, "<selftest>", "exec")
    if "loads(dumps(x)) == x" not in src:
        raise ToolError("SELF_TEST", "generated source unexpected", detail=src)
    return {"self_test": "pass"}


def main(args: list[str]) -> None:
    run_tool(TOOL, VERSION, handler, args)
