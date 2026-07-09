import json
import os
import subprocess
from pathlib import Path

FIX = str(Path("tests/fixtures/cartomap").resolve())


def test_hook_emits_context_json_not_envelope(tmp_path):
    stdin = json.dumps({"hook_event_name": "SessionStart", "source": "startup",
                        "cwd": FIX})
    env = {**os.environ, "GROUNDWORK_CACHE_DIR": str(tmp_path / "c")}
    p = subprocess.run(["uv", "run", "groundwork", "cartographer", "hook",
                        "--event", "session-start", "--budget", "1500"],
                       input=stdin, capture_output=True, text=True, env=env)
    assert p.returncode == 0, p.stderr
    out = json.loads(p.stdout)
    # hook protocol, NOT the groundwork envelope
    assert "hookSpecificOutput" in out and "ok" not in out
    hs = out["hookSpecificOutput"]
    assert hs["hookEventName"] == "SessionStart"
    assert "helper" in hs["additionalContext"]


def test_hook_tolerates_bom_and_utf8_stdin(tmp_path):
    # Windows PowerShell 5.1 pipes prepend a UTF-8 BOM; the event JSON is
    # UTF-8 regardless of the console locale. Both must still yield a map.
    stdin = chr(0xFEFF) + json.dumps({"hook_event_name": "SessionStart",
                                      "source": "startup", "cwd": FIX})
    env = {**os.environ, "GROUNDWORK_CACHE_DIR": str(tmp_path / "c")}
    p = subprocess.run(["uv", "run", "groundwork", "cartographer", "hook",
                        "--event", "session-start"],
                       input=stdin.encode("utf-8"), capture_output=True, env=env)
    assert p.returncode == 0, p.stderr
    out = json.loads(p.stdout.decode("utf-8"))
    assert "helper" in out["hookSpecificOutput"]["additionalContext"]


def test_hook_bad_stdin_still_exits_zero_without_context(tmp_path):
    env = {**os.environ, "GROUNDWORK_CACHE_DIR": str(tmp_path / "c")}
    p = subprocess.run(["uv", "run", "groundwork", "cartographer", "hook",
                        "--event", "session-start"],
                       input="not json", capture_output=True, text=True, env=env)
    # A hook must never break the session: malformed stdin -> exit 0, empty context.
    assert p.returncode == 0
    out = json.loads(p.stdout)
    assert out["hookSpecificOutput"]["additionalContext"] == ""
