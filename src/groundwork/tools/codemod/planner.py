"""Compute a change plan; never touch tracked files. Plans live under
<root>/.groundwork/codemod/plans/<plan_id>.json with full new content."""
import difflib
import hashlib
import json
from pathlib import Path

from groundwork.core.atomicjson import write_atomic
from groundwork.core.runner import ToolError
from groundwork.tools.codemod import presets as presets_mod
from groundwork.tools.codemod.astgrep import LANG_GLOBS, rewrite_source
from groundwork.tools.codemod.combyengine import rewrite_source as comby_rewrite

_SKIP_DIRS = {".git", ".venv", "node_modules", "__pycache__", ".tmp",
              "dist", "build", ".mypy_cache", ".pytest_cache", ".groundwork"}
_ENVELOPE_DIFF_LINES = 40


def _iter_files(root: Path, glob: str):
    for p in sorted(root.glob(glob)):
        if not p.is_file():
            continue
        rel = p.relative_to(root)
        if any(part in _SKIP_DIRS or part.startswith(".")
               for part in rel.parts[:-1]):
            continue
        yield p


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _run_engine(source: str, *, engine: str, pattern, rewrite, lang, preset,
                suffix: str):
    if engine == "ast-grep":
        return rewrite_source(source, lang, pattern, rewrite)
    if engine == "preset":
        return presets_mod.run_preset(source, preset)
    return comby_rewrite(source, pattern, rewrite, suffix)


def build_plan(root: Path, *, engine: str, pattern, rewrite, lang, preset,
               glob) -> dict:
    """Walk, transform, diff. Writes only the plan record; returns envelope data."""
    root = Path(root).resolve()
    if glob is None:
        glob = LANG_GLOBS[lang] if engine == "ast-grep" else "**/*.py"
    scanned = 0
    files = []
    errors = []
    total_matches = 0 if engine == "ast-grep" else None
    for p in _iter_files(root, glob):
        scanned += 1
        # open(), not Path.read_text(): read_text gained newline= only in 3.13
        with open(p, encoding="utf-8", newline="") as fh:
            source = fh.read()
        try:
            new, count = _run_engine(source, engine=engine, pattern=pattern,
                                     rewrite=rewrite, lang=lang, preset=preset,
                                     suffix=p.suffix)
        except ValueError as e:
            errors.append({"file": p.relative_to(root).as_posix(), "error": str(e)})
            continue
        if count is not None:
            total_matches += count
        if new == source:
            continue
        rel = p.relative_to(root).as_posix()
        diff = "".join(difflib.unified_diff(
            source.splitlines(keepends=True), new.splitlines(keepends=True),
            fromfile=f"a/{rel}", tofile=f"b/{rel}", n=3))
        files.append({"file": rel, "matches": count, "old_sha256": _sha(source),
                      "diff": diff, "new_content": new})

    key_src = json.dumps({"engine": engine, "pattern": pattern,
                          "rewrite": rewrite, "preset": preset, "lang": lang,
                          "hashes": [(f["file"], f["old_sha256"]) for f in files]},
                         sort_keys=True)
    plan_id = hashlib.sha256(key_src.encode("utf-8")).hexdigest()[:12]
    plan = {"plan_id": plan_id, "engine": engine, "pattern": pattern,
            "rewrite": rewrite, "preset": preset, "lang": lang, "glob": glob,
            "root": root.as_posix(), "files": files, "errors": errors}
    plans_dir = root / ".groundwork" / "codemod" / "plans"
    plans_dir.mkdir(parents=True, exist_ok=True)
    plan_path = plans_dir / f"{plan_id}.json"
    write_atomic(plan_path, json.dumps(plan))

    def _clip(diff: str) -> str:
        lines = diff.splitlines(keepends=True)
        if len(lines) <= _ENVELOPE_DIFF_LINES:
            return diff
        kept = "".join(lines[:_ENVELOPE_DIFF_LINES])
        return kept + (f"... [{len(lines) - _ENVELOPE_DIFF_LINES} more diff "
                       f"lines in {plan_path.name}]\n")

    return {"plan_id": plan_id, "engine": engine, "pattern": pattern,
            "preset": preset, "root": root.as_posix(), "files_scanned": scanned,
            "files_changed": len(files), "total_matches": total_matches,
            "changes": [{"file": f["file"], "matches": f["matches"],
                         "diff": _clip(f["diff"])} for f in files],
            "errors": errors, "plan_path": plan_path.as_posix()}


def load_plan(root: Path, plan_id: str) -> dict:
    """Load a stored plan record; NO_PLAN (exit 2) when absent."""
    p = Path(root).resolve() / ".groundwork" / "codemod" / "plans" / f"{plan_id}.json"
    if not p.is_file():
        raise ToolError("NO_PLAN", f"no stored plan {plan_id!r} at {p.as_posix()}",
                        exit_code=2)
    return json.loads(p.read_text(encoding="utf-8"))
