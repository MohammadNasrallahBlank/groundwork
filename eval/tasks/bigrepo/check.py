"""Check for the codemod-on-bigrepo task: rename `require` -> `ensure`.

`require` is defined in utils/validation.py and called by every domain model.
Pass iff, across the workdir's Python files: `ensure` is now defined and used,
and `require` no longer appears as a Python identifier anywhere.
accuracy = fraction of (new-defined, new-used-widely, old-gone) met.
"""
import re
from pathlib import Path


def check(*, answer: str, workdir: str, spec: dict) -> dict:
    wd = Path(workdir)
    files = list(wd.rglob("*.py"))
    joined = "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in files)

    defines_ensure = bool(re.search(r"\bdef ensure\b", joined))
    old_gone = re.search(r"\brequire\b", joined) is None
    # used widely: ensure() called in several model files
    uses = len([p for p in files if p.name == "model.py"
                and re.search(r"\bensure\(", p.read_text(encoding='utf-8', errors='replace'))])
    used_widely = uses >= 10

    conds = [defines_ensure, old_gone, used_widely]
    acc = round(sum(conds) / len(conds), 4)
    return {"pass": all(conds), "accuracy": acc,
            "detail": f"def_ensure={defines_ensure} old_require_gone={old_gone} "
                      f"model_call_sites={uses}"}
