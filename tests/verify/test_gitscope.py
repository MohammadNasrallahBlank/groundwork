import subprocess
from pathlib import Path

from groundwork.tools.verify.gitscope import changed_files


def make_repo(tmp_path: Path) -> Path:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t",
                    "commit", "--allow-empty", "-m", "init", "-q"], cwd=tmp_path, check=True)
    return tmp_path


def test_changed_files_sees_modified_and_untracked(tmp_path):
    repo = make_repo(tmp_path)
    (repo / "tracked.py").write_text("x = 1\n")
    subprocess.run(["git", "add", "tracked.py"], cwd=repo, check=True)
    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t",
                    "commit", "-m", "add", "-q"], cwd=repo, check=True)
    (repo / "tracked.py").write_text("x = 2\n")      # modified
    (repo / "new_file.py").write_text("y = 1\n")      # untracked
    got = changed_files(repo)
    assert sorted(got) == ["new_file.py", "tracked.py"]


def test_non_repo_returns_none(tmp_path):
    assert changed_files(tmp_path) is None
