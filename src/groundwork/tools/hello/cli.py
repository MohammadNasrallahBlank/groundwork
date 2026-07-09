import argparse
from groundwork.core.runner import ToolError, run_tool

TOOL, VERSION = "hello", "0.1.0"


def handler(args: list[str]) -> dict:
    p = argparse.ArgumentParser(prog=f"groundwork {TOOL}", exit_on_error=False)
    sub = p.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("greet")
    g.add_argument("--name", required=True)
    sub.add_parser("self-test")
    try:
        ns = p.parse_args(args)
    except (argparse.ArgumentError, SystemExit) as e:
        raise ToolError("USAGE", str(e), exit_code=2) from e
    if ns.cmd == "self-test":
        return {"self_test": "pass"}
    return {"greeting": f"Hello, {ns.name}"}


def main(args: list[str]) -> None:
    run_tool(TOOL, VERSION, handler, args)
