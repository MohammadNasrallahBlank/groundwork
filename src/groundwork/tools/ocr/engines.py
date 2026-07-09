"""Two OCR engines behind one item schema: RapidOCR (primary), tesseract (fallback)."""
import importlib.util
import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

from groundwork.core.runner import ToolError

_ENGINE = None  # RapidOCR session is expensive (~1s); build once per process


def rapidocr_available() -> bool:
    return importlib.util.find_spec("rapidocr_onnxruntime") is not None


def tesseract_available() -> bool:
    return shutil.which("tesseract") is not None


def _quad_to_ints(quad) -> list[list[int]]:
    return [[int(round(x)), int(round(y))] for x, y in quad]


def _quad_bbox(quad: list[list[int]]) -> list[int]:
    xs = [p[0] for p in quad]
    ys = [p[1] for p in quad]
    return [min(xs), min(ys), max(xs), max(ys)]


def run_rapidocr(image: np.ndarray) -> list[dict]:
    global _ENGINE
    if _ENGINE is None:
        from rapidocr_onnxruntime import RapidOCR
        _ENGINE = RapidOCR()
    try:
        result, _elapse = _ENGINE(image)
    except Exception as e:
        raise ToolError("ENGINE_ERROR", f"rapidocr failed: {e}") from e
    items = []
    for quad, text, score in result or []:
        q = _quad_to_ints(quad)
        items.append({"text": str(text), "confidence": round(float(score), 4),
                      "bbox": _quad_bbox(q), "quad": q})
    return items


def parse_tesseract_tsv(tsv: str) -> list[dict]:
    """Word rows (level 5) with a real confidence; anything malformed is skipped."""
    items = []
    for line in tsv.splitlines()[1:]:
        cols = line.split("\t")
        if len(cols) < 12 or cols[0] != "5":
            continue
        try:
            left, top, width, height = (int(cols[6]), int(cols[7]),
                                        int(cols[8]), int(cols[9]))
            conf = float(cols[10])
        except ValueError:
            continue
        text = cols[11].strip()
        if conf < 0 or not text:
            continue
        bbox = [left, top, left + width, top + height]
        quad = [[bbox[0], bbox[1]], [bbox[2], bbox[1]],
                [bbox[2], bbox[3]], [bbox[0], bbox[3]]]
        items.append({"text": text, "confidence": round(conf / 100, 4),
                      "bbox": bbox, "quad": quad})
    return items


def run_tesseract(image: Image.Image) -> list[dict]:
    if not tesseract_available():
        raise ToolError("NO_ENGINE", "tesseract is not on PATH", exit_code=3)
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "ocr-input.png"
        image.save(p, format="PNG")
        try:
            proc = subprocess.run(
                ["tesseract", str(p), "stdout", "tsv"],
                capture_output=True, text=True, encoding="utf-8",
                errors="replace", timeout=120)
        except subprocess.TimeoutExpired as e:
            raise ToolError("ENGINE_ERROR", "tesseract timed out") from e
        except OSError as e:
            raise ToolError("ENGINE_ERROR", f"tesseract failed to start: {e}") from e
    if proc.returncode != 0:
        raise ToolError("ENGINE_ERROR", "tesseract exited non-zero",
                        detail=proc.stderr[-2000:])
    return parse_tesseract_tsv(proc.stdout)
