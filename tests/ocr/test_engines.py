import numpy as np
import pytest
from PIL import Image

from groundwork.tools.ocr.engines import (parse_tesseract_tsv, rapidocr_available,
                                          run_rapidocr, run_tesseract,
                                          tesseract_available)

requires_tesseract = pytest.mark.skipif(
    not tesseract_available(), reason="tesseract binary not on PATH")


def test_rapidocr_available_here():
    assert rapidocr_available() is True  # it is a hard dependency of groundwork


def test_run_rapidocr_emits_item_schema(render_text):
    items = run_rapidocr(np.asarray(render_text(["GROUNDWORK 42"])))
    assert len(items) >= 1
    it = items[0]
    assert set(it) == {"text", "confidence", "bbox", "quad"}
    assert "GROUNDWORK" in it["text"].upper()
    x0, y0, x1, y1 = it["bbox"]
    assert all(isinstance(v, int) for v in (x0, y0, x1, y1))
    assert x0 < x1 and y0 < y1
    assert len(it["quad"]) == 4 and all(isinstance(v, int) for pt in it["quad"] for v in pt)
    assert 0.0 < it["confidence"] <= 1.0


def test_run_rapidocr_blank_image_is_empty_list():
    assert run_rapidocr(np.asarray(Image.new("RGB", (200, 100), (255, 255, 255)))) == []


_TSV = (
    "level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext\n"
    "1\t1\t0\t0\t0\t0\t0\t0\t640\t200\t-1\t\n"
    "5\t1\t1\t1\t1\t1\t22\t32\t180\t38\t96.5\tGROUNDWORK\n"
    "5\t1\t1\t1\t1\t2\t210\t32\t60\t38\t91.0\t42\n"
    "5\t1\t1\t1\t2\t1\t22\t110\t90\t40\t-1\t\n"          # conf -1 -> skipped
    "not\ta\tvalid\trow\n"                                    # garbage -> skipped
)


def test_parse_tesseract_tsv_words_only_with_bbox_and_conf():
    items = parse_tesseract_tsv(_TSV)
    assert [i["text"] for i in items] == ["GROUNDWORK", "42"]
    assert items[0]["bbox"] == [22, 32, 202, 70]     # left, top, left+w, top+h
    assert items[0]["confidence"] == 0.965
    assert items[0]["quad"] == [[22, 32], [202, 32], [202, 70], [22, 70]]


def test_parse_tesseract_tsv_garbage_only_is_empty():
    assert parse_tesseract_tsv("total garbage\nwith\ttabs\n") == []


@requires_tesseract
def test_run_tesseract_reads_rendered_text(render_text):
    items = run_tesseract(render_text(["GROUNDWORK 42"]))
    assert any("GROUNDWORK" in i["text"].upper() for i in items)
