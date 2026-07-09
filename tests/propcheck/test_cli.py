import json
import os
import subprocess
from pathlib import Path


def run_cli(*args, cwd):
    return subprocess.run(["uv", "run", "groundwork", "propcheck", *args],
                          capture_output=True, text=True, env={**os.environ},
                          cwd=cwd)


def _codec(tmp_path: Path, buggy: bool):
    dec = ("    return int(s) if s != '0' else 999\n" if buggy
           else "    return int(s)\n")
    (tmp_path / "codec.py").write_text(
        "def enc(x):\n    return str(x)\n\ndef dec(s):\n" + dec,
        encoding="utf-8", newline="\n")


def test_new_writes_a_compiling_property_file(tmp_path):
    _codec(tmp_path, buggy=False)
    p = run_cli("new", "--invariant", "roundtrip", "--module", "codec",
                "--func", "enc", "--inverse", "codec.dec", "--strategy", "int",
                "--out", "test_prop.py", cwd=str(tmp_path))
    assert p.returncode == 0, p.stdout
    gen = (tmp_path / "test_prop.py").read_text(encoding="utf-8")
    compile(gen, "<f>", "exec")
    assert "dec(enc(x)) == x" in gen


def test_new_refuses_overwrite_without_force(tmp_path):
    _codec(tmp_path, buggy=False)
    (tmp_path / "test_prop.py").write_text("# existing\n", encoding="utf-8")
    p = run_cli("new", "--invariant", "idempotent", "--module", "codec",
                "--func", "enc", "--strategy", "int", "--out", "test_prop.py",
                cwd=str(tmp_path))
    assert p.returncode == 2
    assert json.loads(p.stdout)["error"]["code"] == "EXISTS"


def test_run_passing_property(tmp_path):
    _codec(tmp_path, buggy=False)
    run_cli("new", "--invariant", "roundtrip", "--module", "codec", "--func",
            "enc", "--inverse", "codec.dec", "--strategy", "int", "--out",
            "test_prop.py", cwd=str(tmp_path))
    p = run_cli("run", "--file", "test_prop.py", cwd=str(tmp_path))
    assert p.returncode == 0, p.stdout
    assert json.loads(p.stdout)["data"]["passed"] is True


def test_run_failing_property_reports_counterexample_exit_1(tmp_path):
    _codec(tmp_path, buggy=True)
    run_cli("new", "--invariant", "roundtrip", "--module", "codec", "--func",
            "enc", "--inverse", "codec.dec", "--strategy", "int", "--out",
            "test_prop.py", cwd=str(tmp_path))
    p = run_cli("run", "--file", "test_prop.py", cwd=str(tmp_path))
    assert p.returncode == 1
    data = json.loads(p.stdout)["data"]
    assert data["passed"] is False
    assert data["properties"][0]["counterexample"]["x"] == "0"


def test_new_unknown_strategy_exits_2(tmp_path):
    _codec(tmp_path, buggy=False)
    p = run_cli("new", "--invariant", "idempotent", "--module", "codec",
                "--func", "enc", "--strategy", "banana", "--out", "t.py",
                cwd=str(tmp_path))
    assert p.returncode == 2
    assert json.loads(p.stdout)["error"]["code"] == "BAD_STRATEGY"


def test_self_test(tmp_path):
    p = run_cli("self-test", cwd=str(tmp_path))
    assert p.returncode == 0, p.stdout
    assert json.loads(p.stdout)["data"]["self_test"] == "pass"
