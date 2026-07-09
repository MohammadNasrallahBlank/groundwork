import numpy as np

from groundwork.tools.imgmeasure.analyze import count_components, profile_skeleton


def _shapes() -> np.ndarray:
    img = np.full((200, 300), 230, dtype=np.uint8)
    img[20:60, 20:60] = 10        # 40x40 square
    img[100:110, 50:250] = 10     # 10x200 bar
    img[150:154, 280:284] = 10    # 4x4 speck (16 px, above default min_area 8)
    return img


def test_count_components_with_stats():
    out = count_components(_shapes())
    assert out["count"] == 3
    areas = [c["area"] for c in out["components"]]
    assert areas == sorted(areas, reverse=True)
    # the 10x200 bar (2000 px) outranks the 40x40 square (1600 px)
    assert out["components"][0]["area"] == 10 * 200
    assert out["components"][0]["bbox"] == [50, 100, 250, 110]
    assert out["components"][1]["area"] == 40 * 40
    assert out["components"][1]["bbox"] == [20, 20, 60, 60]
    cx, cy = out["components"][1]["centroid"]
    assert abs(cx - 39.5) < 1 and abs(cy - 39.5) < 1


def test_min_area_filters_specks():
    out = count_components(_shapes(), min_area=100)
    assert out["count"] == 2


def test_count_blank_is_zero_not_error():
    blank = np.full((50, 50), 255, dtype=np.uint8)
    out = count_components(blank, threshold=128)
    assert out["count"] == 0 and out["components"] == []


def test_profile_bar_width_and_length():
    img = np.full((100, 300), 230, dtype=np.uint8)
    img[45:54, 20:280] = 10       # 9 px tall, 260 px long bar
    out = profile_skeleton(img)
    assert 240 <= out["skeleton_pixels"] <= 260
    assert out["foreground_pixels"] == 9 * 260
    assert abs(out["width"]["mean"] - 9.0) <= 1.5


def test_profile_blank_returns_null_width():
    blank = np.full((50, 50), 255, dtype=np.uint8)
    out = profile_skeleton(blank, threshold=128)
    assert out["skeleton_pixels"] == 0 and out["width"] is None
