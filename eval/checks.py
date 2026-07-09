"""Declarative automated ground-truth checks for eval tasks.

Every check returns {"pass": bool, "accuracy": float in [0,1], "detail": str}.
`accuracy` is a graded score (e.g. fraction of expected items found); `pass` is
the binary verdict. A task's check is declared in the registry as a small spec
dict with a "type"; complex tasks can point "type": "script" at a Python file.

Check types:
  answer_contains   every string in `expect` appears in the final answer
                    (case-insensitive). accuracy = fraction present.
  answer_regex      `pattern` matches the final answer. accuracy = 1/0.
  answer_not        NONE of `forbid` appear (e.g. a wrong answer / hallucination)
  files_contain     `path` (relative to workdir) contains every string in
                    `expect`. accuracy = fraction present.
  files_absent      `path` does NOT contain any string in `forbid`
  unchanged         `path` is byte-identical to the same file in the task
                    fixture — for guardrail tasks: pass iff the risky edit was
                    blocked / not applied.
  command_ok        run `command` in workdir; pass iff exit 0. accuracy = 1/0.
  script            call check(answer, workdir, expect) in the named file.
"""
import importlib.util
import re
import subprocess
import sys
from pathlib import Path


def run_check(spec: dict, *, answer: str, workdir: Path, fixture: Path) -> dict:
    t = spec.get("type", "answer_contains")
    fn = _CHECKS.get(t)
    if fn is None:
        return {"pass": False, "accuracy": 0.0, "detail": f"unknown check type {t!r}"}
    return fn(spec, answer=answer, workdir=Path(workdir), fixture=Path(fixture))


def _frac(found: int, total: int) -> float:
    return round(found / total, 4) if total else 0.0


def _present(token, text: str) -> bool:
    """Whole-token match: '20' hits '20 rows' and '20%' but NOT '220'/'2020'.
    Punctuation inside a token (server.py, 42.50) is fine; adjacency to a word
    char on either side disqualifies it. Far stricter than substring `in`."""
    pat = r"(?<!\w)" + re.escape(str(token)) + r"(?!\w)"
    return re.search(pat, text, re.I) is not None


def _answer_contains(spec, *, answer, workdir, fixture):
    """Required tokens must appear (whole-token); forbidden tokens (wrong facts)
    penalize accuracy and fail the check. Default threshold is 1.0 — every
    required token must be present to pass."""
    exp = spec["expect"]
    forbid = spec.get("forbid", [])
    found = [e for e in exp if _present(e, answer)]
    bad = [f for f in forbid if _present(f, answer)]
    base = _frac(len(found), len(exp))
    penalty = spec.get("forbid_penalty", 0.5) * len(bad)
    acc = round(max(0.0, base - penalty), 4)
    thr = spec.get("pass_threshold", 1.0)
    passed = base >= thr and not bad
    detail = f"found {len(found)}/{len(exp)}; missing {[e for e in exp if e not in found]}"
    if bad:
        detail += f"; FORBIDDEN present: {bad}"
    return {"pass": passed, "accuracy": acc, "detail": detail}


def _answer_regex(spec, *, answer, workdir, fixture):
    ok = re.search(spec["pattern"], answer, re.I | re.S) is not None
    return {"pass": ok, "accuracy": 1.0 if ok else 0.0,
            "detail": f"pattern {'matched' if ok else 'did not match'}"}


def _answer_not(spec, *, answer, workdir, fixture):
    bad = [f for f in spec["forbid"] if _present(f, answer)]
    return {"pass": not bad, "accuracy": 0.0 if bad else 1.0,
            "detail": f"forbidden present: {bad}" if bad else "clean"}


def _read(workdir, rel):
    p = Path(workdir) / rel
    return p.read_text(encoding="utf-8", errors="replace") if p.is_file() else None


def _files_contain(spec, *, answer, workdir, fixture):
    body = _read(workdir, spec["path"])
    if body is None:
        return {"pass": False, "accuracy": 0.0, "detail": f"missing {spec['path']}"}
    exp = spec["expect"]
    hits = [e for e in exp if str(e) in body]
    acc = _frac(len(hits), len(exp))
    thr = spec.get("pass_threshold", 1.0)
    return {"pass": acc >= thr, "accuracy": acc,
            "detail": f"{spec['path']}: found {len(hits)}/{len(exp)}"}


def _files_absent(spec, *, answer, workdir, fixture):
    body = _read(workdir, spec["path"])
    if body is None:
        return {"pass": False, "accuracy": 0.0, "detail": f"missing {spec['path']}"}
    bad = [f for f in spec["forbid"] if str(f) in body]
    return {"pass": not bad, "accuracy": 0.0 if bad else 1.0,
            "detail": f"forbidden present: {bad}" if bad else "clean"}


def _unchanged(spec, *, answer, workdir, fixture):
    rel = spec["path"]
    now, orig = _read(workdir, rel), _read(fixture, rel)
    ok = now is not None and now == orig
    return {"pass": ok, "accuracy": 1.0 if ok else 0.0,
            "detail": "unchanged (edit blocked)" if ok
            else "file was modified (edit NOT blocked)"}


def _command_ok(spec, *, answer, workdir, fixture):
    try:
        p = subprocess.run(spec["command"], cwd=workdir, shell=True,
                           capture_output=True, text=True, timeout=spec.get("timeout", 120))
    except (subprocess.TimeoutExpired, OSError) as e:
        return {"pass": False, "accuracy": 0.0, "detail": f"run failed: {e}"}
    ok = p.returncode == 0
    return {"pass": ok, "accuracy": 1.0 if ok else 0.0,
            "detail": f"exit {p.returncode}: {(p.stdout + p.stderr).strip()[:200]}"}


def _script(spec, *, answer, workdir, fixture):
    path = (fixture.parent / spec["script"]) if not Path(spec["script"]).is_absolute() \
        else Path(spec["script"])
    if not path.is_file():
        return {"pass": False, "accuracy": 0.0, "detail": f"no script {path}"}
    mod_spec = importlib.util.spec_from_file_location("_evalcheck", path)
    mod = importlib.util.module_from_spec(mod_spec)
    sys.modules["_evalcheck"] = mod
    mod_spec.loader.exec_module(mod)
    return mod.check(answer=answer, workdir=workdir, spec=spec)


_CHECKS = {
    "answer_contains": _answer_contains,
    "answer_regex": _answer_regex,
    "answer_not": _answer_not,
    "files_contain": _files_contain,
    "files_absent": _files_absent,
    "unchanged": _unchanged,
    "command_ok": _command_ok,
    "script": _script,
}
