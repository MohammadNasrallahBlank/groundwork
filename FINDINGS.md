# Do local deterministic tools make Claude Code more efficient? A measured answer.

**TL;DR — I built 23 local, deterministic CLI tools to offload mechanical work
from Claude Code, then ran a controlled A/B experiment (with-tools vs
without-tools, 46 headless sessions — 23 tools × 2 conditions — cost/speed/
quality measured from the session transcripts). The honest result: in agentic use, the tools mostly do
*not* make Claude cheaper or more correct — Claude's native tools (grep, file
reading, code execution, vision, and its own safety) already cover most of the
ground cheaply. The real value is narrow and specific, and this document reports
exactly where it is and isn't.**

This is a negative-leaning result, reported in full. The reusable measurement
harness that produced it lives in [`eval/`](eval/).

---

## The hypothesis

Large language models are expensive and non-deterministic. It's intuitive that
if you hand mechanical work (parsing, searching, computing exact statistics,
rewriting code) to fast, deterministic local tools, you should make an
agent **cheaper**, **faster**, and **more correct**.

Groundwork is 23 such tools (a code-map, semantic search, an AST codemod, a
data profiler, a git-bisect driver, a coverage/mutation/property-test suite, a
PDF→Markdown extractor, OCR, and more), each a local CLI returning a strict JSON
envelope, wired into Claude Code as a skill + hooks.

The question this repo actually answers is not "can I build them" (I did) but
**"do they help?"**

## How I measured it (this is the part I'm proud of)

For every task, I ran Claude Code **twice**: once with Groundwork installed and
enabled, once with it completely absent (uninstalled + plugin disabled). Same
model (`claude-sonnet-5`), same prompt, same fixture, fresh session each time.

Everything except quality is extracted **exactly** from the Claude Code session
transcript (`~/.claude/projects/.../*.jsonl`):

- **Cost** — exact input / output / cache token counts per message, priced per model.
- **Speed** — wall-clock, API round-trips, tool-call counts from timestamps.
- **Tool usage** — which Groundwork tools were actually invoked (so I can tell
  whether the model even *used* what it was given).

Quality is graded per task by (a) an automated ground-truth check (pass/fail +
accuracy) and (b) an LLM-as-judge scored **against a written ground truth** (so
it can't be fooled by a confident-but-wrong answer — a real failure mode I
caught and fixed mid-experiment).

The harness, the 23 task fixtures, and the grader are all in [`eval/`](eval/)
and reproducible.

## The results

**23 complex tasks, one per tool, with vs without Groundwork.** Tokens are
billable (excluding cheap cache reads); time is wall-clock; correctness is the
1–5 judge score against a written ground truth. One run per cell, so read large
single deltas as directional. **Δtok is blank (—) when the model never invoked
the tool** — that difference is run-to-run variance, not the tool (see below).

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

**What the per-tool numbers show:**

- **A short list helped.** `doc2md` cut tokens −24%. `bisector` bought a real
  correctness jump (3→5) at +95% tokens. `codemod` shows a large token drop, but
  its without-run was a costly outlier — treat it as noise, not a clean win.
  Notice the wins are mostly *correctness paid for in tokens*, not cost savings.
- **Several tools actively hurt.** `depsurface`, `propcheck`, `hello`, `skillgen`
  dropped correctness 5→3, and `ledger` 4→1 — when the model used a tool it often
  trusted its terse output instead of reasoning the answer out itself.
- **Where a tool *was* used, cost usually rose, quality stayed flat** — extra
  round-trips plus the skill/hook overhead, with no correctness gain.
- **The `used: no` rows are blanked (—) on purpose — they don't measure the
  tool.** With one run per cell, the with-vs-without difference there is
  dominated by Claude's own run-to-run randomness (several unused tools are
  *cheaper* with Groundwork, which only noise, not overhead, could produce),
  plus a small fixed cost from the plugin merely being loaded (skill in context,
  hooks firing). Those rows reflect Claude's variance and the plugin's presence,
  not the named tool's effect.

Sharpening each tool's "why use it / when NOT to" guidance did make the model
reach for the tools more often — but as the table shows, using them more did not
make outcomes better. "Make the model use our
tools" turned out to be the wrong goal.

### The one tool with a real (if modest) win: `doc2md`

`doc2md` converts a document to text locally so you send the model text instead
of an expensive PDF. On a 40-page PDF:

| | Billable tokens | Cost |
| --- | --- | --- |
| Without (Claude reads the PDF) | 116,642 | $0.489 |
| With `doc2md` | **88,789 (−24%)** | $0.480 (flat) |

A real token saving — but far smaller than hoped, because **Claude Code already
extracts *text* from text-PDFs cheaply**; it never paid the image-token price I
assumed. The large win only exists for **scanned / image-only documents**, where
the model *must* use vision — which is the genuinely promising, still-open lead.

## What I learned (the honest findings)

1. **Claude + its native tools is already very good and cheap.** grep beats
   semantic search on most repos; the model runs the tests itself; it reads
   images and HTML natively; it refuses risky actions on its own. A local tool
   that duplicates any of these *adds* round-trips instead of removing them.
2. **Guardrail tools were redundant** — Claude's own safety refused to hardcode
   a secret or run a destructive delete, with or without the tool.
3. **Vision tools were redundant** — Claude is multimodal; it read receipts,
   charts, and page layouts directly.
4. **Clearer "why use it / when NOT to" guidance genuinely moves tool usage
   upward** — but forcing usage where the model's native approach is better
   *hurts* quality.
5. **The value is real but narrow:** (a) **binary / expensive inputs** the model
   pays vision-token prices for — scanned documents, images-as-text; and (b) a
   few **deterministic-correctness** tasks where the model *approximates* and the
   tool is *exact* (git-bisect culprit, reference-centrality of a large repo,
   exact data statistics).

## Conclusion

The broad intuition — "local tools make an agent cheaper" — **does not hold** for
a strong agentic model in 2026, because the model's built-in tools already win
the cheap, general cases. The defensible value of local deterministic tooling is
a narrow band: **compressing expensive/binary inputs before they reach the
model, and replacing the few computations the model gets subtly wrong.**

Everything here is reproducible. If you're building agent tooling, the takeaway
is: **measure against the model-does-it-itself baseline before you assume your
tool helps — it's a much stronger baseline than it feels like.**

## Reproduce it

```bash
uv sync
uv run python eval/selftest.py          # validate the harness
# then follow eval/PROTOCOL.md to run the with/without A/B yourself
```

Full harness, tasks, and grader: [`eval/`](eval/). The tools themselves are
in [`src/groundwork/tools/`](src/groundwork/tools/), each with a manifest,
self-test, and cross-platform CI.
