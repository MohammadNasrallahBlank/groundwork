"""Aggregate all graded runs in eval/runs/ into a with-vs-without comparison.

Reads every eval/runs/*.json, groups by (task, condition), averages across the
repeated runs, and reports per-task and overall deltas for speed, cost,
efficiency, and quality. Emits Markdown (default) or JSON.

    python eval/compare.py                 # Markdown report to stdout
    python eval/compare.py --json          # machine-readable
    python eval/compare.py --out eval/REPORT.md
"""
import argparse
import json
import statistics as st
from collections import defaultdict
from pathlib import Path

EVAL = Path(__file__).parent
RUBRIC_DIMS = ("correctness", "completeness", "clarity")


def _load_runs() -> list[dict]:
    d = EVAL / "runs"
    return [json.loads(p.read_text(encoding="utf-8"))
            for p in sorted(d.glob("*.json"))] if d.is_dir() else []


def _mean(xs):
    xs = [x for x in xs if x is not None]
    return round(st.mean(xs), 4) if xs else None


def _stdev(xs):
    xs = [x for x in xs if x is not None]
    return round(st.pstdev(xs), 4) if len(xs) > 1 else 0.0


def _metrics_of(run: dict) -> dict:
    """Pull the scalar metrics we compare from one run record."""
    s, c, e = run["speed"], run["cost"], run["efficiency"]
    rub = run.get("rubric") or {}
    rub_scores = [rub.get(d) for d in RUBRIC_DIMS if rub.get(d) is not None]
    return {
        "wall_clock_min": s["wall_clock_min"],
        "api_requests": s["api_requests"],
        "tool_calls": s["tool_calls"],
        "total_tokens": c["total_tokens"],
        "billable_tokens": c["billable_tokens_excl_cache_read"],
        "estimated_usd": c["estimated_usd"],
        "groundwork_invocations": e["groundwork_tool_invocations"],
        "check_pass": 1.0 if run["check"]["pass"] else 0.0,
        "check_accuracy": run["check"]["accuracy"],
        "rubric_mean": round(st.mean(rub_scores), 3) if rub_scores else None,
    }


_METRIC_KEYS = ("wall_clock_min", "api_requests", "tool_calls", "total_tokens",
                "billable_tokens", "estimated_usd", "groundwork_invocations",
                "check_pass", "check_accuracy", "rubric_mean")
# For these, LOWER is better (speed/cost/effort); a negative with-minus-without
# delta is an improvement. The rest (quality) are higher-is-better.
_LOWER_BETTER = {"wall_clock_min", "api_requests", "tool_calls", "total_tokens",
                 "billable_tokens", "estimated_usd"}


def _agg(runs: list[dict]) -> dict:
    per = [_metrics_of(r) for r in runs]
    out = {}
    for k in _METRIC_KEYS:
        vals = [p[k] for p in per]
        out[k] = {"mean": _mean(vals), "stdev": _stdev(vals),
                  "n": len([v for v in vals if v is not None])}
    return out


def _pct(with_v, without_v) -> str:
    if with_v is None or without_v is None or without_v == 0:
        return "n/a"
    return f"{(with_v - without_v) / abs(without_v) * 100:+.1f}%"


def build(runs: list[dict]) -> dict:
    by_task = defaultdict(lambda: defaultdict(list))
    for r in runs:
        by_task[r["task"]][r["condition"]].append(r)
    tasks = {}
    for task, conds in sorted(by_task.items()):
        tasks[task] = {c: _agg(rs) for c, rs in conds.items()}
    overall = defaultdict(lambda: defaultdict(list))
    for r in runs:
        overall[r["condition"]]  # touch
    overall_agg = {c: _agg([r for r in runs if r["condition"] == c])
                   for c in ("with", "without") if any(r["condition"] == c for r in runs)}
    return {"tasks": tasks, "overall": overall_agg,
            "n_runs": len(runs),
            "n_tasks": len(by_task)}


def _delta_row(name, agg, indent="") -> list[str]:
    w = agg.get("with", {})
    wo = agg.get("without", {})
    rows = []
    for k in _METRIC_KEYS:
        wv = (w.get(k) or {}).get("mean")
        wov = (wo.get(k) or {}).get("mean")
        if wv is None and wov is None:
            continue
        arrow = ""
        if wv is not None and wov is not None:
            better = (wv < wov) if k in _LOWER_BETTER else (wv > wov)
            worse = (wv > wov) if k in _LOWER_BETTER else (wv < wov)
            arrow = " ✅" if better and wv != wov else (" ⚠️" if worse else "")
        rows.append(f"| {indent}{k} | {wov} | {wv} | {_pct(wv, wov)}{arrow} |")
    return rows


def render_md(report: dict) -> str:
    out = [
        "# Groundwork A/B — with vs without",
        "",
        f"_{report['n_runs']} graded runs across {report['n_tasks']} tasks. "
        "Columns: **without** (control) and **with** (Groundwork) are means over "
        "repeated runs; **Δ%** is with-vs-without. ✅ = Groundwork better, "
        "⚠️ = worse. Lower is better for speed/cost/effort; higher for quality._",
        "",
        "## Overall",
        "",
        "| metric | without | with | Δ% |",
        "| --- | --- | --- | --- |",
    ]
    out += _delta_row("overall", report["overall"])
    out += ["", "## Per task", ""]
    for task, agg in report["tasks"].items():
        out.append(f"### {task}")
        out.append("")
        out.append("| metric | without | with | Δ% |")
        out.append("| --- | --- | --- | --- |")
        out += _delta_row(task, agg)
        out.append("")
    out += [
        "## Reading this",
        "",
        "- **total_tokens / estimated_usd** — cost. Token counts are exact; $ "
        "uses `eval/pricing.json` (edit to your rates).",
        "- **wall_clock_min / api_requests / tool_calls** — speed & effort.",
        "- **check_pass / check_accuracy** — automated correctness (0–1).",
        "- **rubric_mean** — human/LLM 1–5 quality (blank until scored).",
        "- **groundwork_invocations** — sanity check that the *with* arm "
        "actually used the tools (should be >0 with, 0 without).",
    ]
    return "\n".join(out)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--out", type=Path)
    ns = ap.parse_args(argv)
    runs = _load_runs()
    if not runs:
        print("no graded runs in eval/runs/ yet — run eval/grade.py first.")
        return 0
    report = build(runs)
    text = json.dumps(report, indent=2) if ns.json else render_md(report)
    if ns.out:
        ns.out.write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote {ns.out}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
