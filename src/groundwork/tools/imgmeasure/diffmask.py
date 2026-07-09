"""Registration-aligned change mask: warp B onto A, threshold the difference."""
from pathlib import Path

import cv2
import numpy as np

from groundwork.tools.imgmeasure.imageio import write_png
from groundwork.tools.imgmeasure.registration import register_arrays

_MAX_REGIONS = 50


def diff_mask(gray_a: np.ndarray, gray_b: np.ndarray, root: Path, name: str, *,
              threshold: int = 32, min_matches: int = 15,
              min_inlier_ratio: float = 0.5) -> dict:
    reg = register_arrays(gray_a, gray_b, min_matches=min_matches,
                          min_inlier_ratio=min_inlier_ratio)
    h = np.array(reg["homography"], dtype=np.float64)
    hh, ww = gray_a.shape
    # H maps A -> B; warp B back onto A's frame with the inverse.
    aligned_b = cv2.warpPerspective(gray_b, np.linalg.inv(h), (ww, hh))
    delta = cv2.absdiff(gray_a, aligned_b)
    # Pixels the warp left undefined (borders) read as huge diffs; mask them out
    # by warping a white frame the same way and requiring coverage.
    coverage = cv2.warpPerspective(np.full_like(gray_b, 255), np.linalg.inv(h),
                                   (ww, hh))
    mask = (delta > threshold) & (coverage > 0)

    regions = []
    n, _labels, stats, _cent = cv2.connectedComponentsWithStats(
        mask.astype(np.uint8) * 255, connectivity=8)
    for i in range(1, n):
        x = int(stats[i, cv2.CC_STAT_LEFT])
        y = int(stats[i, cv2.CC_STAT_TOP])
        w = int(stats[i, cv2.CC_STAT_WIDTH])
        hgt = int(stats[i, cv2.CC_STAT_HEIGHT])
        regions.append({"bbox": [x, y, x + w, y + hgt],
                        "pixels": int(stats[i, cv2.CC_STAT_AREA])})
    regions.sort(key=lambda r: (-r["pixels"], r["bbox"]))
    regions = regions[:_MAX_REGIONS]

    art_dir = Path(root) / ".groundwork" / "imgmeasure"
    art_dir.mkdir(parents=True, exist_ok=True)
    mask_path = art_dir / f"{name}-mask.png"
    write_png(mask_path, mask.astype(np.uint8) * 255)

    total = int(mask.size)
    changed = int(mask.sum())
    return {"registration": reg, "threshold": threshold,
            "changed_pixels": changed,
            "changed_ratio": round(changed / total, 6) if total else 0.0,
            "regions": regions, "mask_path": mask_path.as_posix()}
