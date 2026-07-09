"""Local document -> Markdown extraction. The point is token economy: a PDF
read directly becomes page-images (expensive); its text as Markdown is a
fraction of that. We do the extraction on the local machine and hand back only
the text, with a size report so the saving is visible."""
import contextlib
import os
import re
import sys
from pathlib import Path

from groundwork.core.runner import ToolError


@contextlib.contextmanager
def _quiet_stdout():
    """Silence pymupdf's C-level chatter (e.g. 'Using RapidOCR...') so it can't
    leak onto the tool's stdout and corrupt the one-JSON-object contract."""
    sys.stdout.flush()
    fd = sys.stdout.fileno()
    saved = os.dup(fd)
    devnull = os.open(os.devnull, os.O_WRONLY)
    try:
        os.dup2(devnull, fd)
        yield
    finally:
        sys.stdout.flush()
        os.dup2(saved, fd)
        os.close(devnull)
        os.close(saved)

_MD_FORMATS = {".pdf", ".xps", ".epub", ".mobi", ".fb2", ".cbz", ".svg"}
_TEXT_FORMATS = {".txt", ".md", ".markdown"}


def _parse_pages(spec: str, total: int) -> list[int]:
    out: list[int] = []
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-", 1)
            out.extend(range(int(a) - 1, int(b)))     # 1-based inclusive -> 0-based
        elif part:
            out.append(int(part) - 1)
    bad = [p + 1 for p in out if not 0 <= p < total]
    if bad:
        raise ToolError("USAGE", f"pages out of range 1..{total}: {bad}", exit_code=2)
    return out


def convert(path: Path, *, pages: str | None = None, grep: str | None = None,
            max_chars: int | None = None) -> dict:
    p = Path(path)
    if not p.is_file():
        raise ToolError("NO_FILE", f"no such file: {p.as_posix()}", exit_code=2)
    ext = p.suffix.lower()
    source_bytes = p.stat().st_size
    page_count = None

    if ext in _TEXT_FORMATS:
        md = p.read_text(encoding="utf-8", errors="replace")
    elif ext in _MD_FORMATS:
        import pymupdf
        with _quiet_stdout():
            doc = pymupdf.open(p)
            page_count = doc.page_count
            page_list = (_parse_pages(pages, page_count) if pages
                         else range(page_count))
            parts = []
            for i in page_list:
                # native text layer: complete and reliable (pymupdf4llm's
                # layout/OCR pass silently drops body text on some PDFs).
                txt = doc[i].get_text("text").strip()
                if txt:
                    parts.append(txt)
            doc.close()
        md = "\n\n".join(parts)
    else:
        raise ToolError("UNSUPPORTED",
                        f"cannot convert {ext!r}; supported: "
                        f"{sorted(_MD_FORMATS | _TEXT_FORMATS)}", exit_code=2)

    if grep:
        md = _grep_sections(md, grep)
    truncated = False
    if max_chars and len(md) > max_chars:
        md, truncated = md[:max_chars], True

    chars = len(md)
    return {
        "format": ext.lstrip("."),
        "pages": page_count,
        "markdown": md,
        "chars": chars,
        "est_tokens": chars // 4,
        "source_bytes": source_bytes,
        "truncated": truncated,
        "note": ("Markdown text handed back locally; reading the raw document "
                 "directly would typically cost several times more tokens "
                 "(pages become images)."),
    }


def _grep_sections(md: str, pattern: str) -> str:
    """Keep only the Markdown blocks (paragraphs / sections) that match, so the
    model receives just the relevant slice of a large document."""
    rx = re.compile(pattern, re.I)
    blocks = re.split(r"\n\s*\n", md)
    keep = [b for b in blocks if rx.search(b)]
    return "\n\n".join(keep) if keep else ""
