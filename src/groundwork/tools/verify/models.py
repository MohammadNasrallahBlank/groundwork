"""Normalized diagnostics: the one schema every adapter must emit."""
from dataclasses import asdict, dataclass

SEVERITIES = ("error", "warning", "info")


@dataclass(frozen=True)
class Diagnostic:
    source: str          # adapter name: pytest, ruff, junit, ...
    suite: str           # logical suite: unit, lint, ...
    file: str | None
    line: int | None
    col: int | None
    rule: str | None     # e.g. ruff code E501; None for test failures
    severity: str        # error | warning | info
    message: str
    duration_ms: int | None

    def to_dict(self) -> dict:
        return asdict(self)


def summarize(diags: list[Diagnostic]) -> dict:
    counts = {s: 0 for s in SEVERITIES}
    for d in diags:
        counts[d.severity] += 1
    return {"ok": counts["error"] == 0,
            "counts": counts,
            "sources": sorted({d.source for d in diags})}
