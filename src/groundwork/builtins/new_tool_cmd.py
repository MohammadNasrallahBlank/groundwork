import argparse
import json
from pathlib import Path

import groundwork
from groundwork.core.runner import ToolError, run_tool

CLI_TEMPLATE = '''import argparse
from groundwork.core.runner import ToolError, run_tool

TOOL, VERSION = "{name}", "0.1.0"


def handler(args: list[str]) -> dict:
    p = argparse.ArgumentParser(prog=f"groundwork {name_brace}", exit_on_error=False)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("self-test")
    try:
        ns = p.parse_args(args)
    except (argparse.ArgumentError, SystemExit) as e:
        raise ToolError("USAGE", str(e), exit_code=2) from e
    if ns.cmd == "self-test":
        return {{"self_test": "pass"}}
    raise ToolError("USAGE", "unknown command", exit_code=2)


def main(args: list[str]) -> None:
    run_tool(TOOL, VERSION, handler, args)
'''


def handler(args: list[str]) -> dict:
    p = argparse.ArgumentParser(prog="groundwork new-tool", exit_on_error=False)
    p.add_argument("name")
    p.add_argument("--purpose", required=True)
    try:
        ns = p.parse_args(args)
    except (argparse.ArgumentError, SystemExit) as e:
        raise ToolError("USAGE", str(e), exit_code=2) from e
    if not ns.name.isidentifier():
        raise ToolError("BAD_NAME", "tool name must be a valid python identifier", exit_code=2)
    tool_dir = Path(groundwork.__file__).parent / "tools" / ns.name
    if tool_dir.exists():
        raise ToolError("EXISTS", f"tool already exists: {ns.name}")
    tool_dir.mkdir(parents=True)
    (tool_dir / "__init__.py").write_text("", encoding="utf-8", newline="\n")
    (tool_dir / "cli.py").write_text(
        CLI_TEMPLATE.format(name=ns.name, name_brace="{TOOL}"),
        encoding="utf-8", newline="\n")
    manifest = {
        "name": ns.name, "version": "0.1.0", "purpose": ns.purpose,
        "reach_for_me_when": [f"TODO-replace: describe when to reach for {ns.name}"],
        "commands": [{"name": "self-test", "summary": "Prove the tool works", "args": ""}],
        "danger_level": "read_only", "cache": "off",
        "deps": {"python": [], "system": [], "optional": []},
    }
    (tool_dir / "manifest.json").write_text(json.dumps(manifest, indent=2),
                                            encoding="utf-8", newline="\n")
    return {"created": tool_dir.as_posix(), "next": "edit manifest.json, add commands, add tests"}


def main(args: list[str]) -> None:
    run_tool("new-tool", "0.1.0", handler, args)
