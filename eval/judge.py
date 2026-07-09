"""LLM-as-judge: score a task result 1-5 on the rubric using a headless Claude.

Calls `claude -p` (Claude Code in print mode) with a fixed judge model so the
scoring is consistent across all runs. The judge sees the task, Claude's final
answer, and the automated check verdict, and returns 1-5 scores. Keep the judge
MODEL fixed for a whole experiment and note it in the report.

Used automatically by grade.py --judge; can also be run standalone:
    uv run python eval/judge.py --task cartographer \
        --session <session.jsonl> --model claude-sonnet-5
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

from transcript import final_answer   # noqa: E402

DEFAULT_JUDGE_MODEL = "claude-sonnet-5"
DIMS = ("correctness", "completeness", "clarity")

_PROMPT = """\
You are grading how well an AI coding assistant completed a task. Be a STRICT, \
skeptical judge. A confident, elaborate, well-formatted answer that gets a \
FACT wrong must score LOW on correctness - do not be swayed by length or polish.

TASK GIVEN TO THE ASSISTANT:
{prompt}

GROUND TRUTH (the verified correct answer - grade against THIS, not vibes):
{ground_truth}

THE ASSISTANT'S FINAL ANSWER:
<<<
{answer}
>>>

An independent automated checker reported: {check}

Score 1-5, deducting hard for any factual error vs the ground truth:
- correctness: does it match the ground truth? Any wrong/invented fact (a wrong
  number, wrong row, wrong location) caps this at 3; multiple wrong facts -> 1-2.
- completeness: did it cover everything the task asked, no gaps?
- clarity: is it clear, well-organized, and easy to act on?

Reply with ONLY a JSON object, no prose, exactly:
{{"correctness": <1-5>, "completeness": <1-5>, "clarity": <1-5>, "reasoning": "<one sentence naming any factual error>"}}"""


def build_prompt(task: dict, answer: str, check: dict, ground_truth=None) -> str:
    check_s = (f"check {'PASSED' if check.get('pass') else 'FAILED'}, "
               f"accuracy {check.get('accuracy')}") if check else "n/a"
    ans = answer.strip() or "(the assistant produced no final text answer)"
    gt = ground_truth or task.get("ground_truth") or "(none provided)"
    return _PROMPT.format(prompt=task["prompt"], ground_truth=gt,
                          answer=ans[:6000], check=check_s)


def _call_claude(prompt: str, model: str) -> str:
    """Run headless Claude; return the assistant's text (unwrapped from JSON)."""
    try:
        p = subprocess.run(
            ["claude", "-p", prompt, "--output-format", "json", "--model", model],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=180)
    except (OSError, subprocess.TimeoutExpired) as e:
        raise RuntimeError(f"judge call failed: {e}") from e
    if p.returncode != 0:
        raise RuntimeError(f"claude -p exit {p.returncode}: {p.stderr.strip()[:300]}")
    try:
        return json.loads(p.stdout).get("result", p.stdout)
    except json.JSONDecodeError:
        return p.stdout


def _parse_scores(text: str) -> dict:
    matches = re.findall(r"\{[^{}]*correctness[^{}]*\}", text, re.S)
    if not matches:
        raise RuntimeError(f"no score JSON in judge reply: {text[:200]!r}")
    obj = json.loads(matches[-1])
    scores = {}
    for d in DIMS:
        v = obj.get(d)
        if not isinstance(v, (int, float)) or not 1 <= v <= 5:
            raise RuntimeError(f"judge gave invalid {d}: {v!r}")
        scores[d] = int(round(v))
    scores["reasoning"] = str(obj.get("reasoning", ""))[:300]
    return scores


def judge(task: dict, answer: str, check: dict, *, model=DEFAULT_JUDGE_MODEL) -> dict:
    scores = _parse_scores(_call_claude(build_prompt(task, answer, check), model))
    scores["judge_model"] = model
    return scores


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--task", required=True)
    ap.add_argument("--session", required=True, type=Path)
    ap.add_argument("--model", default=DEFAULT_JUDGE_MODEL)
    ns = ap.parse_args(argv)
    reg = json.loads((HERE / "tasks" / "registry.json").read_text(encoding="utf-8"))
    task = next((t for t in reg["tasks"] if t["id"] == ns.task), None)
    if task is None:
        ap.error(f"unknown task {ns.task}")
    ans = final_answer(ns.session)
    print(json.dumps(judge(task, ans, {}, model=ns.model), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
