from groundwork.tools.covdiff.analyze import analyze


def test_uncovered_changed_lines_flagged():
    diff = {"mod.py": {2, 4, 5}}          # changed lines
    cov = {"mod.py": {"executed": {1, 2, 4}, "missing": {5}}}
    out = analyze(diff, cov)
    f = out["files"][0]
    assert f["covered"] == [2, 4] and f["uncovered"] == [5]
    assert f["ratio"] == round(2 / 3, 4)  # 2 covered of 3 testable-changed
    assert out["summary"]["ratio"] == round(2 / 3, 4)


def test_non_executable_changed_lines_are_unmeasured():
    diff = {"mod.py": {2, 3}}             # line 3 is a blank the coverage ignores
    cov = {"mod.py": {"executed": {2}, "missing": set()}}
    out = analyze(diff, cov)
    f = out["files"][0]
    assert f["covered"] == [2] and f["uncovered"] == [] and f["unmeasured"] == [3]
    assert f["ratio"] == 1.0


def test_file_coverage_did_not_measure_is_listed_separately():
    diff = {"new.py": {1, 2, 3}}
    cov = {}                              # coverage never saw new.py
    out = analyze(diff, cov)
    assert out["files"] == []
    assert out["unmeasured_files"] == [{"file": "new.py", "changed_lines": 3}]
    assert out["summary"]["ratio"] is None


def test_file_with_no_testable_changed_lines_has_null_ratio():
    diff = {"mod.py": {3}}               # only a blank line changed
    cov = {"mod.py": {"executed": {1}, "missing": {2}}}
    out = analyze(diff, cov)
    assert out["files"][0]["ratio"] is None


def test_summary_aggregates_across_files():
    diff = {"a.py": {1, 2}, "b.py": {1}}
    cov = {"a.py": {"executed": {1}, "missing": {2}},
           "b.py": {"executed": set(), "missing": {1}}}
    out = analyze(diff, cov)
    assert out["summary"] == {"covered": 1, "uncovered": 2, "ratio": round(1 / 3, 4)}


def test_empty_diff_is_null_summary():
    out = analyze({}, {})
    assert out["files"] == [] and out["summary"]["ratio"] is None
