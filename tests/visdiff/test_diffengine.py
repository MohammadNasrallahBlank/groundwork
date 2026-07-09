import io

import pytest
from PIL import Image

from groundwork.tools.visdiff.diffengine import composite, diff_images


def _png(w, h, rgb, box=None, box_rgb=(0, 0, 0)):
    img = Image.new("RGB", (w, h), rgb)
    if box:
        x0, y0, x1, y1 = box
        for x in range(x0, x1):
            for y in range(y0, y1):
                img.putpixel((x, y), box_rgb)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_identical_images_pass_cleanly():
    a = _png(64, 64, (240, 240, 240))
    d = diff_images(a, a)
    assert d["size_mismatch"] is False
    assert d["ssim"] == pytest.approx(1.0)
    assert d["pixel_diff_count"] == 0 and d["pixel_diff_ratio"] == 0.0
    assert d["regions"] == []


def test_changed_box_yields_one_region_with_right_bbox():
    base = _png(64, 64, (240, 240, 240))
    actual = _png(64, 64, (240, 240, 240), box=(10, 20, 30, 40))
    d = diff_images(base, actual)
    assert d["ssim"] < 1.0
    assert d["pixel_diff_count"] >= (30 - 10) * (40 - 20)
    assert len(d["regions"]) == 1
    x0, y0, x1, y1 = d["regions"][0]["bbox"]
    # region must cover the injected box (AA tolerance allows ±1 growth)
    assert x0 <= 10 and y0 <= 20 and x1 >= 30 and y1 >= 40
    assert 0.0 < d["regions"][0]["severity"] <= 1.0


def test_two_separate_boxes_yield_two_regions_sorted_by_size():
    base = _png(64, 64, (240, 240, 240))
    actual = _png(64, 64, (240, 240, 240), box=(2, 2, 6, 6))
    img = Image.open(io.BytesIO(actual))
    for x in range(40, 60):
        for y in range(40, 60):
            img.putpixel((x, y), (0, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    d = diff_images(base, buf.getvalue())
    assert len(d["regions"]) == 2
    assert d["regions"][0]["pixels"] >= d["regions"][1]["pixels"]


def test_size_mismatch_short_circuits():
    d = diff_images(_png(64, 64, (0, 0, 0)), _png(32, 64, (0, 0, 0)))
    assert d["size_mismatch"] is True
    assert d["ssim"] == 0.0 and d["pixel_diff_ratio"] == 1.0
    assert d["regions"] == [] and d["diff_png"] == b""


def test_composite_is_three_wide_strip():
    a = _png(40, 30, (200, 200, 200))
    d = diff_images(a, a)
    strip = composite(a, a, d["diff_png"])
    img = Image.open(io.BytesIO(strip))
    assert img.height == 30
    assert img.width >= 40 * 3  # three panels plus separators
