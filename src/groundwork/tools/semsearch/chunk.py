"""Function/class/method chunks via cartographer's tree-sitter extraction.
Files with no extractable symbols get one whole-file chunk (capped)."""
from pathlib import Path
from typing import Iterator

from groundwork.tools.cartographer.extract import extract
from groundwork.tools.cartographer.languages import detect_language
from groundwork.tools.cartographer.mapper import _SKIP_DIRS

_WHOLE_FILE_LINE_CAP = 400


def _lines(text: str) -> list[str]:
    return text.splitlines()


def chunk_file(path: Path, root: Path) -> list[dict]:
    """Chunks for one file: top-level defs, or one whole-file chunk if none."""
    root = Path(root)
    rel = path.relative_to(root).as_posix()
    source = path.read_text(encoding="utf-8", errors="replace")
    lang = detect_language(path)
    chunks: list[dict] = []
    if lang is not None:
        syms, _refs = extract(path, source.encode("utf-8"), lang)
        lines = _lines(source)
        # top-level defs only (no dotted qualified_name) become chunks; their
        # text is the span from their line to the next top-level def / EOF.
        tops = sorted((s for s in syms if "." not in s.qualified_name),
                      key=lambda s: s.line)
        for i, s in enumerate(tops):
            start = s.line
            end = tops[i + 1].line - 1 if i + 1 < len(tops) else len(lines)
            body = "\n".join(lines[start - 1:end]).strip("\n")
            if body:
                chunks.append({"file": rel, "symbol": s.name, "kind": s.kind,
                               "start_line": start, "end_line": end, "text": body})
    if not chunks:
        lines = _lines(source)[:_WHOLE_FILE_LINE_CAP]
        body = "\n".join(lines).strip("\n")
        if body:
            chunks.append({"file": rel, "symbol": Path(rel).name,
                           "kind": "file", "start_line": 1,
                           "end_line": len(lines), "text": body})
    return chunks


def _skip(rel_parts) -> bool:
    return any(p in _SKIP_DIRS or p.startswith(".") for p in rel_parts[:-1])


def iter_chunks(root: Path) -> Iterator[dict]:
    """Walk the repo (cartographer skip rules) and yield chunks per file."""
    root = Path(root).resolve()
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        if _skip(p.relative_to(root).parts):
            continue
        # index source files AND common text docs; binary/unknown are skipped
        if detect_language(p) is None and p.suffix.lower() not in (
                ".md", ".txt", ".rst"):
            continue
        try:
            yield from chunk_file(p, root)
        except (OSError, ValueError):
            continue  # unreadable/unparseable: the indexer records nothing here
