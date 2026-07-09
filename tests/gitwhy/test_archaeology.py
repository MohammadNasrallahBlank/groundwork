import subprocess

import pytest

from groundwork.core.runner import ToolError
from groundwork.tools.gitwhy.archaeology import explain


def _git(root, *a, **kw):
    return subprocess.run(["git", *a], cwd=root, capture_output=True, text=True,
                          encoding="utf-8", **kw)


@pytest.fixture()
def repo(tmp_path):
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


def test_explain_returns_commits_with_refs(repo):
    out = explain(repo, "mod.py", 2, 2)
    assert out["file"] == "mod.py" and out["region"] == [2, 2]
    assert out["commits"][0]["summary"].startswith("fix: correct return")
    assert out["commits"][0]["author"] == "Alice"
    assert out["commits"][0]["date"].startswith("20")            # ISO date
    refs = {(r["number"], r["closing"]) for r in out["refs"]}
    assert (7, True) in refs


def test_explain_condenses_and_rolls_up(repo):
    out = explain(repo, "mod.py", 1, 2)
    assert "Alice" in out["authors"]
    assert out["span"]["oldest"] <= out["span"]["newest"]


def test_explain_untracked_file_escalates(repo):
    with pytest.raises(ToolError) as ei:
        explain(repo, "nope.py", 1, 1)
    assert ei.value.code == "NO_BLAME" and ei.value.exit_code == 2


def test_explain_outside_repo(tmp_path, monkeypatch):
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path.parent))
    with pytest.raises(ToolError) as ei:
        explain(tmp_path, "x.py", 1, 1)
    assert ei.value.code in ("NO_GIT", "NO_BLAME")
