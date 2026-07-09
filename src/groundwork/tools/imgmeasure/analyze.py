"""Component counting and skeleton/width profiling over the shared threshold."""
import cv2
import numpy as np

from groundwork.tools.imgmeasure.imageio import binarize

_MAX_COMPONENTS = 200


def count_components(gray: np.ndarray, *, threshold="otsu", invert: bool = False,
                     min_area: int = 8) -> dict:
    mask, used = binarize(gray, threshold, invert)
    n, _labels, stats, centroids = cv2.connectedComponentsWithStats(
        mask.astype(np.uint8) * 255, connectivity=8)
    comps = []
    for i in range(1, n):  # label 0 is the background
        area = int(stats[i, cv2.CC_STAT_AREA])
        if area < min_area:
            continue
        x = int(stats[i, cv2.CC_STAT_LEFT])
        y = int(stats[i, cv2.CC_STAT_TOP])
        w = int(stats[i, cv2.CC_STAT_WIDTH])
        h = int(stats[i, cv2.CC_STAT_HEIGHT])
        comps.append({"bbox": [x, y, x + w, y + h], "area": area,
                      "centroid": [round(float(centroids[i][0]), 4),
                                   round(float(centroids[i][1]), 4)]})
    comps.sort(key=lambda c: (-c["area"], c["bbox"]))
    return {"count": len(comps), "threshold_used": used, "min_area": min_area,
            "components": comps[:_MAX_COMPONENTS]}


def profile_skeleton(gray: np.ndarray, *, threshold="otsu",
                     invert: bool = False) -> dict:
    from scipy.ndimage import distance_transform_edt
    from skimage.morphology import skeletonize

    mask, used = binarize(gray, threshold, invert)
    fg = int(mask.sum())
    if fg == 0:
        return {"skeleton_pixels": 0, "foreground_pixels": 0,
                "threshold_used": used, "width": None}
    sk = skeletonize(mask)
    sk_px = int(sk.sum())
    if sk_px == 0:
        return {"skeleton_pixels": 0, "foreground_pixels": fg,
                "threshold_used": used, "width": None}
    widths = 2 * distance_transform_edt(mask)[sk]
    return {"skeleton_pixels": sk_px, "foreground_pixels": fg,
            "threshold_used": used,
            "width": {"mean": round(float(widths.mean()), 4),
                      "min": round(float(widths.min()), 4),
                      "max": round(float(widths.max()), 4)}}
