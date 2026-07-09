import subprocess
from pathlib import Path

import pytest

from groundwork.core.runner import ToolError
from groundwork.tools.codemod.applier import apply_plan
from groundwork.tools.codemod.planner import build_plan


def _git(root: Path, *args):
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)


@pytest.fixture()
def repo(tmp_path):
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "t@t")
    _git(tmp_path, "config", "user.name", "t")
    (tmp_path / "a.py").write_text("def f():\n    print(1)\n",
                                   encoding="utf-8", newline="\n")
    (tmp_path / "crlf.py").write_text("def g():\r\n    print(2)\r\n",
                                      encoding="utf-8", newline="")
    (tmp_path / ".gitattributes").write_text("* -text\n", encoding="utf-8")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-qm", "init")
    return tmp_path


def _plan(repo):
    return build_plan(repo, engine="ast-grep", pattern="print($A)",
                      rewrite="log($A)", lang="python", preset=None, glob=None)


def test_apply_writes_files_byte_faithfully(repo):
    plan = _plan(repo)
    out = apply_plan(repo, plan["plan_id"], no_verify=True)
    assert sorted(out["files_written"]) == ["a.py", "crlf.py"]
    assert out["verify"] is None
    with open(repo / "a.py", encoding="utf-8", newline="") as fh:
        assert fh.read() == "def f():\n    log(1)\n"
    # CRLF file keeps CRLF line endings — only the edited span changed
    with open(repo / "crlf.py", encoding="utf-8", newline="") as fh:
        assert fh.read() == "def g():\r\n    log(2)\r\n"


def test_apply_refuses_dirty_tree(repo):
    plan = _plan(repo)
    (repo / "a.py").write_text("def f():\n    print(999)\n",
                               encoding="utf-8", newline="\n")
    with pytest.raises(ToolError) as ei:
        apply_plan(repo, plan["plan_id"], no_verify=True)
    assert ei.value.code == "DIRTY_TREE" and ei.value.exit_code == 1
    assert "a.py" in str(ei.value.detail)


def test_apply_refuses_stale_plan(repo):
    plan = _plan(repo)
    (repo / "a.py").write_text("def f():\n    print(42)\n",
                               encoding="utf-8", newline="\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "moved on")   # tree is clean again, but changed
    with pytest.raises(ToolError) as ei:
        apply_plan(repo, plan["plan_id"], no_verify=True)
    assert ei.value.code == "STALE_PLAN" and ei.value.exit_code == 1


def test_apply_outside_git_refuses(tmp_path, monkeypatch):
    # pytest's basetemp (.tmp) lives INSIDE the groundwork repo, so plain git
    # discovery would climb to the outer repo and defeat this test. A ceiling
    # directory stops discovery at tmp_path's parent — the applier's own
    # semantics (a parent repo genuinely provides the guarantee) are unchanged.
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path.parent))
    (tmp_path / "a.py").write_text("print(1)\n", encoding="utf-8", newline="\n")
    plan = build_plan(tmp_path, engine="ast-grep", pattern="print($A)",
                      rewrite="log($A)", lang="python", preset=None, glob=None)
    with pytest.raises(ToolError) as ei:
        apply_plan(tmp_path, plan["plan_id"], no_verify=True)
    assert ei.value.code == "NO_GIT" and ei.value.exit_code == 1


def test_apply_untracked_files_do_not_block(repo):
    plan = _plan(repo)
    (repo / "scratch.txt").write_text("untracked\n", encoding="utf-8")
    out = apply_plan(repo, plan["plan_id"], no_verify=True)
    assert out["files_written"]


def test_apply_empty_plan_is_noop_success(repo):
    plan = build_plan(repo, engine="ast-grep", pattern="frobnicate($A)",
                      rewrite="x($A)", lang="python", preset=None, glob=None)
    out = apply_plan(repo, plan["plan_id"], no_verify=False)
    assert out["files_written"] == [] and out["verify"] is None
