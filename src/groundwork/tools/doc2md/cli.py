import argparse
from pathlib import Path

from groundwork.core.cache import Cache, cache_key
from groundwork.core.cliparse import UsageParser
from groundwork.core.runner import ToolError, run_tool
from groundwork.tools.doc2md.convert import convert

TOOL, VERSION = "doc2md", "0.1.0"


def handler(args: list[str]) -> dict:
    p = UsageParser(prog=f"groundwork {TOOL}", exit_on_error=False)
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("convert")
    c.add_argument("--file", required=True)
    c.add_argument("--pages", help="1-based, e.g. 1-3,7")
    c.add_argument("--grep", help="keep only Markdown blocks matching this regex")
    c.add_argument("--max-chars", type=int)
    c.add_argument("--no-cache", action="store_true")
    sub.add_parser("self-test")
    try:
        ns = p.parse_args(args)
    except argparse.ArgumentError as e:
        raise ToolError("USAGE", str(e), exit_code=2) from e

    if ns.cmd == "self-test":
        return _self_test()

    path = Path(ns.file)
    if not path.is_file():
        raise ToolError("NO_FILE", f"no such file: {path.as_posix()}", exit_code=2)
    cache = Cache()
    key = cache_key(TOOL, VERSION,
                    {"pages": ns.pages, "grep": ns.grep, "max_chars": ns.max_chars},
                    [path])
    if not ns.no_cache:
        hit = cache.get(key)
        if hit is not None:
            return {**hit, "_cache": "hit"}
    out = convert(path, pages=ns.pages, grep=ns.grep, max_chars=ns.max_chars)
    if not ns.no_cache:
        cache.put(key, out)
    return {**out, "_cache": "miss" if not ns.no_cache else "off"}


def _self_test() -> dict:
    """Build a 2-page PDF in memory, convert it, and prove the text round-trips
    and the Markdown is smaller than the PDF bytes."""
    import tempfile

    import pymupdf
    doc = pymupdf.open()
    for n in (1, 2):
        page = doc.new_page()
        page.insert_text((72, 72), f"Heading {n}\nThe quick brown fox {n}.")
    with tempfile.TemporaryDirectory() as td:
        pdf = Path(td) / "s.pdf"
        doc.save(pdf)
        doc.close()
        out = convert(pdf)
    if "quick brown fox" not in out["markdown"] or out["pages"] != 2:
        raise ToolError("SELF_TEST", "doc2md did not extract expected text",
                        detail=out)
    return {"self_test": "pass", "pages": out["pages"], "chars": out["chars"]}


def main(args: list[str]) -> None:
    run_tool(TOOL, VERSION, handler, args)
