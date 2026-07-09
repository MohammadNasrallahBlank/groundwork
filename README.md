# Groundwork

[![ci](https://github.com/MohammadNasrallahBlank/groundwork/actions/workflows/ci.yml/badge.svg)](https://github.com/MohammadNasrallahBlank/groundwork/actions/workflows/ci.yml)

> **A research project, not a product.** I built 23 local, deterministic tools to
> make Claude Code cheaper and more efficient — then ran a controlled experiment
> to find out whether they actually help. This repo is the tools, the
> measurement harness, and the honest answer.

**Short version: they mostly don't.** A frontier model with grep, code
execution, vision, and its own safety training is already a very strong,
very cheap baseline. Local tooling that duplicates any of that *adds* overhead
instead of removing it. The genuine value is narrow and specific. Every number
is below and in [`FINDINGS.md`](FINDINGS.md); the harness is in [`eval/`](eval/).

---

## The question

It's intuitive that handing mechanical work (searching, parsing, computing exact
statistics, rewriting code) to fast deterministic local tools should make an AI
agent **cheaper**, **faster**, and **more correct**. Groundwork is 23 such tools
wired into Claude Code as a skill + hooks.

The interesting question was never "can I build them." It was **"do they help?"** —
and, unusually, I built the instrument to answer it honestly instead of assuming.

## How I measured it

For every task I ran Claude Code **twice** — once with Groundwork installed and
enabled, once with it completely absent — same model (`claude-sonnet-5`), same
prompt, same fixture, fresh session each time. **46 headless sessions** in total
(23 tools × 2 conditions, one run per cell — so treat single deltas as
directional, not statistically tight).

Everything except quality is extracted **exactly** from the Claude Code session
transcript:

| Signal | Source |
| --- | --- |
| **Cost** | exact input/output/cache token counts per message, priced per model |
| **Speed** | wall-clock, API round-trips, tool-call counts from timestamps |
| **Tool usage** | which Groundwork tools the model *actually* invoked |
| **Quality** | an automated ground-truth check **plus** an LLM judge scored against a written ground truth (so it can't be fooled by a confident-but-wrong answer) |

The harness, the task fixtures, and the grader are all reproducible in
[`eval/`](eval/) — see [`eval/PROTOCOL.md`](eval/PROTOCOL.md).

## The result — every tool, measured

One row per tool. **Tokens** are billable tokens (the real cost driver,
excluding cheap cache reads); **time** is wall-clock; **correctness** is the
1–5 judge score. "Used" = did the model actually invoke the tool. One run per
cell, so read large single deltas as directional, not precise. **Δtok is blank
(—) when the model never invoked the tool** — that difference is run-to-run
variance, not the tool (explained below).

| tool | used | tokens w/o | tokens with | Δtok | time w/o | time with | correctness w/o→with |
| --- | --- | --- | --- | --- | --- | --- | --- |
| doc2md | yes | 116,642 | 88,789 | **−24%** | 0.32m | 0.38m | 5→5 |
| cartographer | yes | 74,524 | 132,746 | +78% | 0.82m | 0.71m | 3→3 |
| semsearch | no | 48,297 | 39,270 | — | 0.15m | 0.21m | 5→5 |
| codemod | yes | 822,377 | 114,386 | **−86%** | 1.65m | 1.18m | 5→5 |
| datalens | yes | 63,134 | 74,251 | +18% | 0.84m | 0.43m | 3→3 |
| verify | no | 77,647 | 82,973 | — | 0.35m | 0.31m | 5→5 |
| depsurface | no | 115,841 | 112,310 | — | 0.53m | 0.61m | **5→3** |
| gitwhy | yes | 44,284 | 59,663 | +35% | 0.30m | 0.27m | 5→5 |
| bisector | yes | 69,279 | 134,841 | +95% | 0.48m | 1.08m | **3→5** |
| covdiff | yes | 63,057 | 80,033 | +27% | 0.41m | 0.70m | 5→5 |
| propcheck | no | 47,246 | 41,657 | — | 0.27m | 0.23m | **5→3** |
| mutcheck | yes | 44,701 | 130,310 | +192% | 0.41m | 1.35m | 5→5 |
| patchgate | no | 10,254 | 32,401 | — | 0.07m | 0.20m | 5→5 |
| gates | no | 40,130 | 77,230 | — | 0.40m | 0.38m | 5→5 |
| snipeval | no | 42,596 | 38,606 | — | 0.18m | 0.21m | 5→5 |
| scratchdb | no | 51,572 | 65,395 | — | 0.18m | 0.46m | 3→4 |
| recordstore | yes | 61,701 | 72,547 | +18% | 0.73m | 0.48m | 5→5 |
| visdiff | no | 47,719 | 117,906 | — | 0.20m | 0.27m | 5→5 |
| ocr | yes | 31,050 | 71,080 | +129% | 0.13m | 0.41m | 5→5 |
| imgmeasure | yes | 47,337 | 71,218 | +50% | 0.35m | 2.40m | 5→5 |
| ledger | no | 22,924 | 21,250 | — | 0.24m | 0.12m | **4→1** |
| hello | yes | 120,006 | 76,852 | −36% | 0.71m | 0.19m | **5→3** |
| skillgen | no | 192,976 | 77,163 | — | 2.90m | 0.59m | **5→3** |

**Reading it honestly:**

- **Helped:** `doc2md` (−24% tokens), `bisector` (correctness **3→5**, paid for
  with +95% tokens), and `codemod` (a big token drop — though its without-run
  was a costly outlier, so treat with caution). A short list, and mostly a
  *correctness* win bought with tokens, not a cost win.
- **Hurt:** several tools *lowered* correctness when the model used or was pushed
  to use them — `depsurface`, `propcheck`, `hello`, `skillgen` (**5→3**) and
  `ledger` (**4→1**) — the model leaned on a terse tool result instead of
  reasoning it through.
- **Where a tool *was* used, tokens usually went up** (extra round-trips + the
  skill/hook overhead), and correctness was usually unchanged.
- **Where the tool was *not* used, the Δ is blanked (—) on purpose.** With one
  run per cell, that difference is dominated by Claude's own run-to-run
  randomness — several unused tools are actually *cheaper* with Groundwork, which
  only noise, not overhead, could produce — plus a small fixed cost from the
  plugin merely being loaded (its skill sits in context; the hooks fire). Those
  rows reflect Claude's variance and the plugin's presence, **not the tool.**

Sharpening the skill's "why use it / when NOT to" guidance did get the model to
reach for the tools more often — but as the table shows, using them more didn't
make outcomes better.

**The one tool with a real (modest) win — `doc2md`, on a 40-page PDF:**

| | Billable tokens | Cost |
| --- | --- | --- |
| Without (Claude reads the PDF) | 116,642 | $0.489 |
| With `doc2md` | **88,789 (−24%)** | $0.480 (flat) |

Smaller than hoped, because Claude Code already extracts *text* from text-PDFs
cheaply. The large win exists only for **scanned / image-only documents**, where
the model must pay vision-token prices — the genuinely promising, still-open lead.

## What I learned

1. **Claude + its native tools is already very good and cheap.** grep beats
   semantic search on most repos; the model runs the tests itself, reads images
   and HTML natively, and refuses risky actions on its own.
2. **Guardrail and vision tools were redundant** — the model self-refused unsafe
   actions and read receipts/charts/layouts directly.
3. **Clearer "why use it / when NOT to" guidance moves tool usage upward** — but
   forcing usage where the model's native approach is better *hurts* quality.
4. **The value is real but narrow:** compressing **expensive/binary inputs**
   (scanned documents) and a few **exact-computation** tasks the model
   otherwise approximates (git-bisect culprit, large-repo reference centrality,
   exact data statistics).

**Takeaway for anyone building agent tooling:** measure against the
*model-does-it-itself* baseline before assuming your tool helps. It's a far
stronger baseline than it feels like.

→ **Full methodology and every number: [`FINDINGS.md`](FINDINGS.md).**

## Reproduce it

```bash
uv sync
uv run python eval/selftest.py          # validate the harness
# then follow eval/PROTOCOL.md to run the with/without A/B yourself
```

## What's in this repo

| Path | What |
| --- | --- |
| [`eval/`](eval/) | the A/B measurement harness — transcript analyzer, checks, LLM judge, 23 task fixtures, protocol *(the interesting part)* |
| [`src/groundwork/tools/`](src/groundwork/tools/) | the 23 tools, each a JSON-contract CLI with a manifest, self-test, and cache |
| [`src/groundwork/core/`](src/groundwork/core/) | the envelope contract, runner, cache, manifest loader |
| [`FINDINGS.md`](FINDINGS.md) | the research writeup |
| `.github/workflows/ci.yml` | cross-platform CI (Linux/macOS/Windows) — which caught several real bugs |

## The tools that were built and tested

Each is a local CLI returning one JSON envelope (`{ok, data|error, meta}`) with
stable exit codes, wired into Claude Code as a skill + hooks.

`cartographer` (ranked repo map) · `semsearch` (semantic code search) ·
`codemod` (AST-safe rewrites) · `datalens` (exact data profiling) ·
`doc2md` (document→Markdown) · `ocr` (image→text) · `visdiff` (visual diff) ·
`imgmeasure` (pixel measurement) · `covdiff` (changed-line coverage) ·
`propcheck` (property testing) · `mutcheck` (mutation testing) ·
`gitwhy` (git archaeology) · `bisector` (regression bisect) ·
`depsurface` (API surface) · `snipeval` (snippet execution) ·
`scratchdb` (ad-hoc SQL) · `recordstore` (event log) ·
`patchgate` / `gates` (edit/command guardrails) · `verify` (test runner) ·
`ledger` (calibration) · `skillgen`, `hello` (infra).

The tools are genuinely usable — the CI is green on three OSes and each tool
self-tests — but per the findings above, install them as an experiment, not as
a promised efficiency win.

<details>
<summary>Install (if you want to try them)</summary>

```bash
uv tool install git+https://github.com/MohammadNasrallahBlank/groundwork
groundwork doctor            # all tools healthy
# in Claude Code:
#   /plugin marketplace add MohammadNasrallahBlank/groundwork
#   /plugin install groundwork@groundwork
```
</details>

## License

Released for study and reuse — the measurement harness in particular is meant to
be lifted and applied to *your* agent tooling. Attribution appreciated.
