from pathlib import Path

from groundwork.core.cache import Cache
from groundwork.tools.cartographer.mapper import build_map

FIX = Path("tests/fixtures/cartomap").resolve()


def test_build_map_over_fixture(tmp_path):
    out = build_map(FIX, budget=2000, cache=Cache(tmp_path / "c"))
    assert out["root"] == FIX.as_posix()
    assert out["files_scanned"] >= 2
    assert "python" in out["languages"]
    assert "helper" in out["map"] and "App" in out["map"]


def test_second_build_hits_cache(tmp_path):
    cache = Cache(tmp_path / "c")
    build_map(FIX, budget=2000, cache=cache)
    out = build_map(FIX, budget=2000, cache=cache)
    assert out["_cache"] == "hit"


def test_ignores_dot_dirs_and_non_source(tmp_path):
    root = tmp_path / "proj"
    (root / ".venv").mkdir(parents=True)
    (root / ".venv" / "ignored.py").write_text("def hidden(): pass\n", encoding="utf-8")
    (root / "real.py").write_text("def shown(): pass\n", encoding="utf-8")
    out = build_map(root, budget=2000, cache=Cache(tmp_path / "c"))
    assert "shown" in out["map"] and "hidden" not in out["map"]
