import json
import subprocess

import pytest

from groundwork.tools.gitwhy.churn import churn_report


def _git(root, *a):
    subprocess.run(["git", *a], cwd=root, check=True, capture_output=True)


@pytest.fixture()
def repo(tmp_path):
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "a@x")
    _git(tmp_path, "config", "user.name", "a")
    for i in range(3):                          # hot.py changes 3x, cold.py once
        (tmp_path / "hot.py").write_text(f"x = {i}\n", encoding="utf-8", newline="\n")
        if i == 0:
            (tmp_path / "cold.py").write_text("y = 0\n", encoding="utf-8", newline="\n")
        _git(tmp_path, "add", "-A")
        _git(tmp_path, "commit", "-qm", f"c{i}")
    return tmp_path


def test_churn_ranks_by_frequency(repo):
    out = churn_report(repo, since=None, count=200, top=20, coverage_json=None)
    files = {f["file"]: f["changes"] for f in out["files"]}
    assert files["hot.py"] == 3 and files["cold.py"] == 1
    assert out["files"][0]["file"] == "hot.py"     # highest first


def test_churn_top_limits(repo):
    out = churn_report(repo, since=None, count=200, top=1, coverage_json=None)
    assert len(out["files"]) == 1 and out["files"][0]["file"] == "hot.py"


def test_churn_risk_from_coverage(repo, tmp_path):
    cov = tmp_path / "cov.json"
    cov.write_text(json.dumps({"files": {
        "hot.py": {"executed_lines": [1], "missing_lines": [2, 3, 4]},
        "cold.py": {"executed_lines": [1, 2, 3, 4], "missing_lines": []}}}),
        encoding="utf-8")
    out = churn_report(repo, since=None, count=200, top=20, coverage_json=cov)
    hot = [f for f in out["files"] if f["file"] == "hot.py"][0]
    assert hot["coverage_ratio"] == 0.25
    assert hot["risk"] == round(3 * (1 - 0.25), 4)
    assert out["files"][0]["file"] == "hot.py"
