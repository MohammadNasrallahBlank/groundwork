import subprocess

import pytest

from groundwork.core.runner import ToolError
from groundwork.tools.covdiff.diffparse import git_diff, parse_diff

_DIFF = """diff --git a/mod.py b/mod.py
index b1bfde2..3740e3a 100644
--- a/mod.py
+++ b/mod.py
@@ -2 +2,4 @@ def a():
-    return 1
+    return 99
+
+def b():
+    return 2
"""


def test_parse_added_lines_from_hunk():
    assert parse_diff(_DIFF) == {"mod.py": {2, 3, 4, 5}}


def test_parse_pure_deletion_adds_nothing():
    diff = ("diff --git a/x.py b/x.py\n--- a/x.py\n+++ b/x.py\n"
            "@@ -3,2 +2,0 @@\n-gone1\n-gone2\n")
    assert parse_diff(diff) == {"x.py": set()}


def test_parse_multiple_files():
    diff = ("--- a/one.py\n+++ b/one.py\n@@ -1 +1 @@\n-a\n+b\n"
            "--- a/two.py\n+++ b/two.py\n@@ -0,0 +1,2 @@\n+x\n+y\n")
    assert parse_diff(diff) == {"one.py": {1}, "two.py": {1, 2}}


def test_empty_diff_is_empty_map():
    assert parse_diff("") == {}


def _git(root, *a):
    subprocess.run(["git", *a], cwd=root, check=True, capture_output=True)


def test_git_diff_against_head(tmp_path):
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "t@t")
    _git(tmp_path, "config", "user.name", "t")
    (tmp_path / "m.py").write_text("def a():\n    return 1\n",
                                   encoding="utf-8", newline="\n")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-qm", "init")
    (tmp_path / "m.py").write_text("def a():\n    return 2\n\ndef b():\n    pass\n",
                                   encoding="utf-8", newline="\n")
    diff = git_diff(tmp_path)
    parsed = parse_diff(diff)
    assert parsed["m.py"] >= {2, 3, 4}


def test_git_diff_outside_repo_raises(tmp_path, monkeypatch):
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path.parent))
    with pytest.raises(ToolError) as ei:
        git_diff(tmp_path)
    assert ei.value.code == "NO_GIT" and ei.value.exit_code == 3
