"""`gates hook` - the security PreToolUse battery. Strongest action wins.
Exit 0 always; internal failures follow fail_mode (open: silent allow,
closed: ask with the error)."""
import argparse
import json
import sys
from pathlib import Path


def _emit(decision: str, reason: str) -> None:
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": decision,
        "permissionDecisionReason": reason}}))


def _decide(payload: dict) -> tuple[str, str] | None:
    from groundwork.tools.gates.commandguard import check_command
    from groundwork.tools.gates.config import load_config
    from groundwork.tools.gates.pathguard import check_path
    from groundwork.tools.gates.patterns import scan_text

    tool = str(payload.get("tool_name") or "")
    tool_input = payload.get("tool_input") or {}
    cfg = load_config(Path(str(payload.get("cwd") or ".")))
    findings: list[tuple[str, str]] = []  # (action, reason)

    if tool in ("Bash", "PowerShell") and cfg["commands"]["enabled"]:
        command = tool_input.get("command")
        if isinstance(command, str):
            for f in check_command(
                    command,
                    extra_deny=tuple(cfg["commands"]["extra_deny"]),
                    extra_ask=tuple(cfg["commands"]["extra_ask"])):
                findings.append((f["action"],
                                 f"gates: command matched rule '{f['rule']}'"))
    elif tool in ("Edit", "Write"):
        file_path = tool_input.get("file_path")
        if isinstance(file_path, str) and file_path:
            hit = check_path(file_path,
                             deny=tuple(cfg["paths"]["deny"]),
                             ask=tuple(cfg["paths"]["ask"]))
            if hit:
                findings.append((hit["action"],
                                 f"gates: protected path (glob '{hit['glob']}')"))
            if cfg["secrets"]["enabled"]:
                content = tool_input.get("content" if tool == "Write"
                                         else "new_string")
                if isinstance(content, str):
                    for f in scan_text(content, path=file_path,
                                       allow_files=tuple(
                                           cfg["secrets"]["allow_files"])):
                        findings.append((
                            f["action"],
                            f"gates: secret pattern '{f['rule']}' "
                            f"({f['match']}) at line {f['line']}"))
    if not findings:
        return None
    if any(a == "deny" for a, _ in findings):
        reasons = "; ".join(r for a, r in findings if a == "deny")
        return ("deny", reasons)
    return ("ask", "; ".join(r for _, r in findings))


def run_hook(argv: list[str]) -> None:
    """Read PreToolUse JSON; emit the strongest gate decision, or allow silently."""
    p = argparse.ArgumentParser(prog="groundwork gates hook")
    p.add_argument("--event", required=True, choices=["pre-tool-use"])
    p.parse_known_args(argv)
    fail_mode = "open"
    try:
        raw = sys.stdin.buffer.read().decode("utf-8-sig", errors="replace")
        payload = json.loads(raw or "{}")
        try:
            from groundwork.tools.gates.config import load_config
            fail_mode = load_config(
                Path(str(payload.get("cwd") or "."))).get("fail_mode", "open")
        except Exception:  # noqa: BLE001
            pass
        decision = _decide(payload)
        if decision is not None:
            _emit(*decision)
    except Exception as e:  # noqa: BLE001 - policy decided by fail_mode
        if fail_mode == "closed":
            _emit("ask", f"gates: internal error, escalating (fail_mode=closed): "
                         f"{type(e).__name__}")
    raise SystemExit(0)
