import json
import os
import subprocess
import sys
from pathlib import Path

# use this interpreter (the one with pytest) as the oracle, not bare "python"
_PYTEST = f"{sys.executable} -m pytest -q"


def run_cli(*args, cwd):
    return subprocess.run(["uv", "run", "groundwork", "bisector", *args],
                          capture_output=True, text=True, env={**os.environ},
                          cwd=cwd)


def _git(root, *a):
    return subprocess.run(["git", *a], cwd=root, capture_output=True, text=True,
                          encoding="utf-8")


def _repo_with_regression(tmp_path: Path):
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "t@t")
    _git(tmp_path, "config", "user.name", "t")
    shas = []
    # unique per-commit content (a running step counter) so git bisect cannot
    # same-tree-shortcut; the pytest oracle genuinely decides each commit.
    for i in range(6):
        val = 99 if i >= 3 else i               # commit 3 breaks v() == step
        (tmp_path / "mod.py").write_text(f"STEP = {i}\ndef v():\n    return {val}\n",
                                         encoding="utf-8", newline="\n")
        (tmp_path / "test_mod.py").write_text(
            "import mod\ndef test_v():\n    assert mod.v() == mod.STEP\n",
            encoding="utf-8", newline="\n")
        msg = "regression: break v (#31)" if i == 3 else f"commit {i}"
        _git(tmp_path, "add", "-A")
        _git(tmp_path, "commit", "-qm", msg)
        shas.append(_git(tmp_path, "rev-parse", "HEAD").stdout.strip())
    return shas


def test_bisector_finds_culprit_with_pytest_oracle(tmp_path):
    shas = _repo_with_regression(tmp_path)
    p = run_cli("run", "--good", shas[0], "--bad", shas[5],
                "--oracle", _PYTEST, cwd=str(tmp_path))
    assert p.returncode == 0, p.stdout
    data = json.loads(p.stdout)["data"]
    assert data["culprit"] is not None, data           # transcript explains why
    assert data["culprit"]["sha"].startswith(shas[3][:12])
    assert data["culprit"]["summary"].startswith("regression: break v")
    assert any(r["number"] == 31 for r in data["culprit"]["refs"])
    # the main worktree is undisturbed (no leftover worktrees)
    wl = _git(tmp_path, "worktree", "list").stdout
    assert wl.count("\n") <= 1                    # only the main worktree


def test_bad_range_exits_2(tmp_path):
    shas = _repo_with_regression(tmp_path)
    p = run_cli("run", "--good", shas[5], "--bad", shas[0],
                "--oracle", _PYTEST, cwd=str(tmp_path))
    assert p.returncode == 2
    assert json.loads(p.stdout)["error"]["code"] == "BAD_RANGE"


def test_self_test(tmp_path):
    p = run_cli("self-test", cwd=str(tmp_path))
    assert p.returncode == 0, p.stdout
    assert json.loads(p.stdout)["data"]["self_test"] == "pass"
