import json
import os
import subprocess
from pathlib import Path


def run_cli(*args, cwd):
    return subprocess.run(["uv", "run", "groundwork", "gitwhy", *args],
                          capture_output=True, text=True, env={**os.environ},
                          cwd=cwd)


def _git(root, *a):
    subprocess.run(["git", *a], cwd=root, check=True, capture_output=True)


def _repo(tmp_path: Path) -> Path:
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "a@x")
    _git(tmp_path, "config", "user.name", "Alice")
    (tmp_path / "mod.py").write_text("def a():\n    return 1\n",
                                     encoding="utf-8", newline="\n")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-qm", "feat: add a (#42)")
    (tmp_path / "mod.py").write_text("def a():\n    return 2\n",
                                     encoding="utf-8", newline="\n")
    _git(tmp_path, "commit", "-aqm", "fix: correct return\n\nFixes #7")
    return tmp_path


def test_explain_line(tmp_path):
    repo = _repo(tmp_path)
    p = run_cli("explain", "--file", "mod.py", "--lines", "2", cwd=str(repo))
    assert p.returncode == 0, p.stdout
    data = json.loads(p.stdout)["data"]
    assert data["region"] == [2, 2]
    assert any(r["number"] == 7 and r["closing"] for r in data["refs"])


def test_explain_range(tmp_path):
    repo = _repo(tmp_path)
    p = run_cli("explain", "--file", "mod.py", "--lines", "1-2", cwd=str(repo))
    assert p.returncode == 0, p.stdout
    assert json.loads(p.stdout)["data"]["region"] == [1, 2]


def test_explain_bad_lines_exits_2(tmp_path):
    repo = _repo(tmp_path)
    p = run_cli("explain", "--file", "mod.py", "--lines", "notarange",
                cwd=str(repo))
    assert p.returncode == 2
    assert json.loads(p.stdout)["error"]["code"] == "USAGE"


def test_churn_reports(tmp_path):
    repo = _repo(tmp_path)
    p = run_cli("churn", cwd=str(repo))
    assert p.returncode == 0, p.stdout
    files = json.loads(p.stdout)["data"]["files"]
    assert any(f["file"] == "mod.py" and f["changes"] == 2 for f in files)


def test_self_test(tmp_path):
    p = run_cli("self-test", cwd=str(tmp_path))
    assert p.returncode == 0, p.stdout
    assert json.loads(p.stdout)["data"]["self_test"] == "pass"
