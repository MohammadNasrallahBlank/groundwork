import argparse
from pathlib import Path

import groundwork
from groundwork.core.manifest import ManifestError, discover
from groundwork.core.runner import ToolError, run_tool


def handler(args: list[str]) -> dict:
    p = argparse.ArgumentParser(prog="groundwork manifest", exit_on_error=False)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("lint")
    try:
        p.parse_args(args)
    except (argparse.ArgumentError, SystemExit) as e:
        raise ToolError("USAGE", str(e), exit_code=2) from e
    tools_dir = Path(groundwork.__file__).parent / "tools"
    try:
        manifests = discover(tools_dir)
    except ManifestError as e:
        raise ToolError("MANIFEST_INVALID", str(e)) from e
    return {"tools": [m["name"] for m in manifests], "count": len(manifests)}


def main(args: list[str]) -> None:
    run_tool("manifest", "0.1.0", handler, args)
