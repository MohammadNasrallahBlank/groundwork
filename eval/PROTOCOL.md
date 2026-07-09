# A/B Test Protocol — Groundwork vs. no Groundwork

The goal: measure **speed, cost, efficiency, and quality** of Claude Code doing
real tasks **with** Groundwork available vs. **without** it, across all 23 tools.

The **published run used one run per cell** — `23 tools × 2 conditions × 1 run =
46 sessions` — so single-cell deltas are directional, not statistically tight.
For tighter numbers, bump to 3 runs each (`23 × 2 × 3 = 138 sessions`) and the
harness will average them; the steps below are written to scale to any run count.

Everything except *quality* is extracted automatically from the session
transcript. Quality is graded per task: an automated ground-truth **check**
(pass/fail + accuracy) plus a 1–5 **rubric** you (or an LLM judge) score.

---

## One-time setup

The **grader** runs in this repo's environment (it needs `uv` + this repo). The
**sessions** you run by hand in Claude Code, in throwaway workdirs.

```bash
# from the groundwork repo:
uv sync                      # grader deps
mkdir -p eval/work eval/runs
```

---

## Design rules (read once — they keep the comparison fair)

1. **Same model in both arms.** Pick one model and use it for every session.
   Cost depends on it; note it in `eval/pricing.json`.
2. **Control = Groundwork genuinely absent**, not "present but don't use it."
   Run the whole `without` phase with the plugin disabled and `groundwork` off
   your `PATH`; run the whole `with` phase after installing it. Batch by
   condition so you toggle once, not 66 times.
3. **One task per session.** Open Claude Code fresh in the task's workdir, paste
   exactly the task prompt (verbatim, from `eval/tasks/registry.json`), let it
   finish, end the session. Don't coach mid-task — you're testing the model, not
   yourself.
4. **Identical prompts and fixtures** across both arms. The workdir is a fresh
   copy of the fixture each run.
5. **Guardrail tasks** (`patchgate`, `gates`) measure *prevention*: the "good"
   outcome is the risky edit/command being **blocked**. The prompt deliberately
   asks for something unsafe.

---

## Phase A — control (`without` Groundwork)

Disable Groundwork: `/plugin` → disable `groundwork`, and ensure `groundwork`
is not on `PATH` (`uv tool uninstall groundwork` if you installed it). Then for
each task and each run `1..3`:

```bash
# 1. fresh workdir from the fixture
task=cartographer; cond=without; run=1
rm -rf "eval/work/$task-$cond-$run"
cp -r "eval/tasks/$task/fixture" "eval/work/$task-$cond-$run"

# 2. run the task IN Claude Code, in that workdir:
#    - cd eval/work/$task-$cond-$run  and start claude there
#    - paste the task's "prompt" from eval/tasks/registry.json
#    - let it finish; end the session

# 3. grade it (grader auto-finds the session for that workdir)
sess=$(uv run python eval/latest_session.py "eval/work/$task-$cond-$run")
uv run python eval/grade.py --task $task --condition $cond --run $run \
    --session "$sess" --workdir "eval/work/$task-$cond-$run" \
    --correctness 4 --completeness 4 --clarity 5     # your 1–5 scores
```

Repeat for every task in `registry.json`, runs 1–3.

## Phase B — treatment (`with` Groundwork)

Install and enable Groundwork (see the repo README *Install* section):

```bash
uv tool install git+https://github.com/MohammadNasrallahBlank/groundwork
# in Claude Code:  /plugin marketplace add MohammadNasrallahBlank/groundwork
#                  /plugin install groundwork@groundwork
```

Then repeat the per-task loop with `cond=with`. The grader will confirm the
`with` arm actually used the tools (`groundwork_invocations > 0`); if it's 0,
the model ignored Groundwork — note it, that's a real finding about discoverability.

---

## Rubric (score each run 1–5)

| dim | 1 | 5 |
| --- | --- | --- |
| correctness | wrong | fully correct |
| completeness | partial | covers everything asked |
| clarity | confusing | clear, well-organized, actionable |

Pass them to `grade.py` via `--correctness/--completeness/--clarity`, or edit the
`rubric` block in `eval/runs/<task>__<cond>__r<run>.json` afterward. Leaving them
blank is fine — `compare.py` reports what it has.

> Prefer an LLM judge? Feed the task prompt + Claude's final answer + the rubric
> to a *separate* Claude session and record its 1–5 scores the same way. Keep the
> judge model fixed and note it.

---

## Produce the report

```bash
uv run python eval/compare.py --out eval/REPORT.md
```

You get per-task and overall tables: `without` vs `with` means over the 3 runs,
Δ% deltas, ✅/⚠️ direction markers. Token counts are exact; dollar figures use
`eval/pricing.json` (edit to your real rates first).

---

## What's measured

| metric | source | direction |
| --- | --- | --- |
| wall_clock_min, api_requests, tool_calls | transcript timestamps & tool_use | lower better |
| total_tokens, billable_tokens, estimated_usd | transcript `usage` × pricing | lower better |
| check_pass, check_accuracy | automated ground-truth | higher better |
| rubric_mean | your / judge 1–5 | higher better |
| groundwork_invocations | `groundwork <tool>` in Bash calls | sanity (should be >0 only in `with`) |

## Fixture status

Batch 1 fixtures are ready to run now: **cartographer, semsearch, codemod,
datalens, verify**. The remaining tasks in `registry.json` have their prompts,
checks, and rubrics specified but their `fixture/` still to be built
(`fixture_ready: false`) — those are the next increment.
