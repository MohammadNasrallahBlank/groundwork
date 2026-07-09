"""Pins the external API shapes plan 07 targets. A failure here means the
installed library differs from the plan's assumption: correct the PLAN (and
the code that follows it) to the real shape — do not weaken these tests."""
import numpy as np
import pytest
from PIL import Image


def _solid(w, h, rgb):
    return Image.new("RGB", (w, h), rgb)


def test_ssim_identical_images_score_one():
    from skimage.metrics import structural_similarity
    a = np.asarray(_solid(32, 32, (200, 10, 10)))
    score = structural_similarity(a, a, channel_axis=-1, data_range=255)
    assert score == pytest.approx(1.0)


def test_label_and_regionprops_bbox_shape():
    from skimage.measure import label, regionprops
    mask = np.zeros((20, 20), dtype=bool)
    mask[5:10, 3:8] = True
    regions = regionprops(label(mask, connectivity=2))
    assert len(regions) == 1
    # bbox is (min_row, min_col, max_row, max_col) — half-open
    assert regions[0].bbox == (5, 3, 10, 8)


def test_pixelmatch_pil_contract():
    # Verified-at-authoring shape: pixelmatch(img1, img2, output=None, ...)
    # returns the count of mismatched pixels and paints the diff into output.
    from pixelmatch.contrib.PIL import pixelmatch
    a = _solid(16, 16, (255, 255, 255))
    b = _solid(16, 16, (255, 255, 255))
    b.putpixel((4, 4), (0, 0, 0))
    out = Image.new("RGBA", (16, 16))
    count = pixelmatch(a, b, out, threshold=0.1, includeAA=False)
    assert count >= 1
    assert out.size == (16, 16)


def test_playwright_exposes_chromium_executable_path():
    # We only pin the API here, NOT that the binary exists: executable_path
    # must be a string path whether or not `install-browser` has ever run.
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        path = p.chromium.executable_path
    assert isinstance(path, str) and len(path) > 0
