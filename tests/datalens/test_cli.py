import json
import os
import subprocess


def run_cli(*args, cwd):
    return subprocess.run(["uv", "run", "groundwork", "datalens", *args],
                          capture_output=True, text=True, env={**os.environ},
                          cwd=cwd)


def test_profile_emits_report(csv_file, tmp_path):
    p = run_cli("profile", "--file", str(csv_file), cwd=str(tmp_path))
    assert p.returncode == 0, p.stdout
    data = json.loads(p.stdout)["data"]
    assert data["rows"] == 4 and data["columns"] == 3


def test_profile_sqlite_needs_table_exits_4(sqlite_file, tmp_path):
    p = run_cli("profile", "--file", str(sqlite_file), cwd=str(tmp_path))
    assert p.returncode == 4
    assert json.loads(p.stdout)["error"]["code"] == "NEED_TABLE"


def test_compare_emits_drift(tmp_path):
    a = tmp_path / "a.csv"
    a.write_text("v\n" + "\n".join(str(i) for i in range(1, 21)) + "\n",
                 encoding="utf-8")
    b = tmp_path / "b.csv"
    b.write_text("v\n" + "\n".join(str(i) for i in range(81, 101)) + "\n",
                 encoding="utf-8")
    p = run_cli("compare", "--a", str(a), "--b", str(b), cwd=str(tmp_path))
    assert p.returncode == 0, p.stdout
    assert json.loads(p.stdout)["data"]["numeric_drift"]["v"]["psi"] > 0.25


def test_missing_file_exits_2(tmp_path):
    p = run_cli("profile", "--file", str(tmp_path / "nope.csv"), cwd=str(tmp_path))
    assert p.returncode == 2
    assert json.loads(p.stdout)["error"]["code"] == "NO_FILE"


def test_self_test(tmp_path):
    p = run_cli("self-test", cwd=str(tmp_path))
    assert p.returncode == 0, p.stdout
    assert json.loads(p.stdout)["data"]["self_test"] == "pass"
