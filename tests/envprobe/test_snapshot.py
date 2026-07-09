import json

from groundwork.tools.envprobe import snapshot


def test_build_snapshot_shape_and_no_env_values(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVPROBE_SENTINEL_SECRET", "hunter2-do-not-leak")
    (tmp_path / "uv.lock").write_text("lock", encoding="utf-8")
    s = snapshot.build_snapshot(tmp_path)
    assert set(s) == {"root", "os", "runtimes", "lockfiles", "env_names", "env_count"}
    assert s["root"] == tmp_path.resolve().as_posix()
    assert "ENVPROBE_SENTINEL_SECRET" in s["env_names"]
    assert s["env_count"] == len(s["env_names"])
    assert "uv.lock" in s["lockfiles"]
    assert "git" in s["runtimes"]
    assert "hunter2-do-not-leak" not in json.dumps(s)  # values NEVER leave


def test_baseline_roundtrip_and_missing(tmp_path, monkeypatch):
    monkeypatch.setenv("GROUNDWORK_DATA_DIR", str(tmp_path / "data"))
    root = tmp_path / "proj"
    root.mkdir()
    assert snapshot.load_baseline(root) is None
    s = snapshot.build_snapshot(root)
    p = snapshot.save_baseline(s)
    assert p.exists() and p.suffix == ".json"
    assert snapshot.load_baseline(root) == s
    assert not list(p.parent.glob("*.tmp"))


def test_diff_env_reports_drift():
    old = {"root": "r", "os": {"system": "W"}, "runtimes":
           {"git": {"version": "2.44.0", "raw": "git version 2.44.0"}},
           "lockfiles": {"uv.lock": "aaa"}, "env_names": ["A", "B"], "env_count": 2}
    new = {"root": "r", "os": {"system": "W"}, "runtimes":
           {"git": {"version": "2.45.1", "raw": "git version 2.45.1"},
            "go": {"version": "1.22.0", "raw": "go version go1.22.0"}},
           "lockfiles": {"uv.lock": "bbb"}, "env_names": ["B", "C"], "env_count": 2}
    d = snapshot.diff_env(old, new)
    assert d["drift"] is True
    assert d["runtimes"]["added"] == ["go"]
    assert d["runtimes"]["changed"] == [{"name": "git", "before": "2.44.0", "after": "2.45.1"}]
    assert d["lockfiles"]["changed"] == [{"name": "uv.lock", "before": "aaa", "after": "bbb"}]
    assert d["env_names"] == {"added": ["C"], "removed": ["A"]}


def test_diff_env_identical_is_no_drift():
    s = {"root": "r", "os": {"system": "W"}, "runtimes": {}, "lockfiles": {},
         "env_names": [], "env_count": 0}
    d = snapshot.diff_env(s, s)
    assert d["drift"] is False


def test_render_digest_one_line_no_values(tmp_path, monkeypatch):
    monkeypatch.setenv("ENVPROBE_SENTINEL_SECRET", "hunter2-do-not-leak")
    s = snapshot.build_snapshot(tmp_path)
    line = snapshot.render_digest(s)
    assert "\n" not in line
    assert "git=" in line and "env:" in line
    assert "hunter2-do-not-leak" not in line
