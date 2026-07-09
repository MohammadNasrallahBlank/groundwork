import json
import os
import subprocess
from pathlib import Path

FIXTURE_SP = str(Path("tests/fixtures/sitepkgs").resolve())


def run_cli(*args, data_dir, cache_dir):
    env = {**os.environ, "GROUNDWORK_DATA_DIR": str(data_dir),
           "GROUNDWORK_CACHE_DIR": str(cache_dir)}
    return subprocess.run(["uv", "run", "groundwork", "depsurface", *args],
                          capture_output=True, text=True, env=env)


def test_api_extracts_and_snapshots(tmp_path):
    p = run_cli("api", "demopkg", "--site-packages", FIXTURE_SP,
                data_dir=tmp_path / "d", cache_dir=tmp_path / "c")
    assert p.returncode == 0, p.stdout
    out = json.loads(p.stdout)
    assert out["ok"] and out["data"]["version"] == "1.2.3"
    assert out["meta"]["cache"] == "miss"
    assert "demopkg.core" in out["data"]["modules"]
    assert (tmp_path / "d" / "depsurface" / "demopkg@1.2.3.json").exists()


def test_api_second_run_hits_cache(tmp_path):
    kw = {"data_dir": tmp_path / "d", "cache_dir": tmp_path / "c"}
    run_cli("api", "demopkg", "--site-packages", FIXTURE_SP, **kw)
    p = run_cli("api", "demopkg", "--site-packages", FIXTURE_SP, **kw)
    out = json.loads(p.stdout)
    assert out["meta"]["cache"] == "hit"
    assert out["data"]["version"] == "1.2.3"


def test_symbol_filter_and_not_found(tmp_path):
    kw = {"data_dir": tmp_path / "d", "cache_dir": tmp_path / "c"}
    p = run_cli("api", "demopkg", "--site-packages", FIXTURE_SP,
                "--symbol", "core.Engine.start", **kw)
    out = json.loads(p.stdout)
    assert out["data"]["matches"] == {
        "demopkg.core.Engine.start": "method (self, speed: int = 1) -> bool"}
    p2 = run_cli("api", "demopkg", "--site-packages", FIXTURE_SP,
                 "--symbol", "nope.nothing", **kw)
    assert p2.returncode == 1
    assert json.loads(p2.stdout)["error"]["code"] == "SYMBOL_NOT_FOUND"


def test_diff_between_stored_snapshots(tmp_path):
    data = tmp_path / "d"
    store = data / "depsurface"
    store.mkdir(parents=True)
    base = {"package": "demopkg", "language": "python", "modules": {
        "demopkg": {"doc": None, "exports": None, "attributes": {}, "classes": {},
                    "functions": {"f": {"sig": "(x: int) -> int", "doc": None}},
                    "aliases": {}}}}
    (store / "demopkg@1.0.0.json").write_text(
        json.dumps({**base, "version": "1.0.0"}), encoding="utf-8")
    changed = json.loads(json.dumps(base))
    changed["modules"]["demopkg"]["functions"]["f"]["sig"] = "(x: int, y: int) -> int"
    (store / "demopkg@2.0.0.json").write_text(
        json.dumps({**changed, "version": "2.0.0"}), encoding="utf-8")
    p = run_cli("diff", "demopkg", "1.0.0", "2.0.0",
                data_dir=data, cache_dir=tmp_path / "c")
    assert p.returncode == 0, p.stdout
    out = json.loads(p.stdout)
    assert out["data"]["changed"][0]["symbol"] == "demopkg.f"


def test_diff_missing_snapshot_lists_available(tmp_path):
    p = run_cli("diff", "demopkg", "1.0.0", "3.0.0",
                data_dir=tmp_path / "d", cache_dir=tmp_path / "c")
    assert p.returncode == 1
    out = json.loads(p.stdout)
    assert out["error"]["code"] == "MISSING_SNAPSHOT"


def test_no_venv_is_named_error(tmp_path):
    p = run_cli("api", "demopkg", "--root", str(tmp_path),
                data_dir=tmp_path / "d", cache_dir=tmp_path / "c")
    assert p.returncode == 1
    assert json.loads(p.stdout)["error"]["code"] == "NO_SITE_PACKAGES"


def test_self_test(tmp_path):
    p = run_cli("self-test", data_dir=tmp_path / "d", cache_dir=tmp_path / "c")
    assert p.returncode == 0


def test_symbol_equal_to_package_returns_whole_surface(tmp_path):
    kw = {"data_dir": tmp_path / "d", "cache_dir": tmp_path / "c"}
    p = run_cli("api", "demopkg", "--site-packages", FIXTURE_SP,
                "--symbol", "demopkg", **kw)
    assert p.returncode == 0, p.stdout
    out = json.loads(p.stdout)
    assert "demopkg.core.Engine.start" in out["data"]["matches"]


def test_usage_error_carries_real_message(tmp_path):
    p = run_cli("api", data_dir=tmp_path / "d", cache_dir=tmp_path / "c")  # missing package
    assert p.returncode == 2
    err = json.loads(p.stdout)["error"]
    assert err["code"] == "USAGE" and err["message"] not in ("2", "")


def test_traversal_package_name_is_rejected(tmp_path):
    kw = {"data_dir": tmp_path / "d", "cache_dir": tmp_path / "c"}
    p = run_cli("api", "../evil", "--site-packages", FIXTURE_SP, **kw)
    assert p.returncode == 2
    assert json.loads(p.stdout)["error"]["code"] == "USAGE"
    assert not (tmp_path / "evil@unknown.json").exists()


def test_traversal_diff_args_rejected_and_nothing_deleted(tmp_path):
    victim = tmp_path / "victim@1.0.0.json"
    victim.write_text("not json", encoding="utf-8")
    p = run_cli("diff", "../../" + victim.parent.name + "/victim", "1.0.0", "2.0.0",
                data_dir=tmp_path / "d", cache_dir=tmp_path / "c")
    assert p.returncode == 2
    assert victim.exists()  # eviction never reached an out-of-store path
