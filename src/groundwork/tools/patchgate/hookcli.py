"""`patchgate hook` - PreToolUse gate. Deny = printed decision JSON; allow =
NO output. Exit 0 ALWAYS: this gate fails open, it never breaks a session."""
import argparse
import json
import sys
from pathlib import Path


def _post_image(tool_name: str, tool_input: dict, cwd: str) -> tuple[str, str] | None:
    """(file_path, resulting content) for Edit/Write, or None -> allow."""
    file_path = tool_input.get("file_path")
    if not isinstance(file_path, str) or not file_path:
        return None
    if tool_name == "Write":
        content = tool_input.get("content")
        return (file_path, content) if isinstance(content, str) else None
    if tool_name == "Edit":
        old = tool_input.get("old_string")
        new = tool_input.get("new_string")
        if not isinstance(old, str) or not isinstance(new, str) or not old:
            return None
        p = Path(file_path)
        if not p.is_absolute():
            p = Path(cwd or ".") / p
        if not p.is_file():
            return None
        try:
            with open(p, encoding="utf-8", newline="") as fh:
                current = fh.read()
        except (OSError, UnicodeDecodeError):
            return None
        count = current.count(old)
        if count == 0 or (count > 1 and not tool_input.get("replace_all")):
            return None  # the Edit tool will refuse on its own; not our call
        replaced = (current.replace(old, new) if tool_input.get("replace_all")
                    else current.replace(old, new, 1))
        return (file_path, replaced)
    return None


def run_hook(argv: list[str]) -> None:
    """Read the PreToolUse JSON on stdin; deny iff the post-image fails a check."""
    p = argparse.ArgumentParser(prog="groundwork patchgate hook")
    p.add_argument("--event", required=True, choices=["pre-tool-use"])
    p.parse_known_args(argv)
    try:
        raw = sys.stdin.buffer.read().decode("utf-8-sig", errors="replace")
        payload = json.loads(raw or "{}")
        pair = _post_image(str(payload.get("tool_name") or ""),
                           payload.get("tool_input") or {},
                           str(payload.get("cwd") or ""))
        if pair is not None:
            from groundwork.tools.patchgate.checks import check_content
            file_path, content = pair
            res = check_content(file_path, content)
            if res["checked"] and not res["ok"]:
                print(json.dumps({"hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason":
                        f"patchgate: this edit would break {res['file']} "
                        f"[{res['checker']}] {res['error']}"}}))
    except Exception:  # noqa: BLE001 - fail OPEN, never break the session
        pass
    raise SystemExit(0)
