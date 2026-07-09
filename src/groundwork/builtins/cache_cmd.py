import argparse
from groundwork.core.cache import Cache
from groundwork.core.runner import ToolError, run_tool


def handler(args: list[str]) -> dict:
    p = argparse.ArgumentParser(prog="groundwork cache", exit_on_error=False)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("stats")
    sub.add_parser("clear")
    try:
        ns = p.parse_args(args)
    except (argparse.ArgumentError, SystemExit) as e:
        raise ToolError("USAGE", str(e), exit_code=2) from e
    c = Cache()
    if ns.cmd == "clear":
        c.clear()
        return {"cleared": True, "root": c.root.as_posix()}
    return {**c.stats(), "root": c.root.as_posix()}


def main(args: list[str]) -> None:
    run_tool("cache", "0.1.0", handler, args)
