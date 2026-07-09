import pytest

from groundwork.core.atomicjson import write_atomic
from groundwork.core.runner import ToolError


def test_write_atomic_roundtrip_and_no_tmp(tmp_path):
    p = tmp_path / "sub" / "x.json"
    write_atomic(p, '{"a":1}')
    assert p.read_text(encoding="utf-8") == '{"a":1}'
    assert [q for q in tmp_path.rglob("*.tmp")] == []


def test_write_atomic_names_store_write_error_when_parent_is_a_file(tmp_path):
    blocker = tmp_path / "blocker"
    blocker.write_text("i am a file", encoding="utf-8")
    with pytest.raises(ToolError) as e:
        write_atomic(blocker / "child.json", "{}")  # parent is a file → OSError
    assert e.value.code == "STORE_WRITE"
    assert "child.json" in str(e.value)
