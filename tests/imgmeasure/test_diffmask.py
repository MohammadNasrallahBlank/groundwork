import numpy as np
import pytest

from groundwork.core.runner import ToolError
from groundwork.tools.imgmeasure.diffmask import diff_mask


def test_shifted_frame_with_local_change_isolates_the_change(tmp_path, textured, shift):
    base = textured()
    changed = shift(base, 6.0, 3.0)          # camera moved...
    changed[200:240, 300:360] = 0            # ...AND a real local change
    out = diff_mask(base, changed, tmp_path, "case1")
    assert out["registration"]["inlier_ratio"] > 0.5
    assert out["changed_pixels"] > 0
    # the real change must dominate the regions despite the global shift
    x0, y0, x1, y1 = out["regions"][0]["bbox"]
    # region is in A's frame; the change was painted in B at (300,200)-(360,240),
    # which maps back to A at roughly (294,197)-(354,237); allow warp tolerance
    assert abs(x0 - 294) < 10 and abs(y0 - 197) < 10
    assert (tmp_path / ".groundwork" / "imgmeasure" / "case1-mask.png").exists()
    assert "\\" not in out["mask_path"]


def test_identical_frames_have_no_regions(tmp_path, textured):
    base = textured()
    out = diff_mask(base, base.copy(), tmp_path, "same")
    assert out["changed_pixels"] == 0 and out["regions"] == []


def test_unregisterable_pair_escalates(tmp_path):
    blank = np.full((200, 200), 255, dtype=np.uint8)
    with pytest.raises(ToolError) as ei:
        diff_mask(blank, blank.copy(), tmp_path, "blank")
    assert ei.value.code == "UNRELIABLE_REGISTRATION" and ei.value.exit_code == 4
