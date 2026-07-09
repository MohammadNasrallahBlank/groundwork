"""Walk a repo, extract each source file (cached by content hash), rank, render."""
from dataclasses import asdict
from pathlib import Path

from groundwork.core.cache import Cache, cache_key
from groundwork.tools.cartographer.extract import Reference, Symbol, extract
from groundwork.tools.cartographer.graph import rank_symbols
from groundwork.tools.cartographer.languages import detect_language
from groundwork.tools.cartographer.render import render_text

_TOOL = "cartographer"
_VERSION = "0.1.0"
_SKIP_DIRS = {".git", ".venv", "node_modules", "__pycache__", ".tmp",
              "dist", "build", ".mypy_cache", ".pytest_cache", ".groundwork"}


def _iter_source_files(root: Path):
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        if any(part in _SKIP_DIRS or part.startswith(".")
               for part in p.relative_to(root).parts[:-1]):
            continue
        if detect_language(p) is not None:
            yield p


def _extract_cached(path: Path, lang: str, cache: Cache | None):
    if cache is None:
        syms, refs = extract(path, path.read_bytes(), lang)
        return syms, refs, "off"
    key = cache_key(_TOOL, _VERSION, {"lang": lang, "path": path.as_posix()},
                    files=[path])
    hit = cache.get(key)
    if hit is not None:
        syms = [Symbol(**d) for d in hit["symbols"]]
        refs = [Reference(**d) for d in hit["refs"]]
        return syms, refs, "hit"
    syms, refs = extract(path, path.read_bytes(), lang)
    cache.put(key, {"symbols": [asdict(s) for s in syms],
                    "refs": [asdict(r) for r in refs]})
    return syms, refs, "miss"


def build_map(root: Path, budget: int, cache: Cache | None = None) -> dict:
    """Map the repo at ``root``: extract every source file (per-file cached),
    rank symbols by reference centrality, and render a budget-fitted map.

    Returns the render dict plus ``root`` (posix), ``files_scanned``,
    ``languages`` (sorted, only languages that yielded records), and
    ``_cache`` — ``"hit"``/``"miss"``/``"mixed"``/``"off"`` for the meta
    sentinel.
    """
    root = root.resolve()
    all_syms: list[Symbol] = []
    all_refs: list[Reference] = []
    langs: set[str] = set()
    states: set[str] = set()
    scanned = 0
    for path in _iter_source_files(root):
        lang = detect_language(path)
        syms, refs, state = _extract_cached(path, lang, cache)
        all_syms.extend(syms)
        all_refs.extend(refs)
        if syms or refs:
            langs.add(lang)
        states.add(state)
        scanned += 1
    ranked = rank_symbols(all_syms, all_refs)
    out = render_text(ranked, budget)
    cache_state = "off"
    if cache is not None:
        cache_state = ("hit" if states <= {"hit"} else
                       "miss" if states <= {"miss", "off"} else "mixed")
    out.update({"root": root.as_posix(), "files_scanned": scanned,
                "languages": sorted(langs), "_cache": cache_state})
    return out
