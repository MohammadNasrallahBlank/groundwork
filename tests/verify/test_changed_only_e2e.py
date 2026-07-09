import json
import shutil
import subprocess


def git(repo, *a):
    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", *a],
                   cwd=repo, check=True, capture_output=True)


def test_changed_only_skips_lint_on_untouched_files(tmp_path):
    repo = tmp_path / "proj"
    shutil.copytree("tests/fixtures/pyfail", repo)
    git(repo, "init", "-q")
    git(repo, "add", "-A")
    git(repo, "commit", "-m", "init", "-q")
    # touch ONLY the test file; calc.py (which holds the F401) is untouched
    tf = repo / "tests" / "test_calc.py"
    tf.write_text(tf.read_text() + "\n# comment\n")
    p = subprocess.run(["uv", "run", "groundwork", "verify", "run",
                        "--root", str(repo), "--changed-only"],
                       capture_output=True, text=True)
    out = json.loads(p.stdout)
    rules = {d["rule"] for d in out["data"]["diagnostics"]}
    assert "F401" not in rules                     # ruff scoped away from calc.py
    assert out["data"]["summary"]["counts"]["error"] == 1  # pytest failure still caught
