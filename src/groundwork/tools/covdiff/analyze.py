"""Intersect changed lines with coverage: covered / uncovered / unmeasured."""


def analyze(diff_map: dict[str, set[int]], cov_map: dict[str, dict]) -> dict:
    """Per-file and overall changed-line coverage. Ratio counts only
    testable (covered+uncovered) changed lines; unmeasured is surfaced,
    never folded in; files coverage never saw are listed separately."""
    files, unmeasured_files = [], []
    total_cov = total_unc = 0
    for path in sorted(diff_map):
        changed = diff_map[path]
        if not changed:
            continue
        cov = cov_map.get(path)
        if cov is None:
            unmeasured_files.append({"file": path, "changed_lines": len(changed)})
            continue
        covered = sorted(changed & cov["executed"])
        uncovered = sorted(changed & cov["missing"])
        unmeasured = sorted(changed - cov["executed"] - cov["missing"])
        testable = len(covered) + len(uncovered)
        ratio = round(len(covered) / testable, 4) if testable else None
        files.append({"file": path, "changed": len(changed),
                      "covered": covered, "uncovered": uncovered,
                      "unmeasured": unmeasured, "ratio": ratio})
        total_cov += len(covered)
        total_unc += len(uncovered)
    total = total_cov + total_unc
    summary = {"covered": total_cov, "uncovered": total_unc,
               "ratio": round(total_cov / total, 4) if total else None}
    return {"files": files, "unmeasured_files": unmeasured_files,
            "summary": summary}
