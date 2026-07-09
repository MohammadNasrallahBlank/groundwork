import pytest

from groundwork.core.runner import ToolError
from groundwork.tools.ledger.store import add_claim, record_run, resolve_claim


def test_claim_and_resolve(tmp_path):
    c = add_claim(tmp_path, statement="tests will pass", confidence=0.9,
                  source="manual", tags=None, at="2026-06-01T00:00:00Z")
    assert c["id"] == 1 and c["confidence"] == 0.9 and c["resolved"] is False
    r = resolve_claim(tmp_path, 1, True, at="2026-06-01T01:00:00Z")
    assert r["resolved"] is True and r["outcome"] is True


def test_confidence_out_of_range_rejected(tmp_path):
    for bad in (-0.1, 1.5):
        with pytest.raises(ToolError) as ei:
            add_claim(tmp_path, statement="x", confidence=bad, source=None,
                      tags=None, at=None)
        assert ei.value.code == "USAGE"


def test_resolve_missing_claim(tmp_path):
    with pytest.raises(ToolError) as ei:
        resolve_claim(tmp_path, 99, True, at=None)
    assert ei.value.code == "NO_CLAIM" and ei.value.exit_code == 2


def test_double_resolve_rejected(tmp_path):
    add_claim(tmp_path, statement="x", confidence=0.5, source=None, tags=None,
              at="2026-06-01T00:00:00Z")
    resolve_claim(tmp_path, 1, True, at="2026-06-01T00:00:00Z")
    with pytest.raises(ToolError) as ei:
        resolve_claim(tmp_path, 1, False, at="2026-06-01T00:00:00Z")
    assert ei.value.code == "USAGE"


def test_record_run(tmp_path):
    out = record_run(tmp_path, tool="depsurface", cache="hit", avoided=True,
                     caught=False, at="2026-06-01T00:00:00Z")
    assert out["tool"] == "depsurface" and out["cache"] == "hit"
