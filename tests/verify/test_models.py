from groundwork.tools.verify.models import Diagnostic, summarize


def diag(sev="error", src="pytest"):
    return Diagnostic(source=src, suite="unit", file="a.py", line=3, col=None,
                      rule=None, severity=sev, message="boom", duration_ms=12)


def test_diagnostic_serializes_to_plain_dict():
    d = diag().to_dict()
    assert d == {"source": "pytest", "suite": "unit", "file": "a.py", "line": 3,
                 "col": None, "rule": None, "severity": "error", "message": "boom",
                 "duration_ms": 12}


def test_summarize_counts_and_verdict():
    s = summarize([diag("error"), diag("warning", "ruff"), diag("warning", "ruff")])
    assert s["ok"] is False
    assert s["counts"] == {"error": 1, "warning": 2, "info": 0}
    assert sorted(s["sources"]) == ["pytest", "ruff"]


def test_summarize_ok_when_no_errors():
    assert summarize([diag("warning")])["ok"] is True
    assert summarize([])["ok"] is True
