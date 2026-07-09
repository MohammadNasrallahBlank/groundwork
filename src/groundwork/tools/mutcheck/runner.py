"""Apply each mutant to the file, run the tests, classify, always restore."""
from pathlib import Path
from typing import Callable

from groundwork.tools.mutcheck.mutate import iter_mutants


def check_file(file: Path, changed_lines: set[int],
               run_tests: Callable[[], bool], *, max_mutants: int = 25) -> dict:
    """Test each mutant of `file`; the original bytes are ALWAYS restored."""
    file = Path(file)
    source = file.read_text(encoding="utf-8")
    original_bytes = file.read_bytes()
    mutants = iter_mutants(source, changed_lines)
    total = len(mutants)
    to_run = mutants[:max_mutants]
    killed = survived = invalid = 0
    survivors = []
    try:
        for m in to_run:
            file.write_text(m.source, encoding="utf-8", newline="\n")
            try:
                passed = run_tests()
            finally:
                file.write_bytes(original_bytes)   # restore after every mutant
            if passed is None:
                invalid += 1
            elif passed:
                survived += 1
                survivors.append({"line": m.line, "mutation": m.description})
            else:
                killed += 1
    finally:
        file.write_bytes(original_bytes)            # belt-and-braces restore
    return {"file": file.resolve().as_posix(), "mutants_total": total,
            "tested": len(to_run), "killed": killed, "survived": survived,
            "invalid": invalid,
            "survivors": sorted(survivors, key=lambda s: (s["line"], s["mutation"])),
            "budget_hit": total > max_mutants}
