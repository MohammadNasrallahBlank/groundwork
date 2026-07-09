import json
import os
import subprocess
from pathlib import Path

FIX = str(Path("tests/fixtures/cartomap").resolve())


def run_cli(*args, data_dir):
    env = {**os.environ, "GROUNDWORK_CACHE_DIR": str(data_dir)}
    return subprocess.run(["uv", "run", "groundwork", "cartographer", *args],
                          capture_output=True, text=True, env=env)


def test_map_emits_envelope(tmp_path):
    p = run_cli("map", "--root", FIX, "--budget", "2000", data_dir=tmp_path / "c")
    assert p.returncode == 0, p.stdout
    out = json.loads(p.stdout)
    assert out["ok"] and "helper" in out["data"]["map"]
    assert out["data"]["languages"] == ["python"]
    assert "\\" not in out["data"]["root"]


def test_bad_root_is_usage(tmp_path):
    p = run_cli("map", "--root", str(tmp_path / "nope"), data_dir=tmp_path / "c")
    assert p.returncode == 2
    assert json.loads(p.stdout)["error"]["code"] == "NO_ROOT"


def test_self_test(tmp_path):
    assert run_cli("self-test", data_dir=tmp_path / "c").returncode == 0
