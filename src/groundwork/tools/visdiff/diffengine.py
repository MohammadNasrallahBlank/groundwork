"""Pure image comparison: SSIM + AA-aware pixel diff + region extraction."""
import io

import numpy as np
from PIL import Image
from pixelmatch.contrib.PIL import pixelmatch
from skimage.measure import label, regionprops
from skimage.metrics import structural_similarity

# Channel-difference floor (of 255) above which a pixel counts toward a region.
# Below this is rasterization noise; above it is a visible change.
_REGION_DIFF_FLOOR = 32
_MAX_REGIONS = 50


def _load(png: bytes) -> Image.Image:
    return Image.open(io.BytesIO(png)).convert("RGB")


def diff_images(baseline_png: bytes, actual_png: bytes) -> dict:
    """Compare two PNGs. Returns size_mismatch, ssim, pixel_diff_count,
    pixel_diff_ratio, regions (bbox [x0, y0, x1, y1] half-open, pixels,
    severity), and the pixelmatch diff image as PNG bytes."""
    base, act = _load(baseline_png), _load(actual_png)
    if base.size != act.size:
        return {"size_mismatch": True, "ssim": 0.0, "pixel_diff_count": 0,
                "pixel_diff_ratio": 1.0, "regions": [], "diff_png": b""}
    a = np.asarray(base)
    b = np.asarray(act)
    ssim = float(structural_similarity(a, b, channel_axis=-1, data_range=255))

    diff_img = Image.new("RGBA", base.size)
    count = int(pixelmatch(base, act, diff_img, threshold=0.1, includeAA=False))
    total = base.size[0] * base.size[1]
    ratio = count / total if total else 0.0

    # Regions from the raw channel-max difference: deterministic, independent
    # of pixelmatch's perceptual weighting.
    delta = np.abs(a.astype(np.int16) - b.astype(np.int16)).max(axis=-1)
    mask = delta > _REGION_DIFF_FLOOR
    regions = []
    if mask.any():
        for r in regionprops(label(mask, connectivity=2)):
            y0, x0, y1, x1 = r.bbox  # skimage bbox is (row, col) ordered
            sub = delta[y0:y1, x0:x1]
            regions.append({"bbox": [int(x0), int(y0), int(x1), int(y1)],
                            "pixels": int(r.area),
                            "severity": round(float(sub[sub > _REGION_DIFF_FLOOR].mean()) / 255, 4)})
        regions.sort(key=lambda r: (-r["pixels"], r["bbox"]))
        regions = regions[:_MAX_REGIONS]

    buf = io.BytesIO()
    diff_img.save(buf, format="PNG")
    return {"size_mismatch": False, "ssim": round(ssim, 4),
            "pixel_diff_count": count, "pixel_diff_ratio": round(ratio, 6),
            "regions": regions, "diff_png": buf.getvalue()}


def composite(baseline_png: bytes, actual_png: bytes, diff_png: bytes) -> bytes:
    """Horizontal strip: baseline | actual | diff, 8px separators, for humans."""
    base, act = _load(baseline_png), _load(actual_png)
    diff = _load(diff_png) if diff_png else Image.new("RGB", base.size, (255, 255, 255))
    sep = 8
    h = max(base.height, act.height, diff.height)
    w = base.width + act.width + diff.width + 2 * sep
    strip = Image.new("RGB", (w, h), (30, 30, 30))
    x = 0
    for panel in (base, act, diff):
        strip.paste(panel, (x, 0))
        x += panel.width + sep
    buf = io.BytesIO()
    strip.save(buf, format="PNG")
    return buf.getvalue()
