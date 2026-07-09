import json
import os
import subprocess
from pathlib import Path

import pytest


def run_cli(*args, cwd):
    return subprocess.run(["uv", "run", "groundwork", "codemod", *args],
                          capture_output=True, text=True, env={**os.environ},
                          cwd=cwd)


def _git(root: Path, *args):
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)


@pytest.fixture()
def repo(tmp_path):
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "t@t")
    _git(tmp_path, "config", "user.name", "t")
    (tmp_path / "a.py").write_text("def f():\n    print(1)\n",
                                   encoding="utf-8", newline="\n")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-qm", "init")
    return tmp_path


def test_plan_then_apply_round_trip(repo):
    p1 = run_cli("plan", "--pattern", "print($A)", "--rewrite", "log($A)",
                 "--lang", "python", cwd=str(repo))
    assert p1.returncode == 0, p1.stdout
    data = json.loads(p1.stdout)["data"]
    assert data["files_changed"] == 1
    plan_id = data["plan_id"]
    # plan must not have modified the source
    assert (repo / "a.py").read_text(encoding="utf-8") == "def f():\n    print(1)\n"
    p2 = run_cli("apply", "--plan", plan_id, "--no-verify", cwd=str(repo))
    assert p2.returncode == 0, p2.stdout
    assert (repo / "a.py").read_text(encoding="utf-8") == "def f():\n    log(1)\n"


def test_apply_dirty_tree_exits_1(repo):
    p1 = run_cli("plan", "--pattern", "print($A)", "--rewrite", "log($A)",
                 "--lang", "python", cwd=str(repo))
    plan_id = json.loads(p1.stdout)["data"]["plan_id"]
    (repo / "a.py").write_text("def f():\n    print(2)\n",
                               encoding="utf-8", newline="\n")
    p2 = run_cli("apply", "--plan", plan_id, "--no-verify", cwd=str(repo))
    assert p2.returncode == 1
    assert json.loads(p2.stdout)["error"]["code"] == "DIRTY_TREE"


def test_plan_requires_lang_for_astgrep(repo):
    p = run_cli("plan", "--pattern", "print($A)", "--rewrite", "log($A)",
                cwd=str(repo))
    assert p.returncode == 2
    assert json.loads(p.stdout)["error"]["code"] == "USAGE"


def test_presets_lists_engines_and_presets(repo):
    p = run_cli("presets", cwd=str(repo))
    assert p.returncode == 0
    data = json.loads(p.stdout)["data"]
    assert "py-fstringify" in data["presets"]
    assert data["engines"]["ast-grep"] is True
    assert isinstance(data["engines"]["comby"], bool)


def test_self_test(repo):
    p = run_cli("self-test", cwd=str(repo))
    assert p.returncode == 0, p.stdout
    assert json.loads(p.stdout)["data"]["self_test"] == "pass"
