import json
import os
import subprocess
from pathlib import Path


def run_cli(*args, cwd):
    return subprocess.run(["uv", "run", "groundwork", "mutcheck", *args],
                          capture_output=True, text=True, env={**os.environ},
                          cwd=cwd)


def _git(root, *a):
    subprocess.run(["git", *a], cwd=root, check=True, capture_output=True)


def _repo(tmp_path: Path, *, strong: bool) -> Path:
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "t@t")
    _git(tmp_path, "config", "user.name", "t")
    (tmp_path / "mod.py").write_text("def classify(x):\n    return 'low'\n",
                                     encoding="utf-8", newline="\n")
    boundary = ("    assert classify(10) == 'high'\n" if strong
                else "    assert classify(50) == 'high'\n")
    (tmp_path / "test_mod.py").write_text(
        "from mod import classify\ndef test_c():\n"
        "    assert classify(5) == 'low'\n" + boundary,
        encoding="utf-8", newline="\n")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-qm", "init")
    (tmp_path / "mod.py").write_text(
        "def classify(x):\n    if x < 10:\n        return 'low'\n"
        "    return 'high'\n", encoding="utf-8", newline="\n")
    return tmp_path


def test_survivor_reported_when_tests_are_weak(tmp_path):
    repo = _repo(tmp_path, strong=False)
    p = run_cli("check", cwd=str(repo))
    assert p.returncode == 0, p.stdout
    data = json.loads(p.stdout)["data"]
    assert data["summary"]["survived"] >= 1
    survs = [s for f in data["files"] for s in f["survivors"]]
    assert any(s["mutation"].startswith("Lt") for s in survs)


def test_strong_tests_kill_the_boundary_mutant(tmp_path):
    repo = _repo(tmp_path, strong=True)
    p = run_cli("check", cwd=str(repo))
    assert p.returncode == 0, p.stdout
    data = json.loads(p.stdout)["data"]
    assert data["summary"]["killed"] >= 1


def test_min_kill_gate_fails_below_floor(tmp_path):
    repo = _repo(tmp_path, strong=False)
    p = run_cli("check", "--min-kill", "1.0", cwd=str(repo))
    assert p.returncode == 1
    assert json.loads(p.stdout)["data"]["passed"] is False


def test_red_baseline_escalates(tmp_path):
    repo = _repo(tmp_path, strong=False)
    (repo / "test_mod.py").write_text(
        "def test_broken():\n    assert False\n", encoding="utf-8", newline="\n")
    p = run_cli("check", cwd=str(repo))
    assert p.returncode == 4
    assert json.loads(p.stdout)["error"]["code"] == "BASELINE_RED"


def test_self_test(tmp_path):
    p = run_cli("self-test", cwd=str(tmp_path))
    assert p.returncode == 0, p.stdout
    assert json.loads(p.stdout)["data"]["self_test"] == "pass"
