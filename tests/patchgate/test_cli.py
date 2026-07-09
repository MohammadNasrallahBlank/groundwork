import json
import os
import subprocess
from pathlib import Path

import pytest


def run_cli(*args, cwd, stdin=None):
    return subprocess.run(["uv", "run", "groundwork", "patchgate", *args],
                          capture_output=True, text=True, env={**os.environ},
                          input=stdin, cwd=cwd)


def _git(root: Path, *args) -> str:
    return subprocess.run(["git", *args], cwd=root, check=True,
                          capture_output=True, text=True,
                          encoding="utf-8").stdout


@pytest.fixture()
def repo(tmp_path):
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "t@t")
    _git(tmp_path, "config", "user.name", "t")
    (tmp_path / "a.py").write_text("def f():\n    return 1\n",
                                   encoding="utf-8", newline="\n")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-qm", "init")
    return tmp_path


def test_check_diff_pass_and_fail_exit_codes(repo):
    (repo / "a.py").write_text("def f():\n    return 2\n",
                               encoding="utf-8", newline="\n")
    good = _git(repo, "diff")
    _git(repo, "checkout", "--", "a.py")
    p = run_cli("check-diff", cwd=str(repo), stdin=good)
    assert p.returncode == 0, p.stdout
    assert json.loads(p.stdout)["data"]["passed"] is True

    (repo / "a.py").write_text("def f(:\n    return 2\n",
                               encoding="utf-8", newline="\n")
    bad = _git(repo, "diff")
    _git(repo, "checkout", "--", "a.py")
    p2 = run_cli("check-diff", cwd=str(repo), stdin=bad)
    assert p2.returncode == 1
    out = json.loads(p2.stdout)
    assert out["ok"] is True and out["data"]["passed"] is False


def test_check_diff_from_file(repo, tmp_path):
    (repo / "a.py").write_text("def f():\n    return 3\n",
                               encoding="utf-8", newline="\n")
    diff_file = tmp_path / "change.patch"
    diff_file.write_text(_git(repo, "diff"), encoding="utf-8", newline="\n")
    _git(repo, "checkout", "--", "a.py")
    p = run_cli("check-diff", "--diff", str(diff_file), cwd=str(repo))
    assert p.returncode == 0, p.stdout


def test_check_content_verdicts(repo):
    p = run_cli("check-content", "--file", "x.py", cwd=str(repo),
                stdin="def ok():\n    pass\n")
    assert p.returncode == 0
    p2 = run_cli("check-content", "--file", "x.py", cwd=str(repo),
                 stdin="def broken(:\n")
    assert p2.returncode == 1
    assert json.loads(p2.stdout)["data"]["ok"] is False


def test_self_test(repo):
    p = run_cli("self-test", cwd=str(repo))
    assert p.returncode == 0, p.stdout
    assert json.loads(p.stdout)["data"]["self_test"] == "pass"
