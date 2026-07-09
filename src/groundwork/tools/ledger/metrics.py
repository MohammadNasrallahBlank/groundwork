"""Pure calibration statistics: Brier score and a reliability table."""


def brier_score(pairs: list[tuple[float, int]]) -> float | None:
    """mean((p - o)^2) over (confidence, outcome) pairs; None if empty."""
    if not pairs:
        return None
    return round(sum((p - o) ** 2 for p, o in pairs) / len(pairs), 6)


def _bucket_index(conf: float, bins: int) -> int:
    # [0,1] into `bins` equal bands; 1.0 lands in the top band (inclusive).
    idx = int(conf * bins)
    return min(idx, bins - 1)


def calibration_table(pairs: list[tuple[float, int]], bins: int = 5) -> list[dict]:
    """Per-bucket calibration; empty buckets are kept with count 0."""
    width = 1.0 / bins
    grouped: list[list[tuple[float, int]]] = [[] for _ in range(bins)]
    for conf, outcome in pairs:
        grouped[_bucket_index(conf, bins)].append((conf, outcome))
    table = []
    for i, group in enumerate(grouped):
        lo = round(i * width, 4)
        hi = round((i + 1) * width, 4)
        if not group:
            table.append({"range": [lo, hi], "count": 0,
                          "mean_confidence": None, "observed_rate": None,
                          "gap": None})
            continue
        mean_conf = sum(c for c, _ in group) / len(group)
        observed = sum(o for _, o in group) / len(group)
        table.append({"range": [lo, hi], "count": len(group),
                      "mean_confidence": round(mean_conf, 4),
                      "observed_rate": round(observed, 4),
                      "gap": round(abs(mean_conf - observed), 4)})
    return table
