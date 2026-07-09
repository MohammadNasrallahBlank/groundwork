"""Validate the eval harness itself: every check type, the transcript
analyzer, and the grade->compare plumbing, against synthetic inputs. Run:

    uv run python eval/selftest.py     # -> "ALL OK" and exit 0
"""
import json
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

from analyze_session import analyze          # noqa: E402
from checks import run_check                 # noqa: E402
from transcript import final_answer          # noqa: E402
import compare                               # noqa: E402

FAILS = []


def ok(cond, msg):
    print(("  ok  " if cond else " FAIL ") + msg)
    if not cond:
        FAILS.append(msg)


def _fake_session(path: Path, answer: str):
    """A minimal but schema-faithful 2-message session."""
    lines = [
        {"type": "user", "timestamp": "2026-07-09T00:00:00.000Z",
         "message": {"role": "user", "content": "do the task"}},
        {"type": "assistant", "timestamp": "2026-07-09T00:03:20.000Z",
         "requestId": "req_1",
         "message": {"role": "assistant", "model": "claude-opus-4-8",
                     "usage": {"input_tokens": 1000, "output_tokens": 500,
                               "cache_read_input_tokens": 8000,
                               "cache_creation_input_tokens": 200},
                     "content": [
                         {"type": "tool_use", "name": "Bash",
                          "input": {"command": "groundwork cartographer map --root ."}},
                         {"type": "text", "text": answer}]}},
    ]
    path.write_text("\n".join(json.dumps(x) for x in lines), encoding="utf-8")


def test_checks():
    print("checks:")
    with tempfile.TemporaryDirectory() as td:
        wd = Path(td)
        (wd / "f.py").write_text("value = calculate_total(x)\n", encoding="utf-8")
        fx = wd / "fx"
        fx.mkdir()
        (fx / "keep.txt").write_text("original\n", encoding="utf-8")
        (wd / "keep.txt").write_text("original\n", encoding="utf-8")

        r = run_check({"type": "answer_contains", "expect": ["net.py", "retry_with_backoff"]},
                      answer="It's in net.py: retry_with_backoff", workdir=wd, fixture=fx)
        ok(r["pass"] and r["accuracy"] == 1.0, "answer_contains all present")
        r = run_check({"type": "answer_contains", "expect": ["a", "zzz"],
                       "pass_threshold": 1.0}, answer="only a", workdir=wd, fixture=fx)
        ok(not r["pass"] and r["accuracy"] == 0.5, "answer_contains partial -> fail, acc .5")
        # word-boundary: "20" must NOT match inside "2020"
        r = run_check({"type": "answer_contains", "expect": ["20"]},
                      answer="the year was 2020", workdir=wd, fixture=fx)
        ok(not r["pass"] and r["accuracy"] == 0.0, "word-boundary: 20 !~ 2020")
        r = run_check({"type": "answer_contains", "expect": ["20"]},
                      answer="there are 20 rows", workdir=wd, fixture=fx)
        ok(r["pass"], "word-boundary: 20 ~ '20 rows'")
        # forbidden wrong fact penalizes and fails
        r = run_check({"type": "answer_contains", "expect": ["amount"],
                       "forbid": ["21"]},
                      answer="amount has 21 distinct", workdir=wd, fixture=fx)
        ok(not r["pass"] and r["accuracy"] == 0.5, "forbid present -> fail, acc penalized")
        r = run_check({"type": "answer_not", "forbid": ["hallucinated"]},
                      answer="clean answer", workdir=wd, fixture=fx)
        ok(r["pass"], "answer_not clean")
        r = run_check({"type": "files_contain", "path": "f.py",
                       "expect": ["calculate_total"]}, answer="", workdir=wd, fixture=fx)
        ok(r["pass"], "files_contain hit")
        r = run_check({"type": "unchanged", "path": "keep.txt"},
                      answer="", workdir=wd, fixture=fx)
        ok(r["pass"], "unchanged -> pass when identical")
        (wd / "keep.txt").write_text("MODIFIED\n", encoding="utf-8")
        r = run_check({"type": "unchanged", "path": "keep.txt"},
                      answer="", workdir=wd, fixture=fx)
        ok(not r["pass"], "unchanged -> fail when modified")
        r = run_check({"type": "command_ok", "command": "python -c \"exit(0)\""},
                      answer="", workdir=wd, fixture=fx)
        ok(r["pass"], "command_ok exit 0")


