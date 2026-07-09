"""Pins the RapidOCR API shape plan 08 targets (verified at authoring,
2026-07-08, on this machine). If the installed version differs, correct the
PLAN and its code to the real shape — do not weaken these tests."""
from pathlib import Path

import numpy as np
from PIL import Image


def test_rapidocr_reads_rendered_text_with_quads_and_scores(render_text):
    from rapidocr_onnxruntime import RapidOCR
    engine = RapidOCR()
    result, _elapse = engine(np.asarray(render_text(["GROUNDWORK 42"])))
    assert isinstance(result, list) and len(result) >= 1
    quad, text, score = result[0]
    assert len(quad) == 4 and all(len(pt) == 2 for pt in quad)
    assert "GROUNDWORK" in text.upper()
    assert 0.5 < float(score) <= 1.0


def test_rapidocr_blank_image_yields_none_or_empty():
    from rapidocr_onnxruntime import RapidOCR
    engine = RapidOCR()
    result, _ = engine(np.asarray(Image.new("RGB", (200, 100), (255, 255, 255))))
    assert result is None or result == []


def test_models_are_bundled_in_the_wheel():
    import rapidocr_onnxruntime
    pkg = Path(rapidocr_onnxruntime.__file__).parent
    onnx = sorted(p.name for p in pkg.rglob("*.onnx"))
    assert len(onnx) >= 3  # det + rec + cls ship inside the package
