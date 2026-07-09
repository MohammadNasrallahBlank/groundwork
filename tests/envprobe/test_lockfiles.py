from groundwork.tools.envprobe.lockfiles import LOCKFILES, hash_lockfiles


def test_hashes_present_lockfiles_only(tmp_path):
    (tmp_path / "uv.lock").write_text("locked-a", encoding="utf-8")
    (tmp_path / "package-lock.json").write_text("{}", encoding="utf-8")
    out = hash_lockfiles(tmp_path)
    assert set(out) == {"uv.lock", "package-lock.json"}
    assert all(len(h) == 64 for h in out.values())


def test_hash_changes_with_content(tmp_path):
    f = tmp_path / "uv.lock"
    f.write_text("v1", encoding="utf-8")
    h1 = hash_lockfiles(tmp_path)["uv.lock"]
    f.write_text("v2", encoding="utf-8")
    assert hash_lockfiles(tmp_path)["uv.lock"] != h1


def test_empty_root_is_empty_dict(tmp_path):
    assert hash_lockfiles(tmp_path) == {}


def test_lockfile_set_is_the_specified_eight():
    assert set(LOCKFILES) == {"uv.lock", "poetry.lock", "requirements.txt",
                              "package-lock.json", "pnpm-lock.yaml", "yarn.lock",
                              "Cargo.lock", "go.sum"}
