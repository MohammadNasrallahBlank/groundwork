import pytest

from groundwork.core.runner import ToolError
from groundwork.tools.ocr.reader import read_image


@pytest.fixture()
def two_line_png(tmp_path, render_text):
    p = tmp_path / "two.png"
    render_text(["GROUNDWORK 42", "hello ocr"]).save(p)
    return p


def test_read_whole_image(two_line_png):
    out = read_image(two_line_png)
    assert out["engine"] == "rapidocr"
    texts = " ".join(i["text"] for i in out["items"]).upper()
    assert "GROUNDWORK" in texts and "HELLO" in texts
    assert out["region"] is None
    assert "\\" not in out["image"]
    assert out["size"] == [640, 200]


def test_region_restricts_and_offsets_back(two_line_png):
    # second line lives in the lower band; region uses visdiff's bbox shape
    out = read_image(two_line_png, region=(0, 90, 640, 200))
    texts = " ".join(i["text"] for i in out["items"]).upper()
    assert "HELLO" in texts and "GROUNDWORK" not in texts
    # coordinates come back in FULL-image space: y0 must be >= the region top
    assert all(i["bbox"][1] >= 90 for i in out["items"])
    assert all(pt[1] >= 90 for i in out["items"] for pt in i["quad"])


@pytest.mark.parametrize("bad", [(-1, 0, 10, 10), (0, 0, 10, 999),
                                 (10, 10, 10, 20), (30, 30, 20, 40)])
def test_region_out_of_bounds_is_usage_error(two_line_png, bad):
    with pytest.raises(ToolError) as ei:
        read_image(two_line_png, region=bad)
    assert ei.value.code == "REGION_OUT_OF_BOUNDS" and ei.value.exit_code == 2


def test_missing_image_is_usage_error(tmp_path):
    with pytest.raises(ToolError) as ei:
        read_image(tmp_path / "nope.png")
    assert ei.value.code == "NO_IMAGE" and ei.value.exit_code == 2


def test_corrupt_image_is_tool_error(tmp_path):
    p = tmp_path / "junk.png"
    p.write_bytes(b"this is not a png at all")
    with pytest.raises(ToolError) as ei:
        read_image(p)
    assert ei.value.code == "BAD_IMAGE" and ei.value.exit_code == 1


def test_unknown_engine_rejected(two_line_png):
    with pytest.raises(ToolError) as ei:
        read_image(two_line_png, engine="sorcery")
    assert ei.value.code == "USAGE" and ei.value.exit_code == 2
