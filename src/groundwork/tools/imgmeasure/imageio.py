"""Grayscale IO + thresholding. np.fromfile/imdecode, NEVER cv2.imread:
imread silently fails on non-ASCII Windows paths."""
from pathlib import Path

import cv2
import numpy as np

from groundwork.core.runner import ToolError


def load_gray(path: Path) -> np.ndarray:
    path = Path(path)
    if not path.is_file():
        raise ToolError("NO_IMAGE", f"no such image: {path.as_posix()}", exit_code=2)
    try:
        buf = np.fromfile(path, dtype=np.uint8)
        img = cv2.imdecode(buf, cv2.IMREAD_GRAYSCALE)
    except OSError as e:
        raise ToolError("BAD_IMAGE", f"cannot read {path.as_posix()}: {e}") from e
    if img is None:
        raise ToolError("BAD_IMAGE", f"cannot decode image {path.as_posix()}")
    return img


def write_png(path: Path, img: np.ndarray) -> None:
    ok, buf = cv2.imencode(".png", img)
    if not ok:
        raise ToolError("BAD_IMAGE", f"cannot encode png for {Path(path).as_posix()}")
    Path(path).write_bytes(buf.tobytes())


def binarize(gray: np.ndarray, threshold, invert: bool) -> tuple[np.ndarray, int]:
    """Bool foreground mask + the threshold actually used.

    Foreground is AT OR BELOW the threshold (dark objects on light background;
    cv2's binary convention is background = src > t, and Otsu can return the
    dark class's exact value); invert flips. `threshold` is "otsu" or an
    int 0-255.
    """
    if threshold == "otsu":
        used, _ = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
        used = int(used)
    else:
        try:
            used = int(threshold)
        except (TypeError, ValueError):
            raise ToolError("USAGE", f"--threshold must be 'otsu' or an int 0-255, "
                                     f"got {threshold!r}", exit_code=2) from None
        if not 0 <= used <= 255:
            raise ToolError("USAGE", f"--threshold out of range 0-255: {used}",
                            exit_code=2)
    mask = gray <= used
    if invert:
        mask = ~mask
    return mask, used
