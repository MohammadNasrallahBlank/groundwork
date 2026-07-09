import numpy as np
import pytest

from groundwork.core.runner import ToolError
from groundwork.tools.imgmeasure.registration import register_arrays


def test_register_recovers_translation_with_ecc_refine(textured, shift):
    base = textured()
    out = register_arrays(base, shift(base, 12.0, -7.0))
    assert out["inlier_ratio"] > 0.8 and out["matches"] > 100
    dx, dy = out["translation"]
    assert abs(dx - 12.0) < 1.0 and abs(dy + 7.0) < 1.0
    assert out["ecc"] is not None and out["ecc"] > 0.9
    edx, edy = out["ecc_translation"]
    assert abs(edx - 12.0) < 0.5 and abs(edy + 7.0) < 0.5
    h = np.array(out["homography"])
    assert h.shape == (3, 3) and abs(h[2, 2] - 1.0) < 1e-6


def test_featureless_images_escalate(textured):
    blank_a = np.full((200, 200), 255, dtype=np.uint8)
    blank_b = np.full((200, 200), 255, dtype=np.uint8)
    with pytest.raises(ToolError) as ei:
        register_arrays(blank_a, blank_b)
    assert ei.value.code == "UNRELIABLE_REGISTRATION" and ei.value.exit_code == 4
    assert "matches" in ei.value.detail


def test_unrelated_images_escalate_on_inlier_ratio(textured):
    rng = np.random.default_rng(7)
    import cv2
    other = cv2.GaussianBlur((rng.random((400, 600)) * 255).astype(np.uint8), (5, 5), 0)
    with pytest.raises(ToolError) as ei:
        register_arrays(textured(), other, min_inlier_ratio=0.5)
    assert ei.value.code == "UNRELIABLE_REGISTRATION" and ei.value.exit_code == 4
