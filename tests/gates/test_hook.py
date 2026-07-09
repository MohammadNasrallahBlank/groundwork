import json
import os
import subprocess


def _run_hook(payload):
    stdin = payload if isinstance(payload, str) else json.dumps(payload)
    return subprocess.run(
        ["uv", "run", "groundwork", "gates", "hook", "--event", "pre-tool-use"],
        input=stdin.encode("utf-8"), capture_output=True,
        env={**os.environ}, timeout=120)


def _payload(tool, tool_input, cwd):
    return {"hook_event_name": "PreToolUse", "tool_name": tool,
            "tool_input": tool_input, "cwd": str(cwd)}


def _decision(proc):
    return json.loads(proc.stdout)["hookSpecificOutput"]


def test_dangerous_bash_command_is_denied(tmp_path):
    p = _run_hook(_payload("Bash", {"command": "rm -rf /"}, tmp_path))
    assert p.returncode == 0
    d = _decision(p)
    assert d["permissionDecision"] == "deny"
    assert "bash-rm-root" in d["permissionDecisionReason"]


def test_dangerous_powershell_command_is_denied(tmp_path):
    p = _run_hook(_payload("PowerShell",
                           {"command": "Remove-Item -Recurse -Force C:\\"},
                           tmp_path))
    assert _decision(p)["permissionDecision"] == "deny"


def test_force_push_is_ask(tmp_path):
    p = _run_hook(_payload("Bash", {"command": "git push --force origin main"},
                           tmp_path))
    assert _decision(p)["permissionDecision"] == "ask"


def test_ordinary_command_is_allowed(tmp_path):
    p = _run_hook(_payload("Bash", {"command": "git status"}, tmp_path))
    assert p.returncode == 0 and p.stdout.strip() == b""


def test_write_with_secret_is_denied(tmp_path):
    p = _run_hook(_payload("Write", {"file_path": str(tmp_path / "cfg.py"),
                                     "content": "KEY='AKIAIOSFODNN7EXAMPLE'\n"},
                           tmp_path))
    d = _decision(p)
    assert d["permissionDecision"] == "deny"
    assert "aws-access-key-id" in d["permissionDecisionReason"]
    assert "AKIAIOSFODNN7EXAMPLE" not in d["permissionDecisionReason"]  # redacted


def test_env_write_is_ask_by_default(tmp_path):
    p = _run_hook(_payload("Write", {"file_path": str(tmp_path / ".env"),
                                     "content": "PORT=3000\n"}, tmp_path))
    assert _decision(p)["permissionDecision"] == "ask"


def test_config_deny_glob_applies(tmp_path):
    d = tmp_path / ".groundwork"
    d.mkdir()
    (d / "gates.yaml").write_text("paths:\n  deny: ['**/prod.yaml']\n",
                                  encoding="utf-8")
    p = _run_hook(_payload("Write", {"file_path": str(tmp_path / "cfg" / "prod.yaml"),
                                     "content": "x: 1\n"}, tmp_path))
    assert _decision(p)["permissionDecision"] == "deny"


def test_clean_write_is_allowed(tmp_path):
    p = _run_hook(_payload("Write", {"file_path": str(tmp_path / "a.py"),
                                     "content": "def f():\n    return 1\n"},
                           tmp_path))
    assert p.stdout.strip() == b""


def test_garbage_stdin_fail_open_default(tmp_path):
    p = _run_hook("not json")
    assert p.returncode == 0 and p.stdout.strip() == b""
