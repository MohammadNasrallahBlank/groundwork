"""Extract objective A/B metrics from a Claude Code session transcript.

A Claude Code session is a JSONL file under
``~/.claude/projects/<slug>/<session-id>.jsonl``. Every assistant message
carries exact token usage and a model tag; every message carries a timestamp;
every tool call is a ``tool_use`` block. That is enough to measure speed, cost,
and efficiency *exactly* — the only metric not in the transcript is quality,
which is graded separately.

Usage:
    python eval/analyze_session.py <session.jsonl> [--label NAME] [--json]
    python eval/analyze_session.py <session.jsonl> --since 2026-07-08T05:00:00Z

Segmenting: pass --since / --until (ISO-8601) to isolate one task's window when
a session holds more than one. The clean protocol is one task per session, in
which case no window is needed and the whole file is the task.
"""
import argparse
import json
import re
from collections import Counter
from pathlib import Path

# The 22 Groundwork tools — used to detect deterministic tool usage inside
# Bash/PowerShell commands (`groundwork <tool> ...`) and skill/plugin attribution.
GROUNDWORK_TOOLS = {
    "cartographer", "visdiff", "ocr", "imgmeasure", "codemod", "patchgate",
    "gates", "semsearch", "datalens", "scratchdb", "recordstore", "covdiff",
    "propcheck", "mutcheck", "gitwhy", "bisector", "ledger", "hello", "verify",
    "depsurface", "snipeval", "skillgen", "doc2md",
}
_GW_RE = re.compile(r"\bgroundwork\s+([a-z0-9]+)\b")
_TOKEN_FIELDS = ("input_tokens", "output_tokens",
                 "cache_read_input_tokens", "cache_creation_input_tokens")


def _load_pricing() -> dict:
    p = Path(__file__).with_name("pricing.json")
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def _cost(model: str, tok: dict, pricing: dict) -> float:
    rate = pricing.get(model) or pricing.get("_default") or {}
    return round(
        tok["input_tokens"] / 1e6 * rate.get("input", 0)
        + tok["output_tokens"] / 1e6 * rate.get("output", 0)
        + tok["cache_read_input_tokens"] / 1e6 * rate.get("cache_read", 0)
        + tok["cache_creation_input_tokens"] / 1e6 * rate.get("cache_write", 0),
        6)


def _iter_records(path: Path, since: str | None, until: str | None):
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                o = json.loads(line)
            except json.JSONDecodeError:
                continue
            ts = o.get("timestamp")
            if since and ts and ts < since:
                continue
            if until and ts and ts > until:
                continue
            yield o


def analyze(path: Path, *, since=None, until=None, label=None) -> dict:
    pricing = _load_pricing()
    timestamps: list[str] = []
    per_model_tokens: dict[str, Counter] = {}
    assistant_msgs = 0
    request_ids: set[str] = set()
    human_prompts = 0
    tool_calls: Counter = Counter()
    gw_invocations: Counter = Counter()
    gw_via_attribution = 0
    api_errors = 0
    tool_errors = 0

    for o in _iter_records(path, since, until):
        ts = o.get("timestamp")
        if ts:
            timestamps.append(ts)
        typ = o.get("type")
        if o.get("isApiErrorMessage"):
            api_errors += 1
        if str(o.get("attributionPlugin") or "").startswith("groundwork") or \
                str(o.get("attributionSkill") or "").startswith("groundwork"):
            gw_via_attribution += 1
        msg = o.get("message")
        if not isinstance(msg, dict):
            continue
        if typ == "user":
            content = msg.get("content")
            is_tool_result = isinstance(content, list) and any(
                isinstance(c, dict) and c.get("type") == "tool_result"
                for c in content)
            if not is_tool_result and not o.get("isMeta"):
                human_prompts += 1
        if typ == "assistant":
            assistant_msgs += 1
            if o.get("requestId"):
                request_ids.add(o["requestId"])
            model = msg.get("model", "unknown")
            usage = msg.get("usage") or {}
            bucket = per_model_tokens.setdefault(model, Counter())
            for f in _TOKEN_FIELDS:
                bucket[f] += int(usage.get(f, 0) or 0)
            content = msg.get("content")
            if isinstance(content, list):
                for c in content:
                    if isinstance(c, dict) and c.get("type") == "tool_use":
                        name = c.get("name", "?")
                        tool_calls[name] += 1
                        _scan_groundwork(name, c.get("input") or {}, gw_invocations)
        if o.get("toolUseResult"):
            r = o["toolUseResult"]
            if isinstance(r, dict) and (r.get("is_error") or r.get("error")):
                tool_errors += 1

    timestamps.sort()
    wall = _seconds(timestamps[0], timestamps[-1]) if len(timestamps) >= 2 else 0.0
    totals = Counter()
    cost = 0.0
    per_model_out = {}
    for model, tok in per_model_tokens.items():
        for f in _TOKEN_FIELDS:
            totals[f] += tok[f]
        c = _cost(model, tok, pricing)
        cost += c
        per_model_out[model] = {**{f: tok[f] for f in _TOKEN_FIELDS},
                                "cost_usd": c}
    total_tokens = sum(totals[f] for f in _TOKEN_FIELDS)
    billed = totals["input_tokens"] + totals["output_tokens"] \
        + totals["cache_creation_input_tokens"]

    return {
        "label": label or path.stem,
        "window": {"since": since, "until": until,
                   "first": timestamps[0] if timestamps else None,
                   "last": timestamps[-1] if timestamps else None},
        "speed": {
            "wall_clock_s": round(wall, 1),
            "wall_clock_min": round(wall / 60, 2),
            "human_prompts": human_prompts,
            "assistant_messages": assistant_msgs,
            "api_requests": len(request_ids),
            "tool_calls": sum(tool_calls.values()),
        },
        "cost": {
            "total_tokens": total_tokens,
            "billable_tokens_excl_cache_read": billed,
            **{f: totals[f] for f in _TOKEN_FIELDS},
            "cache_read_ratio": round(
                totals["cache_read_input_tokens"] / total_tokens, 4)
            if total_tokens else 0.0,
            "estimated_usd": round(cost, 4),
            "per_model": per_model_out,
        },
        "efficiency": {
            "tool_calls_total": sum(tool_calls.values()),
            "tool_calls_by_name": dict(tool_calls.most_common()),
            "groundwork_tool_invocations": sum(gw_invocations.values()),
            "groundwork_tools_used": dict(gw_invocations.most_common()),
            "distinct_groundwork_tools": len(gw_invocations),
            "groundwork_attributed_messages": gw_via_attribution,
            "tokens_per_tool_call": round(
                total_tokens / sum(tool_calls.values()), 1)
            if tool_calls else None,
            "api_errors": api_errors,
            "tool_errors": tool_errors,
        },
    }


