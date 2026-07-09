"""Assemble the honest calibration + proof-of-value report."""
from pathlib import Path

from groundwork.tools.ledger.metrics import brier_score, calibration_table
from groundwork.tools.ledger.store import open_store

_METHODOLOGY = (
    "Brier score = mean((confidence - outcome)^2) over resolved claims "
    "(outcome 1 if the claim came true, else 0); range [0,1], 0 is perfect, "
    "a constant 0.5 guess scores 0.25. Calibration buckets group claims by "
    "confidence band; observed_rate is the fraction that came true and gap = "
    "|mean_confidence - observed_rate| (0 is well-calibrated). cache_hit_rate "
    "= hits/(hits+misses), excluding uncacheable (cache=off) runs. "
    "calls_avoided and verification_catches are raw counts of flagged runs. "
    "All figures are local-only and reported with their sample size."
)


def build_report(root: Path, *, bins: int = 5) -> dict:
    conn = open_store(root)
    try:
        claims = conn.execute(
            "select confidence, outcome from claims where resolved=1").fetchall()
        pairs = [(c, o) for c, o in claims]
        open_count = conn.execute(
            "select count(*) from claims where resolved=0").fetchone()[0]
        runs = conn.execute(
            "select cache, avoided, caught from runs").fetchall()
    finally:
        conn.close()

    hits = sum(1 for cache, _a, _c in runs if cache == "hit")
    misses = sum(1 for cache, _a, _c in runs if cache == "miss")
    cacheable = hits + misses
    calibration = {
        "brier": brier_score(pairs),
        "brier_reference": {"perfect": 0.0, "uninformed_half": 0.25, "worst": 1.0},
        "resolved": len(pairs), "open": open_count,
        "buckets": calibration_table(pairs, bins=bins)}
    efficiency = {
        "runs": len(runs), "cache_hits": hits, "cache_misses": misses,
        "cache_hit_rate": round(hits / cacheable, 4) if cacheable else None,
        "calls_avoided": sum(1 for _c, a, _ca in runs if a),
        "verification_catches": sum(1 for _c, _a, ca in runs if ca)}
    dataset = {"resolved_claims": len(pairs), "open_claims": open_count,
               "runs": len(runs),
               "note": ("low sample size — interpret with caution"
                        if len(pairs) < 20 else "")}
    return {"calibration": calibration, "efficiency": efficiency,
            "methodology": _METHODOLOGY, "dataset": dataset}
