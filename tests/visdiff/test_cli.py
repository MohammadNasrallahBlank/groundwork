import json
import os
import subprocess
from pathlib import Path

import pytest

from groundwork.tools.visdiff.capture import browser_available

FIX = Path("tests/fixtures/visdiff").resolve()

requires_browser = pytest.mark.skipif(
    not browser_available(),
    reason="chromium not installed (run: groundwork visdiff install-browser)")


def run_cli(*args, data_dir, cwd=None):
    env = {**os.environ, "GROUNDWORK_DATA_DIR": str(data_dir)}
    return subprocess.run(["uv", "run", "groundwork", "visdiff", *args],
                          capture_output=True, text=True, env=env, cwd=cwd)


def test_self_test_is_browser_free(tmp_path):
    p = run_cli("self-test", data_dir=tmp_path / "d")
    assert p.returncode == 0, p.stdout
    assert json.loads(p.stdout)["data"]["self_test"] == "pass"


def test_check_without_baseline_exits_4(tmp_path):
    url = (FIX / "page.html").as_uri()
    p = run_cli("check", "--name", "ghost", "--url", url, data_dir=tmp_path / "d")
    assert p.returncode == 4, p.stdout
    assert json.loads(p.stdout)["error"]["code"] == "NO_BASELINE"


def test_bad_name_is_usage_error(tmp_path):
    p = run_cli("check", "--name", "../evil", "--url", "http://x",
                data_dir=tmp_path / "d")
    assert p.returncode == 2
    assert json.loads(p.stdout)["error"]["code"] == "BAD_NAME"


@requires_browser
def test_baseline_then_check_round_trip(tmp_path):
    url = (FIX / "page.html").as_uri()
    d = tmp_path / "d"
    p1 = run_cli("baseline", "--name", "home", "--url", url,
                 "--viewport", "640x480", data_dir=d, cwd=str(tmp_path))
    assert p1.returncode == 0, p1.stdout
    p2 = run_cli("check", "--name", "home", "--url", url,
                 "--viewport", "640x480", data_dir=d, cwd=str(tmp_path))
    assert p2.returncode == 0, p2.stdout
    out = json.loads(p2.stdout)
    assert out["data"]["passed"] is True
    assert "\\" not in out["data"]["composite_path"]
    p3 = run_cli("check", "--name", "home",
                 "--url", (FIX / "changed.html").as_uri(),
                 "--viewport", "640x480", data_dir=d, cwd=str(tmp_path))
    assert p3.returncode == 1
    assert json.loads(p3.stdout)["ok"] is True  # verdict is in the exit code
    p4 = run_cli("list", data_dir=d)
    assert any(b["name"] == "home" for b in json.loads(p4.stdout)["data"]["baselines"])
