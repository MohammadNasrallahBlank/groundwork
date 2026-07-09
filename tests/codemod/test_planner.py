import pytest

from groundwork.core.runner import ToolError
from groundwork.tools.codemod.planner import build_plan, load_plan


@pytest.fixture()
def proj(tmp_path):
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / "a.py").write_text(
        "def f():\n    print(1)\n", encoding="utf-8", newline="\n")
    (tmp_path / "pkg" / "b.py").write_text(
        "x = 1\n", encoding="utf-8", newline="\n")
    (tmp_path / "pkg" / "broken.py").write_text(
        "def broken(:\n", encoding="utf-8", newline="\n")
    (tmp_path / ".venv").mkdir()
    (tmp_path / ".venv" / "skip.py").write_text(
        "print(9)\n", encoding="utf-8", newline="\n")
    return tmp_path


def test_plan_records_changes_and_skips_and_errors(proj):
    out = build_plan(proj, engine="ast-grep", pattern="print($A)",
                     rewrite="log($A)", lang="python", preset=None, glob=None)
    assert out["files_scanned"] == 3            # .venv skipped by walk rules
    assert out["files_changed"] == 1
    assert out["total_matches"] == 1
    assert out["changes"][0]["file"] == "pkg/a.py"
    assert "-    print(1)" in out["changes"][0]["diff"]
    assert "+    log(1)" in out["changes"][0]["diff"]
    # ast-grep parses aggressively; a syntactically broken file either errors
    # or simply doesn't match — it must NOT abort the plan. If it errored it
    # appears here; either way the plan exists and is loadable.
    plan = load_plan(proj, out["plan_id"])
    assert plan["files"][0]["new_content"] == "def f():\n    log(1)\n"
    assert plan["files"][0]["old_sha256"]


def test_plan_is_deterministic(proj):
    a = build_plan(proj, engine="ast-grep", pattern="print($A)",
                   rewrite="log($A)", lang="python", preset=None, glob=None)
    b = build_plan(proj, engine="ast-grep", pattern="print($A)",
                   rewrite="log($A)", lang="python", preset=None, glob=None)
    assert a["plan_id"] == b["plan_id"]


def test_plan_nothing_matched_is_success(proj):
    out = build_plan(proj, engine="ast-grep", pattern="frobnicate($A)",
                     rewrite="x($A)", lang="python", preset=None, glob=None)
    assert out["files_changed"] == 0 and out["changes"] == []


def test_preset_plan_uses_python_glob(proj):
    out = build_plan(proj, engine="preset", pattern=None, rewrite=None,
                     lang=None, preset="py-remove-unused-imports", glob=None)
    assert out["engine"] == "preset" and out["preset"] == "py-remove-unused-imports"
    # broken.py cannot parse under libcst -> listed as a per-file error
    assert any(e["file"] == "pkg/broken.py" for e in out["errors"])


def test_load_missing_plan_is_usage(proj):
    with pytest.raises(ToolError) as ei:
        load_plan(proj, "deadbeef0000")
    assert ei.value.code == "NO_PLAN" and ei.value.exit_code == 2


def test_plan_never_touches_source_files(proj):
    before = (proj / "pkg" / "a.py").read_text(encoding="utf-8")
    build_plan(proj, engine="ast-grep", pattern="print($A)",
               rewrite="log($A)", lang="python", preset=None, glob=None)
    assert (proj / "pkg" / "a.py").read_text(encoding="utf-8") == before
