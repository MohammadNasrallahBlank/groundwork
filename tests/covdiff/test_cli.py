import json
import os
import subprocess
from pathlib import Path


def run_cli(*args, cwd):
    return subprocess.run(["uv", "run", "groundwork", "covdiff", *args],
                          capture_output=True, text=True, env={**os.environ},
                          cwd=cwd)


def _git(root, *a):
    subprocess.run(["git", *a], cwd=root, check=True, capture_output=True)


def _repo_with_partial_coverage(tmp_path: Path) -> Path:
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "t@t")
    _git(tmp_path, "config", "user.name", "t")
    (tmp_path / "mod.py").write_text("def a():\n    return 1\n",
                                     encoding="utf-8", newline="\n")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-qm", "init")
    (tmp_path / "mod.py").write_text(
        "def a():\n    return 2\n\ndef b():\n    return 99\n",
        encoding="utf-8", newline="\n")
    cov = {"files": {(tmp_path / "mod.py").as_posix(): {
        "executed_lines": [1, 2, 4], "missing_lines": [5]}}}
    (tmp_path / "cov.json").write_text(json.dumps(cov), encoding="utf-8")
    return tmp_path


def test_check_ingests_coverage_and_reports(tmp_path):
    repo = _repo_with_partial_coverage(tmp_path)
    p = run_cli("check", "--coverage-json", "cov.json", cwd=str(repo))
    assert p.returncode == 0, p.stdout
    data = json.loads(p.stdout)["data"]
    f = [x for x in data["files"] if x["file"] == "mod.py"][0]
    assert 5 in f["uncovered"] and 2 in f["covered"]


def test_min_gate_fails_below_floor(tmp_path):
    repo = _repo_with_partial_coverage(tmp_path)
    p = run_cli("check", "--coverage-json", "cov.json", "--min", "0.9",
                cwd=str(repo))
    assert p.returncode == 1
    out = json.loads(p.stdout)
    assert out["ok"] is True and out["data"]["passed"] is False


def test_min_gate_passes_above_floor(tmp_path):
    repo = _repo_with_partial_coverage(tmp_path)
    p = run_cli("check", "--coverage-json", "cov.json", "--min", "0.5",
                cwd=str(repo))
    assert p.returncode == 0
    assert json.loads(p.stdout)["data"]["passed"] is True


def test_bad_coverage_json_exits_2(tmp_path):
    repo = _repo_with_partial_coverage(tmp_path)
    p = run_cli("check", "--coverage-json", "nope.json", cwd=str(repo))
    assert p.returncode == 2
    assert json.loads(p.stdout)["error"]["code"] == "BAD_COVERAGE"


def test_self_test(tmp_path):
    p = run_cli("self-test", cwd=str(tmp_path))
    assert p.returncode == 0, p.stdout
    assert json.loads(p.stdout)["data"]["self_test"] == "pass"
