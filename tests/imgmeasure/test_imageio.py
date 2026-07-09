import numpy as np
import pytest

from groundwork.core.runner import ToolError
from groundwork.tools.imgmeasure.imageio import binarize, load_gray, write_png


def test_load_gray_round_trip_with_unicode_name(tmp_path, textured):
    img = textured()
    p = tmp_path / "imagé-测试.png"       # cv2.imread would fail on this on Windows
    write_png(p, img)
    back = load_gray(p)
    assert back.shape == img.shape and back.dtype == np.uint8
    assert np.array_equal(back, img)


def test_load_gray_missing_is_usage_error(tmp_path):
    with pytest.raises(ToolError) as ei:
        load_gray(tmp_path / "nope.png")
    assert ei.value.code == "NO_IMAGE" and ei.value.exit_code == 2


def test_load_gray_undecodable_is_tool_error(tmp_path):
    p = tmp_path / "junk.png"
    p.write_bytes(b"not an image")
    with pytest.raises(ToolError) as ei:
        load_gray(p)
    assert ei.value.code == "BAD_IMAGE" and ei.value.exit_code == 1


def test_binarize_otsu_and_fixed_and_invert():
    gray = np.full((10, 10), 200, dtype=np.uint8)
    gray[2:5, 2:5] = 20                    # dark square on light background
    mask, used = binarize(gray, "otsu", invert=False)
    assert mask[3, 3] and not mask[0, 0]   # dark is foreground
    # cv2's Otsu returns the dark class's exact value (20) for this bimodal
    # image — which is why the foreground rule is <=, not <.
    assert 20 <= used < 200
    mask2, used2 = binarize(gray, 128, invert=True)
    assert used2 == 128
    assert not mask2[3, 3] and mask2[0, 0]


def test_binarize_bad_spec_is_usage():
    gray = np.zeros((4, 4), dtype=np.uint8)
    for bad in ("banana", -1, 256):
        with pytest.raises(ToolError) as ei:
            binarize(gray, bad, invert=False)
        assert ei.value.code == "USAGE" and ei.value.exit_code == 2
