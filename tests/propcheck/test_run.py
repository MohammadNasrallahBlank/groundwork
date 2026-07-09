import pytest

from groundwork.core.runner import ToolError
from groundwork.tools.propcheck.run import parse_counterexample, run_property_file


def test_parse_counterexample_single_arg():
    note = "Falsifying example: test_roundtrip(\n    x=0,\n)"
    assert parse_counterexample(note) == {"x": "0"}


def test_parse_counterexample_multi_arg():
    note = "Falsifying example: t(\n    x=5,\n    s='ab',\n)"
    assert parse_counterexample(note) == {"x": "5", "s": "'ab'"}


def _write(tmp_path, name, src):
    p = tmp_path / name
    p.write_text(src, encoding="utf-8", newline="\n")
    return p


def test_passing_property_reports_passed(tmp_path):
    p = _write(tmp_path, "prop_ok.py",
               "from hypothesis import given, settings, strategies as st\n"
               "@settings(derandomize=True)\n"
               "@given(x=st.integers())\n"
               "def test_abs_nonneg(x):\n"
               "    assert abs(x) >= 0\n")
    out = run_property_file(p)
    assert out["passed"] is True and out["checked"] == 1
    assert out["properties"][0]["passed"] is True


def test_failing_property_reports_counterexample(tmp_path):
    p = _write(tmp_path, "prop_bad.py",
               "from hypothesis import given, settings, strategies as st\n"
               "@settings(derandomize=True)\n"
               "@given(x=st.integers())\n"
               "def test_positive(x):\n"
               "    assert x > 0\n")
    out = run_property_file(p)
    assert out["passed"] is False and out["checked"] == 1
    prop = out["properties"][0]
    assert prop["passed"] is False and prop["counterexample"] is not None
    # the shrunk example for 'x > 0' is x=0
    assert prop["counterexample"]["x"] == "0"


def test_module_with_no_properties_is_checked_zero(tmp_path):
    p = _write(tmp_path, "prop_empty.py", "x = 1\n")
    out = run_property_file(p)
    assert out["checked"] == 0 and out["passed"] is True


def test_unimportable_property_file_raises(tmp_path):
    p = _write(tmp_path, "prop_broken.py", "import does_not_exist_xyz\n")
    with pytest.raises(ToolError) as ei:
        run_property_file(p)
    assert ei.value.code == "BAD_PROPERTY" and ei.value.exit_code == 1
