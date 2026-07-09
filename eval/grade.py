"""Grade one A/B run into a single record: transcript metrics + automated check
+ rubric (LLM-judged with --judge, or hand-scored with --correctness/...).

For the pilot layout you usually need only:

    uv run python eval/grade.py --task cartographer --condition without --run 1 --judge

which infers the workdir (eval/work/<task>-<condition>-<run>), finds that
workdir's newest Claude Code session, runs the check, and LLM-judges the rubric.
Override --workdir / --session / rubric flags as needed. Writes
eval/runs/<task>__<condition>__r<run>.json.
"""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

from analyze_session import analyze          # noqa: E402
from checks import run_check                 # noqa: E402
from latest_session import latest_session    # noqa: E402
from transcript import final_answer          # noqa: E402

RUBRIC_DIMS = ("correctness", "completeness", "clarity")


def load_registry() -> dict:
    reg = json.loads((HERE / "tasks" / "registry.json").read_text(encoding="utf-8"))
    return {t["id"]: t for t in reg["tasks"]}


def grade(task_id, condition, run, session, workdir, *, rubric=None,
          notes="", since=None, until=None,
          use_judge=False, judge_model=None) -> dict:
    tasks = load_registry()
    if task_id not in tasks:
        raise SystemExit(f"unknown task {task_id!r}; known: {sorted(tasks)}")
    task = tasks[task_id]
    fixture = HERE / "tasks" / task["fixture"] / "fixture"
    answer = final_answer(session, since=since, until=until)
    check = run_check(task["check"], answer=answer, workdir=Path(workdir),
                      fixture=fixture)
    metrics = analyze(Path(session), since=since, until=until,
                      label=f"{task_id}/{condition}/r{run}")

    rub = {d: (rubric or {}).get(d) for d in RUBRIC_DIMS}
    judge_info = None
    if use_judge and not any(rub.values()):
        from judge import DEFAULT_JUDGE_MODEL, judge as run_judge
        try:
            scored = run_judge(task, answer, check,
                               model=judge_model or DEFAULT_JUDGE_MODEL)
            for d in RUBRIC_DIMS:
                rub[d] = scored[d]
            judge_info = {"model": scored["judge_model"],
                          "reasoning": scored.get("reasoning", "")}
        except Exception as e:  # noqa: BLE001 — judging must never lose the run
            judge_info = {"error": str(e)}

    return {
        "task": task_id, "targets": task.get("targets", []),
        "condition": condition, "run": int(run),
        "session": str(session), "workdir": str(workdir),
        "check": check, "rubric": rub, "judge": judge_info, "notes": notes,
        "speed": metrics["speed"], "cost": metrics["cost"],
        "efficiency": metrics["efficiency"],
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--task", required=True)
    ap.add_argument("--condition", required=True, choices=["with", "without"])
    ap.add_argument("--run", required=True, type=int)
    ap.add_argument("--workdir", type=Path,
                    help="default eval/work/<task>-<condition>-<run>")
    ap.add_argument("--session", type=Path,
                    help="default = newest session for the workdir")
    ap.add_argument("--judge", action="store_true",
                    help="LLM-judge the 1-5 rubric via headless Claude")
    ap.add_argument("--judge-model")
    ap.add_argument("--since")
    ap.add_argument("--until")
    ap.add_argument("--notes", default="")
    for d in RUBRIC_DIMS:
        ap.add_argument(f"--{d}", type=int, choices=range(1, 6))
    ns = ap.parse_args(argv)

    workdir = ns.workdir or HERE / "work" / f"{ns.task}-{ns.condition}-{ns.run}"
    if not Path(workdir).is_dir():
        ap.error(f"workdir not found: {workdir} (run eval/pilot.py setup?)")
    session = ns.session or latest_session(workdir)
    if session is None or not Path(session).is_file():
        ap.error(f"no session transcript found for workdir {workdir}. "
                 "Did you run the task in Claude Code from that directory?")

    rubric = {d: getattr(ns, d) for d in RUBRIC_DIMS if getattr(ns, d) is not None}
    rec = grade(ns.task, ns.condition, ns.run, Path(session), workdir,
                rubric=rubric, notes=ns.notes, since=ns.since, until=ns.until,
                use_judge=ns.judge, judge_model=ns.judge_model)

    out_dir = HERE / "runs"
    out_dir.mkdir(exist_ok=True)
    out = out_dir / f"{ns.task}__{ns.condition}__r{ns.run}.json"
    out.write_text(json.dumps(rec, indent=2), encoding="utf-8", newline="\n")

    c, e = rec["check"], rec["efficiency"]
    rub = {k: v for k, v in rec["rubric"].items() if v is not None}
    jinfo = rec.get("judge") or {}
    jnote = f"  judge={jinfo['error']}" if jinfo.get("error") else ""
    print(f"{ns.task} [{ns.condition} r{ns.run}]  "
          f"check={'PASS' if c['pass'] else 'FAIL'} acc={c['accuracy']}  "
          f"rubric={rub or '(unscored)'}  "
          f"gw_tools={e['groundwork_tool_invocations']}  "
          f"tokens={rec['cost']['total_tokens']:,}  "
          f"wall={rec['speed']['wall_clock_min']}min{jnote}\n  -> {out.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
