import json
import subprocess


def test_cache_stats_runs():
    p = subprocess.run(["uv", "run", "groundwork", "cache", "stats"],
                       capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    out = json.loads(p.stdout)
    assert set(out["data"]) == {"entries", "bytes", "root"}
    assert "\\" not in out["data"]["root"]
