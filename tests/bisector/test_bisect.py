import subprocess
from pathlib import Path

import pytest

from groundwork.core.runner import ToolError
from groundwork.tools.bisector.bisect import bisect_culprit, map_verdict


def test_map_verdict():
    assert map_verdict(0, {125}) == "good"
    assert map_verdict(125, {125}) == "skip"
    assert map_verdict(1, {125}) == "bad"
    assert map_verdict(3, {3, 125}) == "skip"
    assert map_verdict(2, {125}) == "bad"


def _git(root, *a):
    return subprocess.run(["git", *a], cwd=root, capture_output=True, text=True,
                          encoding="utf-8")


@pytest.fixture()
def repo_with_regression(tmp_path):
    r = tmp_path / "r"
    r.mkdir()
    _git(r, "init", "-q")
    _git(r, "config", "user.email", "t@t")
    _git(r, "config", "user.name", "t")
    shas = []
    # unique content per commit (a running counter) so every commit has a
    # distinct tree — this defeats git bisect's same-tree auto-classification
    # and forces the oracle to actually decide each step.
    for i in range(6):
        bug = "  # BUG" if i >= 3 else ""       # commit index 3 introduces the bug
        (r / "mod.py").write_text(f"step = {i}{bug}\n",
                                  encoding="utf-8", newline="\n")
        _git(r, "add", "-A")
        _git(r, "commit", "-qm", f"commit {i}")
        shas.append(_git(r, "rev-parse", "HEAD").stdout.strip())
    return r, shas


def _worktree(repo, ref, tmp_path):
    wt = tmp_path / "wt"
    _git(repo, "worktree", "add", "-q", str(wt), ref)
    return wt


def test_finds_the_culprit(repo_with_regression, tmp_path):
    repo, shas = repo_with_regression
    wt = _worktree(repo, shas[5], tmp_path)
    try:
        def oracle(path: Path) -> int:
            src = (path / "mod.py").read_text(encoding="utf-8")
            return 1 if "# BUG" in src else 0
        out = bisect_culprit(wt, shas[0], shas[5], oracle, skip_codes={125})
        assert out["culprit"] == shas[3] and out["inconclusive"] is False, out
        assert out["steps"] >= 1
    finally:
        _git(wt, "bisect", "reset")
        _git(repo, "worktree", "remove", "--force", str(wt))


def test_one_sided_range_is_bad_range(repo_with_regression, tmp_path):
    repo, shas = repo_with_regression
    wt = _worktree(repo, shas[5], tmp_path)
    try:
        # good NEWER than bad -> git rejects
        with pytest.raises(ToolError) as ei:
            bisect_culprit(wt, shas[5], shas[0], lambda p: 0, skip_codes={125})
        assert ei.value.code in ("BAD_RANGE", "BISECT_FAILED")
    finally:
        _git(wt, "bisect", "reset")
        _git(repo, "worktree", "remove", "--force", str(wt))
