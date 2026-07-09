# eval/ — Groundwork A/B measurement harness

Measures Claude Code doing real tasks **with** vs **without** Groundwork, across
all 23 tools. Speed, cost, and efficiency are extracted exactly from the session
transcript; quality is graded (automated check + 1–5 rubric).

**To run the experiment, follow [`PROTOCOL.md`](PROTOCOL.md).**

## Pieces

| file | what it does |
| --- | --- |
| `tasks/registry.json` | the 23-task suite: prompt, target tool, automated check, rubric |
| `tasks/<id>/fixture/` | files a task runs against (copied into a fresh workdir per run) |
| `analyze_session.py` | transcript → exact speed/cost/efficiency metrics |
| `checks.py` | declarative ground-truth check library |
| `grade.py` | one run → a graded record in `runs/` (metrics + check + rubric) |
| `compare.py` | all `runs/` → `REPORT.md` (with-vs-without, per task + overall) |
| `latest_session.py` | find the transcript for a workdir |
| `pricing.json` | per-model $/token (edit to your rates; token counts are exact) |
| `selftest.py` | validates the harness itself — `uv run python eval/selftest.py` |

## Quick sanity check (no Claude Code needed)

```bash
uv run python eval/selftest.py                       # -> ALL OK
uv run python eval/analyze_session.py <any-session.jsonl>   # see the metrics
```

## Metrics at a glance

- **Speed** — wall clock, API requests, tool calls (transcript timestamps).
- **Cost** — exact input/output/cache token counts × `pricing.json`.
- **Efficiency** — tool-call counts, and detection of which `groundwork` tools
  were actually invoked (scans Bash commands).
- **Quality** — automated `check_pass`/`check_accuracy` + `rubric_mean` (1–5).
