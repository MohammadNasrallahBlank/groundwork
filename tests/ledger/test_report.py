from groundwork.tools.ledger.report import build_report
from groundwork.tools.ledger.store import add_claim, record_run, resolve_claim


def _seed_calibrated(root):
    data = [(0.9, True), (0.9, True), (0.9, True), (0.9, False),
            (0.2, False), (0.2, False)]
    for i, (conf, outcome) in enumerate(data, 1):
        add_claim(root, statement=f"c{i}", confidence=conf, source=None,
                  tags=None, at="2026-06-01T00:00:00Z")
        resolve_claim(root, i, outcome, at="2026-06-01T00:00:00Z")


def test_report_has_brier_and_calibration(tmp_path):
    _seed_calibrated(tmp_path)
    out = build_report(tmp_path, bins=5)
    assert out["calibration"]["brier"] is not None
    assert out["calibration"]["resolved"] == 6
    top = [b for b in out["calibration"]["buckets"]
           if b["range"] == [0.8, 1.0]][0]
    assert top["count"] == 4 and top["observed_rate"] == 0.75
    assert "brier" in out["methodology"].lower()
    assert out["dataset"]["resolved_claims"] == 6


def test_report_efficiency_counters(tmp_path):
    record_run(tmp_path, tool="a", cache="hit", avoided=True, caught=False,
               at="2026-06-01T00:00:00Z")
    record_run(tmp_path, tool="b", cache="miss", avoided=False, caught=True,
               at="2026-06-01T00:00:00Z")
    record_run(tmp_path, tool="c", cache="off", avoided=False, caught=False,
               at="2026-06-01T00:00:00Z")
    out = build_report(tmp_path, bins=5)
    eff = out["efficiency"]
    assert eff["runs"] == 3
    assert eff["cache_hits"] == 1 and eff["cache_hit_rate"] == 0.5  # off excluded
    assert eff["calls_avoided"] == 1 and eff["verification_catches"] == 1


def test_empty_ledger_is_honest(tmp_path):
    out = build_report(tmp_path, bins=5)
    assert out["calibration"]["brier"] is None
    assert out["calibration"]["resolved"] == 0
    assert out["efficiency"]["runs"] == 0
    assert out["efficiency"]["cache_hit_rate"] is None