def test_analyzer():
    print("analyzer:")
    with tempfile.TemporaryDirectory() as td:
        sess = Path(td) / "s.jsonl"
        _fake_session(sess, "Entry point is main in server.py")
        m = analyze(sess)
        ok(m["speed"]["wall_clock_s"] == 200.0, "wall clock = 200s")
        ok(m["speed"]["api_requests"] == 1, "1 api request")
        ok(m["cost"]["total_tokens"] == 9700, "total tokens 9700")
        ok(m["cost"]["estimated_usd"] > 0, "cost computed")
        ok(m["efficiency"]["groundwork_tool_invocations"] == 1
           and "cartographer" in m["efficiency"]["groundwork_tools_used"],
           "detected groundwork cartographer call")
        ok(final_answer(sess) == "Entry point is main in server.py", "final answer extracted")


def test_codemod_check():
    print("codemod check:")
    reg = json.loads((HERE / "tasks" / "registry.json").read_text(encoding="utf-8"))
    spec = next(t for t in reg["tasks"] if t["id"] == "codemod")["check"]
    fixture = HERE / "tasks" / "codemod" / "fixture"
    with tempfile.TemporaryDirectory() as td:
        wd = Path(td) / "wd"
        shutil.copytree(fixture, wd)
        # unmodified fixture still has compute_total -> must FAIL
        r = run_check(spec, answer="", workdir=wd, fixture=fixture)
        ok(not r["pass"], "codemod fails on un-renamed fixture")
        # apply a correct rename to the .py files, keep README literal
        for p in wd.rglob("*.py"):
            p.write_text(p.read_text(encoding="utf-8").replace(
                "compute_total", "calculate_total"), encoding="utf-8")
        r = run_check(spec, answer="", workdir=wd, fixture=fixture)
        ok(r["pass"] and r["accuracy"] == 1.0, "codemod passes on correct rename")


def test_verify_check():
    print("verify check:")
    fixture = HERE / "tasks" / "verify" / "fixture"
    spec = {"type": "command_ok", "command": "python -m pytest -q"}
    with tempfile.TemporaryDirectory() as td:
        wd = Path(td) / "wd"
        shutil.copytree(fixture, wd)
        r = run_check(spec, answer="", workdir=wd, fixture=fixture)
        ok(not r["pass"], "verify fails with the bug present")
        calc = wd / "calc.py"
        calc.write_text(calc.read_text(encoding="utf-8").replace(
            "return a - b            # BUG: should be a + b", "return a + b"),
            encoding="utf-8")
        r = run_check(spec, answer="", workdir=wd, fixture=fixture)
        ok(r["pass"], "verify passes after the fix")


def test_judge_parsing():
    print("judge parsing:")
    import judge as J
    txt = ('Here are my scores.\n'
           '{"correctness": 5, "completeness": 4, "clarity": 5, '
           '"reasoning": "correct and clear, minor gap"}')
    s = J._parse_scores(txt)
    ok(s["correctness"] == 5 and s["completeness"] == 4 and s["clarity"] == 5,
       "parses 1-5 scores from judge reply")
    ok("minor gap" in s["reasoning"], "captures reasoning")
    for bad in ['{"correctness": 9, "completeness": 4, "clarity": 5}',
                'no json here']:
        try:
            J._parse_scores(bad)
            ok(False, f"should reject: {bad[:30]}")
        except RuntimeError:
            ok(True, f"rejects invalid judge reply: {bad[:20]}")
    prompt = J.build_prompt({"prompt": "map the repo"}, "It's in server.py",
                            {"pass": True, "accuracy": 1.0})
    ok("map the repo" in prompt and "server.py" in prompt and "PASSED" in prompt,
       "judge prompt embeds task, answer, check")


def test_compare():
    print("compare:")
    runs = [
        {"task": "t", "condition": "without", "run": 1, "check": {"pass": True, "accuracy": 0.8},
         "rubric": {"correctness": 4}, "speed": {"wall_clock_min": 10.0, "api_requests": 20, "tool_calls": 15},
         "cost": {"total_tokens": 100000, "billable_tokens_excl_cache_read": 40000, "estimated_usd": 1.0},
         "efficiency": {"groundwork_tool_invocations": 0}},
        {"task": "t", "condition": "with", "run": 1, "check": {"pass": True, "accuracy": 1.0},
         "rubric": {"correctness": 5}, "speed": {"wall_clock_min": 6.0, "api_requests": 12, "tool_calls": 9},
         "cost": {"total_tokens": 60000, "billable_tokens_excl_cache_read": 25000, "estimated_usd": 0.6},
         "efficiency": {"groundwork_tool_invocations": 3}},
    ]
    rep = compare.build(runs)
    md = compare.render_md(rep)
    ok("Δ%" in md and "-40.0%" in md, "compare computes token delta -40%")
    ok(rep["overall"]["with"]["total_tokens"]["mean"] == 60000, "overall with-tokens mean")


def main():
    for t in (test_checks, test_analyzer, test_codemod_check, test_verify_check,
              test_judge_parsing, test_compare):
        t()
    print()
    if FAILS:
        print(f"{len(FAILS)} FAILURES")
        return 1
    print("ALL OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
