"""Load image -> validate/crop region -> run engine -> full-image coordinates."""
from pathlib import Path

import numpy as np
from PIL import Image, UnidentifiedImageError

from groundwork.core.runner import ToolError
from groundwork.tools.ocr import engines

_ENGINES = ("auto", "rapidocr", "tesseract")


def _pick_engine(requested: str) -> str:
    if requested not in _ENGINES:
        raise ToolError("USAGE", f"--engine must be one of {_ENGINES}, got {requested!r}",
                        exit_code=2)
    if requested == "rapidocr" and not engines.rapidocr_available():
        raise ToolError("NO_ENGINE", "rapidocr is not importable", exit_code=3)
    if requested == "tesseract" and not engines.tesseract_available():
        raise ToolError("NO_ENGINE", "tesseract is not on PATH", exit_code=3)
    if requested != "auto":
        return requested
    if engines.rapidocr_available():
        return "rapidocr"
    if engines.tesseract_available():
        return "tesseract"
    raise ToolError("NO_ENGINE",
                    "no OCR engine available (rapidocr not importable, "
                    "tesseract not on PATH)", exit_code=3)


def _offset(items: list[dict], dx: int, dy: int) -> list[dict]:
    for it in items:
        x0, y0, x1, y1 = it["bbox"]
        it["bbox"] = [x0 + dx, y0 + dy, x1 + dx, y1 + dy]
        it["quad"] = [[x + dx, y + dy] for x, y in it["quad"]]
    return items


def read_image(image_path: Path, *, engine: str = "auto",
               region: tuple[int, int, int, int] | None = None) -> dict:
    chosen = _pick_engine(engine)
    image_path = Path(image_path)
    if not image_path.is_file():
        raise ToolError("NO_IMAGE", f"no such image: {image_path.as_posix()}",
                        exit_code=2)
    try:
        img = Image.open(image_path).convert("RGB")
    except (UnidentifiedImageError, OSError) as e:
        raise ToolError("BAD_IMAGE",
                        f"cannot decode image {image_path.as_posix()}: {e}") from e
    w, h = img.size
    dx = dy = 0
    if region is not None:
        x0, y0, x1, y1 = region
        if not (0 <= x0 < x1 <= w and 0 <= y0 < y1 <= h):
            raise ToolError("REGION_OUT_OF_BOUNDS",
                            f"region {list(region)} outside image {w}x{h} "
                            f"(need 0 <= x0 < x1 <= {w}, 0 <= y0 < y1 <= {h})",
                            exit_code=2)
        img = img.crop((x0, y0, x1, y1))
        dx, dy = x0, y0
    if chosen == "rapidocr":
        items = engines.run_rapidocr(np.asarray(img))
    else:
        items = engines.run_tesseract(img)
    return {"engine": chosen, "image": image_path.as_posix(), "size": [w, h],
            "region": list(region) if region is not None else None,
            "items": _offset(items, dx, dy)}