def _scan_groundwork(tool_name: str, tool_input: dict, counter: Counter) -> None:
    """Detect `groundwork <tool>` invoked through a Bash/PowerShell command."""
    if tool_name not in ("Bash", "PowerShell"):
        return
    cmd = str(tool_input.get("command", ""))
    for m in _GW_RE.finditer(cmd):
        sub = m.group(1)
        if sub in GROUNDWORK_TOOLS:
            counter[sub] += 1


def _seconds(a: str, b: str) -> float:
    import datetime

    def _p(s: str) -> datetime.datetime:
        return datetime.datetime.fromisoformat(s.replace("Z", "+00:00"))
    return (_p(b) - _p(a)).total_seconds()


def _render(m: dict) -> str:
    s, c, e = m["speed"], m["cost"], m["efficiency"]
    lines = [
        f"# Session metrics: {m['label']}",
        "",
        "## Speed",
        f"- wall clock: {s['wall_clock_min']} min ({s['wall_clock_s']} s)",
        f"- human prompts: {s['human_prompts']}  |  assistant messages: "
        f"{s['assistant_messages']}  |  API requests: {s['api_requests']}",
        f"- tool calls: {s['tool_calls']}",
        "",
        "## Cost",
        f"- total tokens: {c['total_tokens']:,}  "
        f"(billable excl. cache-read: {c['billable_tokens_excl_cache_read']:,})",
        f"- input {c['input_tokens']:,} | output {c['output_tokens']:,} | "
        f"cache-read {c['cache_read_input_tokens']:,} | "
        f"cache-write {c['cache_creation_input_tokens']:,}",
        f"- cache-read ratio: {c['cache_read_ratio']}",
        f"- estimated cost: ${c['estimated_usd']}  "
        "(token counts exact; $ from eval/pricing.json — edit to your rates)",
        "",
        "## Efficiency",
        f"- groundwork tool invocations: {e['groundwork_tool_invocations']} "
        f"across {e['distinct_groundwork_tools']} distinct tools",
        f"- groundwork tools used: {e['groundwork_tools_used'] or '(none)'}",
        f"- tokens per tool call: {e['tokens_per_tool_call']}",
        f"- API errors: {e['api_errors']}  |  tool errors: {e['tool_errors']}",
        f"- all tool calls: {e['tool_calls_by_name']}",
    ]
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("session", type=Path)
    ap.add_argument("--since")
    ap.add_argument("--until")
    ap.add_argument("--label")
    ap.add_argument("--json", action="store_true", help="emit JSON, not text")
    ns = ap.parse_args(argv)
    if not ns.session.is_file():
        ap.error(f"no such session file: {ns.session}")
    m = analyze(ns.session, since=ns.since, until=ns.until, label=ns.label)
    print(json.dumps(m, indent=2) if ns.json else _render(m))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
