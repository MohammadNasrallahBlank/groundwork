"""Deterministic Playwright capture. The ONLY module that touches the browser."""
from pathlib import Path

from groundwork.core.runner import ToolError

_LAUNCH_ARGS = ["--force-color-profile=srgb"]


def browser_available() -> bool:
    """True iff playwright imports AND its chromium binary is on disk."""
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            return Path(p.chromium.executable_path).exists()
    except Exception:
        return False


def capture_png(url: str, *, viewport: tuple[int, int] = (1280, 720),
                full_page: bool = False, masks: tuple[str, ...] = (),
                timeout_s: int = 30) -> tuple[bytes, dict]:
    try:
        from playwright.sync_api import Error as PWError
        from playwright.sync_api import sync_playwright
    except ImportError as e:  # dependency floor guarantees this; belt-and-braces
        raise ToolError("NO_BROWSER", f"playwright not importable: {e}", exit_code=3) from e
    if not browser_available():
        raise ToolError(
            "NO_BROWSER",
            "chromium is not installed; run: groundwork visdiff install-browser",
            exit_code=3)
    timeout_ms = timeout_s * 1000
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(args=_LAUNCH_ARGS)
            try:
                ctx = browser.new_context(
                    viewport={"width": viewport[0], "height": viewport[1]},
                    device_scale_factor=1, reduced_motion="reduce",
                    color_scheme="light", timezone_id="UTC", locale="en-US")
                page = ctx.new_page()
                page.goto(url, wait_until="networkidle", timeout=timeout_ms)
                page.wait_for_function("document.fonts.status === 'loaded'",
                                       timeout=timeout_ms)
                png = page.screenshot(
                    full_page=full_page, animations="disabled", caret="hide",
                    mask=[page.locator(sel) for sel in masks],
                    # Playwright's default mask color is #FF00FF, which a page
                    # can legitimately contain; pin black so "masked" is
                    # unambiguous and the contract really is "blacked out".
                    mask_color="#000000", timeout=timeout_ms)
                version = browser.version
            finally:
                browser.close()
    except PWError as e:
        raise ToolError("PAGE_ERROR", f"capture failed for {url}: {e}",
                        exit_code=1) from e
    return png, {"browser_version": version, "viewport": [viewport[0], viewport[1]]}
