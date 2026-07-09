import numpy as np
import pytest

from groundwork.core.runner import ToolError
from groundwork.tools.imgmeasure.calibrate import calibrate_scale


def test_calibrate_from_generated_marker(marker_canvas):
    out = calibrate_scale(marker_canvas(marker_id=7, side=120), marker_mm=60.0)
    assert [m["id"] for m in out["markers"]] == [7]
    side = out["markers"][0]["side_px"]
    assert abs(side - 120.0) < 3.0
    assert out["mm_per_px"] == pytest.approx(60.0 / side, rel=1e-6)


def test_no_marker_is_definite_error():
    blank = np.full((200, 200), 255, dtype=np.uint8)
    with pytest.raises(ToolError) as ei:
        calibrate_scale(blank, marker_mm=60.0)
    assert ei.value.code == "NO_MARKER" and ei.value.exit_code == 1


def test_unknown_dict_is_usage(marker_canvas):
    with pytest.raises(ToolError) as ei:
        calibrate_scale(marker_canvas(), marker_mm=60.0, dict_name="17x17_9000")
    assert ei.value.code == "USAGE" and ei.value.exit_code == 2
