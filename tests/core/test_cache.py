import pytest

from groundwork.core.cache import Cache, cache_key


def test_key_is_stable_and_input_sensitive(tmp_path):
    f = tmp_path / "a.txt"
    f.write_text("hello")
    k1 = cache_key("t", "1.0", {"x": 1, "y": 2}, [f])
    k2 = cache_key("t", "1.0", {"y": 2, "x": 1}, [f])  # dict order must not matter
    assert k1 == k2 and len(k1) == 64
    f.write_text("changed")
    assert cache_key("t", "1.0", {"x": 1, "y": 2}, [f]) != k1
    assert cache_key("t", "1.1", {"x": 1, "y": 2}, [f]) != k1  # version-sensitive


def test_put_get_roundtrip_and_miss(tmp_path):
    c = Cache(tmp_path / "cache")
    assert c.get("0" * 64) is None
    c.put("0" * 64, {"answer": 42})
    assert c.get("0" * 64) == {"answer": 42}


def test_stats_and_clear(tmp_path):
    c = Cache(tmp_path / "cache")
    c.put("a" * 64, {"v": 1})
    c.put("b" * 64, {"v": 2})
    s = c.stats()
    assert s["entries"] == 2 and s["bytes"] > 0
    c.clear()
    assert c.stats()["entries"] == 0


def test_get_treats_corrupt_entry_as_miss_and_removes_it(tmp_path):
    c = Cache(tmp_path / "cache")
    c.put("c" * 64, {"v": 1})
    blob = c._path("c" * 64)
    blob.write_text("{truncated", encoding="utf-8")
    assert c.get("c" * 64) is None
    assert not blob.exists()  # poisoned entry evicted, next put repopulates


def test_put_leaves_no_tmp_files(tmp_path):
    c = Cache(tmp_path / "cache")
    c.put("d" * 64, {"v": 2})
    leftovers = [p for p in (tmp_path / "cache").rglob("*") if p.suffix == ".tmp"]
    assert leftovers == []
    assert c.get("d" * 64) == {"v": 2}


def test_put_survives_stale_tmp_from_crashed_writer(tmp_path):
    # A prior writer for this same key crashed after creating its tmp file but
    # before os.replace. With a deterministic tmp name (p.name + ".tmp"), a
    # concurrent/subsequent put() for the SAME key would collide with that
    # leftover tmp file. With a unique-per-call tmp name, the stale file is
    # simply ignored and a fresh put+get roundtrip succeeds.
    c = Cache(tmp_path / "cache")
    key = "e" * 64
    p = c._path(key)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.with_name(p.name + ".deadbeef.tmp").write_text("{half", encoding="utf-8")
    c.put(key, {"v": 3})
    assert c.get(key) == {"v": 3}


def test_cache_root_env_override(tmp_path, monkeypatch):
    monkeypatch.setenv("GROUNDWORK_CACHE_DIR", str(tmp_path / "envcache"))
    c = Cache()
    assert c.root == tmp_path / "envcache"


def test_hash_file_is_public_and_stable(tmp_path):
    from groundwork.core.cache import hash_file
    f = tmp_path / "x.bin"
    f.write_bytes(b"abc")
    assert hash_file(f) == hash_file(f)
    assert len(hash_file(f)) == 64


def test_put_failure_raises_store_write(tmp_path, monkeypatch):
    from groundwork.core.runner import ToolError
    c = Cache(tmp_path / "cache")
    import groundwork.core.cache as cache_mod

    def _boom(*a, **kw):
        raise OSError("disk full")
    monkeypatch.setattr(cache_mod.os, "replace", _boom)
    with pytest.raises(ToolError) as e:
        c.put("f" * 64, {"v": 1})
    assert e.value.code == "STORE_WRITE"
