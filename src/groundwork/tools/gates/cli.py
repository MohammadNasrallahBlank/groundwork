import argparse
import sys
from pathlib import Path

from groundwork.core.cliparse import UsageParser
from groundwork.core.runner import ToolError, run_tool
from groundwork.tools.gates.commandguard import check_command
from groundwork.tools.gates.config import load_config
from groundwork.tools.gates.patterns import scan_text

TOOL, VERSION = "gates", "0.1.0"


def handler(args: list[str]) -> dict:
    p = UsageParser(prog=f"groundwork {TOOL}", exit_on_error=False)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("scan")
    s.add_argument("--file")
    s.add_argument("--path", default="")
    s.add_argument("--root", default=".")
    c = sub.add_parser("check-command")
    c.add_argument("--command", required=True)
    c.add_argument("--root", default=".")
    sc = sub.add_parser("show-config")
    sc.add_argument("--root", default=".")
    sub.add_parser("self-test")
    try:
        ns = p.parse_args(args)
    except argparse.ArgumentError as e:
        raise ToolError("USAGE", str(e), exit_code=2) from e

    if ns.cmd == "self-test":
        return _self_test()
    root = Path(ns.root).resolve()
    if not root.is_dir():
        raise ToolError("NO_ROOT", f"not a directory: {root.as_posix()}", exit_code=2)
    cfg = load_config(root)
    if ns.cmd == "show-config":
        return cfg
    if ns.cmd == "check-command":
        findings = check_command(ns.command,
                                 extra_deny=tuple(cfg["commands"]["extra_deny"]),
                                 extra_ask=tuple(cfg["commands"]["extra_ask"]))
        out = {"command_checked": True, "findings": findings}
        if findings:
            out["_exit_override"] = 1
        return out
    if ns.file:
        fp = Path(ns.file)
        if not fp.is_file():
            raise ToolError("USAGE", f"no such file: {fp.as_posix()}", exit_code=2)
        text = fp.read_text(encoding="utf-8", errors="replace")
        path_for_rules = ns.path or fp.name
    else:
        text = sys.stdin.read()
        path_for_rules = ns.path
    findings = scan_text(text, path=path_for_rules,
                         allow_files=tuple(cfg["secrets"]["allow_files"]))
    out = {"path": path_for_rules, "findings": findings}
    if findings:
        out["_exit_override"] = 1
    return out


def _self_test() -> dict:
    """Prove the gate verdicts are consistent - pure, no I/O."""
    hot = scan_text("k = 'AKIAIOSFODNN7EXAMPLE'\n")
    cold = scan_text("def f():\n    return 1\n")
    cmd = check_command("rm -rf /")
    if not hot or cold or not cmd:
        raise ToolError("SELF_TEST", "gate verdicts inconsistent",
                        detail={"hot": hot, "cold": cold, "cmd": cmd})
    return {"self_test": "pass"}


def main(args: list[str]) -> None:
    # `hook` speaks the PreToolUse permission protocol, not the envelope.
    if args and args[0] == "hook":
        from groundwork.tools.gates.hookcli import run_hook
        run_hook(args[1:])
        return
    run_tool(TOOL, VERSION, handler, args)
