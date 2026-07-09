import subprocess
from pathlib import Path

import pytest

from groundwork.tools.patchgate.diffcheck import check_diff


def _git(root: Path, *args) -> str:
    p = subprocess.run(["git", *args], cwd=root, check=True,
                       capture_output=True, text=True, encoding="utf-8")
    return p.stdout


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


def _diff_for(repo: Path, path: str, new_content: str) -> str:
    (repo / path).write_text(new_content, encoding="utf-8", newline="\n")
    diff = _git(repo, "diff")
    _git(repo, "checkout", "--", path)      # restore pristine tree
    return diff


def test_good_diff_passes(repo):
    diff = _diff_for(repo, "a.py", "def f():\n    return 2\n")
    out = check_diff(repo, diff)
    assert out["passed"] is True and out["applies"] is True
    assert out["files"] == ["a.py"]
    assert "_exit_override" not in out


def test_syntax_breaking_diff_fails_parse(repo):
    diff = _diff_for(repo, "a.py", "def f(:\n    return 2\n")
    out = check_diff(repo, diff)
    assert out["applies"] is True and out["passed"] is False
    assert out["_exit_override"] == 1
    assert any(f["check"] == "compile" and not f["ok"] for f in out["findings"])


def test_non_applying_diff_fails_apply(repo):
    diff = _diff_for(repo, "a.py", "def f():\n    return 2\n")
    (repo / "a.py").write_text("def totally():\n    return 9\n",
                               encoding="utf-8", newline="\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "diverge")
    out = check_diff(repo, diff)
    assert out["applies"] is False and out["passed"] is False
    assert out["findings"][0]["check"] == "apply"


def test_new_file_diff_is_checked(repo):
    (repo / "new.py").write_text("def g(:\n    pass\n",
                                 encoding="utf-8", newline="\n")
    _git(repo, "add", "new.py")
    diff = _git(repo, "diff", "--cached")
    _git(repo, "rm", "-q", "--cached", "new.py")
    (repo / "new.py").unlink()
    out = check_diff(repo, diff)
    assert out["applies"] is True and out["passed"] is False
    assert any(f["check"] == "compile" for f in out["findings"])


def test_garbage_diff_is_apply_finding_not_crash(repo):
    out = check_diff(repo, "this is not a diff at all\n")
    assert out["passed"] is False and out["applies"] is False


def test_empty_diff_passes_trivially(repo):
    out = check_diff(repo, "")
    assert out["passed"] is True and out["files"] == []
