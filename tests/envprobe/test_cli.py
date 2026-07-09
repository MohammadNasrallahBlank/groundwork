import json
import os
import subprocess


def run_cli(*args, data_dir, extra_env=None):
    env = {**os.environ, "GROUNDWORK_DATA_DIR": str(data_dir), **(extra_env or {})}
    return subprocess.run(["uv", "run", "groundwork", "envprobe", *args],
                          capture_output=True, text=True, env=env)


def test_snapshot_saves_baseline_and_masks_values(tmp_path):
    p = run_cli("snapshot", "--root", str(tmp_path),
                data_dir=tmp_path / "d",
                extra_env={"ENVPROBE_SENTINEL_SECRET": "hunter2-do-not-leak"})
    assert p.returncode == 0, p.stdout
    out = json.loads(p.stdout)
    assert out["ok"] and out["data"]["env_count"] > 0
    assert "ENVPROBE_SENTINEL_SECRET" in out["data"]["env_names"]
    assert "hunter2-do-not-leak" not in p.stdout
    assert list((tmp_path / "d" / "envprobe").glob("*.json"))


def test_diff_without_baseline_exits_4(tmp_path):
    p = run_cli("diff", "--root", str(tmp_path), data_dir=tmp_path / "d")
    assert p.returncode == 4
    assert json.loads(p.stdout)["error"]["code"] == "NO_BASELINE"


def test_diff_reports_env_name_drift(tmp_path):
    kw = {"data_dir": tmp_path / "d"}
    assert run_cli("snapshot", "--root", str(tmp_path), **kw).returncode == 0
    p = run_cli("diff", "--root", str(tmp_path),
                extra_env={"ENVPROBE_NEW_VAR_XYZ": "1"}, **kw)
    assert p.returncode == 0, p.stdout
    d = json.loads(p.stdout)["data"]
    assert "ENVPROBE_NEW_VAR_XYZ" in d["env_names"]["added"]
    assert d["drift"] is True


def test_digest_is_one_line(tmp_path):
    p = run_cli("digest", "--root", str(tmp_path), data_dir=tmp_path / "d")
    assert p.returncode == 0
    digest = json.loads(p.stdout)["data"]["digest"]
    assert "\n" not in digest and "env:" in digest


def test_bad_root_is_usage_error(tmp_path):
    p = run_cli("snapshot", "--root", str(tmp_path / "nope"), data_dir=tmp_path / "d")
    assert p.returncode == 2
    assert json.loads(p.stdout)["error"]["code"] == "NO_ROOT"


def test_self_test(tmp_path):
    p = run_cli("self-test", data_dir=tmp_path / "d")
    assert p.returncode == 0
