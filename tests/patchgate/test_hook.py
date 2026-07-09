import json
import os
import subprocess
import time


def _run_hook(payload, extra_env=None):
    env = {**os.environ, **(extra_env or {})}
    stdin = payload if isinstance(payload, str) else json.dumps(payload)
    return subprocess.run(
        ["uv", "run", "groundwork", "patchgate", "hook", "--event", "pre-tool-use"],
        input=stdin.encode("utf-8"), capture_output=True, env=env, timeout=120)


def _payload(tool, tool_input, cwd):
    return {"hook_event_name": "PreToolUse", "tool_name": tool,
            "tool_input": tool_input, "cwd": str(cwd)}


def test_write_with_broken_python_is_denied(tmp_path):
    p = _run_hook(_payload("Write", {"file_path": str(tmp_path / "x.py"),
                                     "content": "def f(:\n    pass\n"}, tmp_path))
    assert p.returncode == 0
    out = json.loads(p.stdout)
    hs = out["hookSpecificOutput"]
    assert hs["hookEventName"] == "PreToolUse"
    assert hs["permissionDecision"] == "deny"
    assert "line 1" in hs["permissionDecisionReason"]


def test_write_with_valid_python_is_allowed_silently(tmp_path):
    p = _run_hook(_payload("Write", {"file_path": str(tmp_path / "x.py"),
                                     "content": "def f():\n    pass\n"}, tmp_path))
    assert p.returncode == 0 and p.stdout.strip() == b""


def test_edit_producing_broken_python_is_denied(tmp_path):
    target = tmp_path / "y.py"
    target.write_text("def f():\n    return 1\n", encoding="utf-8", newline="\n")
    p = _run_hook(_payload("Edit", {"file_path": str(target),
                                    "old_string": "return 1",
                                    "new_string": "return ((1"}, tmp_path))
    out = json.loads(p.stdout)
    assert out["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_edit_old_string_missing_is_allowed(tmp_path):
    target = tmp_path / "y.py"
    target.write_text("def f():\n    return 1\n", encoding="utf-8", newline="\n")
    p = _run_hook(_payload("Edit", {"file_path": str(target),
                                    "old_string": "NOT PRESENT",
                                    "new_string": "x"}, tmp_path))
    assert p.returncode == 0 and p.stdout.strip() == b""   # the tool errors itself


def test_unknown_tool_and_unknown_filetype_are_allowed(tmp_path):
    assert _run_hook(_payload("Bash", {"command": "rm -rf /"}, tmp_path)
                     ).stdout.strip() == b""
    assert _run_hook(_payload("Write", {"file_path": str(tmp_path / "n.txt"),
                                        "content": "anything"}, tmp_path)
                     ).stdout.strip() == b""


def test_garbage_stdin_is_allowed_and_exit_zero(tmp_path):
    p = _run_hook("not json at all")
    assert p.returncode == 0 and p.stdout.strip() == b""


def test_hook_latency_measured(tmp_path):
    payload = _payload("Write", {"file_path": str(tmp_path / "x.py"),
                                 "content": "def f():\n    pass\n"}, tmp_path)
    start = time.perf_counter()
    _run_hook(payload)
    elapsed_ms = (time.perf_counter() - start) * 1000
    # informational: printed so the run log carries the real number for the
    # README/index correction. The assertion only catches pathology.
    print(f"\npatchgate hook end-to-end latency: {elapsed_ms:.0f} ms")
    assert elapsed_ms < 5000
