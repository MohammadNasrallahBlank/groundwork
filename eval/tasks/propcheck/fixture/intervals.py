def merge_intervals(intervals):
    """Merge overlapping [start, end] intervals. Has a subtle bug: it only
    merges when the next start is strictly LESS than the current end, so
    intervals that merely touch (next start == current end) are not merged."""
    if not intervals:
        return []
    xs = sorted(intervals)
    merged = [list(xs[0])]
    for s, e in xs[1:]:
        if s < merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], e)
        else:
            merged.append([s, e])
    return [tuple(m) for m in merged]
