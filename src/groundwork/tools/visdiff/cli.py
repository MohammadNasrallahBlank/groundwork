import argparse
import re
import subprocess
import sys
from pathlib import Path

from groundwork.core.cliparse import UsageParser
from groundwork.core.runner import ToolError, run_tool
from groundwork.tools.visdiff import store
from groundwork.tools.visdiff.checker import approve, run_check, set_baseline

TOOL, VERSION = "visdiff", "0.1.0"
_NAME_RE = re.compile(r"^[A-Za-z0-9._-]{1,64}$")


def _viewport(spec: str) -> tuple[int, int]:
    m = re.fullmatch(r"(\d{2,5})x(\d{2,5})", spec)
    if not m:
        raise ToolError("USAGE", f"--viewport must look like 1280x720, got {spec!r}",
                        exit_code=2)
    return int(m.group(1)), int(m.group(2))


def _checked_name(name: str) -> str:
    if not _NAME_RE.fullmatch(name):
        raise ToolError("BAD_NAME",
                        f"invalid baseline name {name!r} (must match {_NAME_RE.pattern})",
                        exit_code=2)
    return name


def _add_capture_args(sp) -> None:
    sp.add_argument("--name", required=True)
    sp.add_argument("--url", required=True)
    sp.add_argument("--root", default=".")
    sp.add_argument("--viewport", default="1280x720")
    sp.add_argument("--full-page", action="store_true")
    sp.add_argument("--mask", action="append", default=[])
    sp.add_argument("--timeout", type=int, default=30)


def handler(args: list[str]) -> dict:
    p = UsageParser(prog=f"groundwork {TOOL}", exit_on_error=False)
    sub = p.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("baseline")
    _add_capture_args(b)
    c = sub.add_parser("check")
    _add_capture_args(c)
    c.add_argument("--min-ssim", type=float, default=0.995)
    c.add_argument("--max-diff-ratio", type=float, default=0.001)
    a = sub.add_parser("approve")
    a.add_argument("--name", required=True)
    a.add_argument("--root", default=".")
    sub.add_parser("list")
    sub.add_parser("install-browser")
    sub.add_parser("self-test")
    try:
        ns = p.parse_args(args)
    except argparse.ArgumentError as e:
        raise ToolError("USAGE", str(e), exit_code=2) from e

    if ns.cmd == "self-test":
        return _self_test()
    if ns.cmd == "list":
        return {"baselines": store.list_baselines(),
                "platform_key": store.platform_key()}
    if ns.cmd == "install-browser":
        return _install_browser()

    name = _checked_name(ns.name)
    root = Path(ns.root).resolve()
    if not root.is_dir():
        raise ToolError("NO_ROOT", f"not a directory: {root.as_posix()}", exit_code=2)
    if ns.cmd == "approve":
        return approve(name, root)
    vw = _viewport(ns.viewport)
    if ns.cmd == "baseline":
        return set_baseline(name, ns.url, root, viewport=vw, full_page=ns.full_page,
                            masks=tuple(ns.mask), timeout_s=ns.timeout)
    return run_check(name, ns.url, root, viewport=vw, full_page=ns.full_page,
                     masks=tuple(ns.mask), timeout_s=ns.timeout,
                     min_ssim=ns.min_ssim, max_diff_ratio=ns.max_diff_ratio)


def _self_test() -> dict:
    """Browser-free: exercise the diff engine on synthesized images."""
    import io

    from PIL import Image

    from groundwork.tools.visdiff.diffengine import diff_images

    def png(rgb):
        img = Image.new("RGB", (32, 32), rgb)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    same = diff_images(png((10, 10, 10)), png((10, 10, 10)))
    changed = diff_images(png((10, 10, 10)), png((200, 200, 200)))
    if same["pixel_diff_count"] != 0 or changed["pixel_diff_count"] == 0:
        raise ToolError("SELF_TEST", "diff engine produced inconsistent results")
    return {"self_test": "pass"}


def _install_browser() -> dict:
    """Explicit, user-invoked browser download - the no-silent-downloads gate."""
    proc = subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"],
                          capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=900)
    if proc.returncode != 0:
        raise ToolError("INSTALL_FAILED",
                        "playwright install chromium failed",
                        detail=proc.stderr[-2000:])
    from groundwork.tools.visdiff.capture import browser_available
    if not browser_available():
        raise ToolError("INSTALL_FAILED",
                        "install reported success but chromium is still unavailable")
    return {"installed": "chromium"}


def main(args: list[str]) -> None:
    run_tool(TOOL, VERSION, handler, args)
