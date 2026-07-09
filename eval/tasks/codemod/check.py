"""Ground-truth check for the codemod rename task.

Pass iff, across the workdir's Python files:
  * `calculate_total` is defined and used (the new name is present), AND
  * `compute_total` no longer appears as a Python identifier, AND
  * the README.md historical-note literal "compute_total" is preserved
    (renaming it would be an over-eager edit — a false positive).
accuracy = fraction of these three sub-conditions met.
"""
import re
from pathlib import Path


def check(*, answer: str, workdir: str, spec: dict) -> dict:
    wd = Path(workdir)
    py = list(wd.rglob("*.py"))
    code = "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in py)

    new_present = bool(re.search(r"\bcalculate_total\b", code))
    old_gone = re.search(r"\bcompute_total\b", code) is None
    readme = wd / "README.md"
    literal_kept = readme.is_file() and "compute_total" in readme.read_text(
        encoding="utf-8", errors="replace")

    conds = [new_present, old_gone, literal_kept]
    acc = round(sum(conds) / len(conds), 4)
    detail = (f"new_name_present={new_present} old_name_gone={old_gone} "
              f"readme_literal_kept={literal_kept}")
    return {"pass": all(conds), "accuracy": acc, "detail": detail}
