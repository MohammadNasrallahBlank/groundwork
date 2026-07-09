import pytest

from groundwork.core.runner import ToolError
from groundwork.tools.datalens.compare import _psi, compare_datasets


def _csv(tmp_path, name, header, rows):
    p = tmp_path / name
    p.write_text(header + "\n" + "\n".join(rows) + "\n", encoding="utf-8")
    return p


def test_psi_zero_for_identical_distribution():
    assert _psi([0.25, 0.25, 0.25, 0.25], [0.25, 0.25, 0.25, 0.25]) == \
        pytest.approx(0.0, abs=1e-9)


def test_psi_positive_for_shifted_distribution():
    assert _psi([0.4, 0.3, 0.2, 0.1], [0.1, 0.2, 0.3, 0.4]) > 0.25


def test_numeric_drift_detected(tmp_path):
    a = _csv(tmp_path, "a.csv", "v", [str(i) for i in range(1, 21)])
    b = _csv(tmp_path, "b.csv", "v", [str(i) for i in range(81, 101)])
    out = compare_datasets(a, b)
    assert out["numeric_drift"]["v"]["psi"] > 0.25
    assert out["numeric_drift"]["v"]["reading"] == "significant"


def test_no_drift_for_same_data(tmp_path):
    a = _csv(tmp_path, "a.csv", "v", [str(i) for i in range(1, 21)])
    b = _csv(tmp_path, "b.csv", "v", [str(i) for i in range(1, 21)])
    out = compare_datasets(a, b)
    assert out["numeric_drift"]["v"]["psi"] < 0.1
    assert out["numeric_drift"]["v"]["reading"] == "stable"


def test_categorical_share_delta(tmp_path):
    a = _csv(tmp_path, "a.csv", "cat", ["x"] * 8 + ["y"] * 2)
    b = _csv(tmp_path, "b.csv", "cat", ["x"] * 2 + ["y"] * 8)
    out = compare_datasets(a, b)
    assert "cat" in out["categorical_drift"]


def test_disjoint_columns_escalate(tmp_path):
    a = _csv(tmp_path, "a.csv", "x", ["1", "2"])
    b = _csv(tmp_path, "b.csv", "y", ["1", "2"])
    with pytest.raises(ToolError) as ei:
        compare_datasets(a, b)
    assert ei.value.code == "NO_COMMON_COLUMNS" and ei.value.exit_code == 4
