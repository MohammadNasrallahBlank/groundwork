import io
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from groundwork.tools.visdiff.capture import browser_available, capture_png

FIX = Path("tests/fixtures/visdiff").resolve()

requires_browser = pytest.mark.skipif(
    not browser_available(),
    reason="chromium not installed (run: groundwork visdiff install-browser)")


def _arr(png: bytes):
    return np.asarray(Image.open(io.BytesIO(png)).convert("RGB"))


@requires_browser
def test_capture_is_deterministic_same_machine():
    url = (FIX / "page.html").as_uri()
    png1, info1 = capture_png(url, viewport=(640, 480))
    png2, _ = capture_png(url, viewport=(640, 480))
    assert np.array_equal(_arr(png1), _arr(png2))
    assert info1["viewport"] == [640, 480]
    assert info1["browser_version"]


@requires_browser
def test_viewport_sets_image_size():
    url = (FIX / "page.html").as_uri()
    png, _ = capture_png(url, viewport=(640, 480))
    assert _arr(png).shape[:2] == (480, 640)


@requires_browser
def test_mask_blacks_out_volatile_region():
    url = (FIX / "page.html").as_uri()
    plain, _ = capture_png(url, viewport=(640, 480))
    masked, _ = capture_png(url, viewport=(640, 480), masks=("#volatile",))
    # the two differ exactly where the mask painted over the magenta box
    assert not np.array_equal(_arr(plain), _arr(masked))
    a = _arr(masked)
    # magenta (255,0,255) must be gone from the masked capture
    assert not ((a[:, :, 0] > 200) & (a[:, :, 1] < 50) & (a[:, :, 2] > 200)).any()


@requires_browser
def test_bad_url_raises_page_error():
    from groundwork.core.runner import ToolError
    with pytest.raises(ToolError) as ei:
        capture_png((FIX / "does-not-exist.html").as_uri(), timeout_s=10)
    assert ei.value.code == "PAGE_ERROR" and ei.value.exit_code == 1
