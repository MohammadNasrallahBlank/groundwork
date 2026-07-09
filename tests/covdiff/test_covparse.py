import json

import pytest

from groundwork.core.runner import ToolError
from groundwork.tools.covdiff.covparse import load_coverage, parse_coverage_obj


def test_parse_coverage_obj_relativizes_and_sets(tmp_path):
    root = tmp_path.resolve()
    obj = {"files": {
        (root / "mod.py").as_posix(): {"executed_lines": [1, 2, 4],
                                       "missing_lines": [5]},
    }}
    out = parse_coverage_obj(obj, root)
    assert out["mod.py"]["executed"] == {1, 2, 4}
    assert out["mod.py"]["missing"] == {5}


def test_load_coverage_from_file(tmp_path):
    root = tmp_path.resolve()
    p = tmp_path / "cov.json"
    p.write_text(json.dumps({"files": {
        "pkg/a.py": {"executed_lines": [1], "missing_lines": [2, 3]}}}),
        encoding="utf-8")
    out = load_coverage(p, root)
    assert out["pkg/a.py"]["missing"] == {2, 3}


def test_bad_coverage_json_raises(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("not json", encoding="utf-8")
    with pytest.raises(ToolError) as ei:
        load_coverage(p, tmp_path)
    assert ei.value.code == "BAD_COVERAGE" and ei.value.exit_code == 2


def test_missing_coverage_file_raises(tmp_path):
    with pytest.raises(ToolError) as ei:
        load_coverage(tmp_path / "nope.json", tmp_path)
    assert ei.value.code == "BAD_COVERAGE"
