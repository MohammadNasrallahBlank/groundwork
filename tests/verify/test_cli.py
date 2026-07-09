import json
import subprocess
from pathlib import Path

from conftest_data import JUNIT

FIXTURE = str(Path("tests/fixtures/pyfail").resolve())


def run_cli(*args):
    return subprocess.run(["uv", "run", "groundwork", "verify", *args],
                          capture_output=True, text=True)


def test_run_on_pyfail_exits_1_with_normalized_diagnostics():
    p = run_cli("run", "--root", FIXTURE)
    assert p.returncode == 1, p.stdout
    out = json.loads(p.stdout)
    assert out["ok"] is True                      # envelope ok: tool ran fine
    assert out["data"]["summary"]["ok"] is False  # verification verdict: failures exist
    sources = {d["source"] for d in out["data"]["diagnostics"]}
    assert {"pytest", "ruff"} <= sources
    assert out["data"]["summary"]["counts"]["error"] == 1


def test_junit_only_mode(tmp_path):
    f = tmp_path / "r.xml"
    f.write_text(JUNIT)
    p = run_cli("run", "--root", str(tmp_path), "--junit", str(f))
    assert p.returncode == 1
    out = json.loads(p.stdout)
    assert out["data"]["summary"]["counts"]["error"] == 1


def test_junit_missing_file_surfaces_named_error(tmp_path):
    p = run_cli("run", "--root", str(tmp_path), "--junit", str(tmp_path / "nope.xml"))
    assert p.returncode == 1, p.stdout
    out = json.loads(p.stdout)
    assert out["error"]["code"] == "JUNIT_UNREADABLE"


def test_no_adapters_detected_exits_3(tmp_path):
    p = run_cli("run", "--root", str(tmp_path))
    assert p.returncode == 3
    out = json.loads(p.stdout)
    assert out["error"]["code"] == "NO_ADAPTERS"
    # Binding convention: all file paths in JSON output must be posix-style,
    # even on Windows, so the message is stable across platforms.
    assert "\\" not in out["error"]["message"]


def test_self_test():
    p = run_cli("self-test")
    assert p.returncode == 0
