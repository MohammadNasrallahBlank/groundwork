import pytest

from groundwork.tools.depsurface import store


def snap(version):
    return {"package": "demopkg", "version": version, "language": "python",
            "modules": {}}


def test_roundtrip_and_versions(tmp_path, monkeypatch):
    monkeypatch.setenv("GROUNDWORK_DATA_DIR", str(tmp_path))
    p = store.save_snapshot(snap("1.0.0"))
    store.save_snapshot(snap("2.0.0"))
    assert p.name == "demopkg@1.0.0.json"
    assert store.load_snapshot("demopkg", "1.0.0")["version"] == "1.0.0"
    assert store.load_snapshot("demopkg", "9.9.9") is None
    assert store.list_versions("demopkg") == ["1.0.0", "2.0.0"]
    assert store.list_versions("other") == []


def test_save_is_atomic_no_tmp_leftovers(tmp_path, monkeypatch):
    monkeypatch.setenv("GROUNDWORK_DATA_DIR", str(tmp_path))
    store.save_snapshot(snap("1.0.0"))
    assert [p for p in tmp_path.rglob("*.tmp")] == []


def test_load_corrupt_snapshot_is_miss_and_evicted(tmp_path, monkeypatch):
    monkeypatch.setenv("GROUNDWORK_DATA_DIR", str(tmp_path))
    store.save_snapshot(snap("1.0.0"))
    p = store.store_dir() / "demopkg@1.0.0.json"
    p.write_text("{truncated", encoding="utf-8")
    assert store.load_snapshot("demopkg", "1.0.0") is None
    assert not p.exists()


def test_snapshot_path_containment(tmp_path, monkeypatch):
    monkeypatch.setenv("GROUNDWORK_DATA_DIR", str(tmp_path))
    # NOTE: "../../evil" (as given in the original report) does NOT actually
    # escape the store dir here: the literal filename segment produced is
    # "demopkg@.." (the "@" glues to the first ".." before the next "/"), so
    # only the *second* ".." cancels it back to exactly the store dir itself.
    # "../evil" has just one ".." after the glued "demopkg@.." segment, which
    # is kept as a literal (non-canonical) path component and genuinely
    # resolves outside the store dir — verified interactively before writing
    # this assertion.
    with pytest.raises(ValueError):
        store.save_snapshot(snap("../evil"))
