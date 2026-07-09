"""ORB -> cross-checked Hamming matches -> RANSAC homography -> ECC refine."""
import cv2
import numpy as np

from groundwork.core.envelope import EXIT_ESCALATE
from groundwork.core.runner import ToolError

_ORB_FEATURES = 2000
_RANSAC_REPROJ = 3.0
_ECC_CRITERIA = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 100, 1e-6)


def _escalate(reason: str, **detail) -> ToolError:
    return ToolError("UNRELIABLE_REGISTRATION", reason, exit_code=EXIT_ESCALATE,
                     detail=detail)


def register_arrays(gray_a: np.ndarray, gray_b: np.ndarray, *,
                    min_matches: int = 15,
                    min_inlier_ratio: float = 0.5) -> dict:
    orb = cv2.ORB_create(nfeatures=_ORB_FEATURES)
    ka, da = orb.detectAndCompute(gray_a, None)
    kb, db = orb.detectAndCompute(gray_b, None)
    if da is None or db is None or len(ka) < min_matches or len(kb) < min_matches:
        raise _escalate("too few features to register",
                        features_a=len(ka or []), features_b=len(kb or []),
                        matches=0, min_matches=min_matches)
    matches = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True).match(da, db)
    if len(matches) < min_matches:
        raise _escalate("too few matches to register",
                        features_a=len(ka), features_b=len(kb),
                        matches=len(matches), min_matches=min_matches)
    src = np.float32([ka[m.queryIdx].pt for m in matches]).reshape(-1, 1, 2)
    dst = np.float32([kb[m.trainIdx].pt for m in matches]).reshape(-1, 1, 2)
    h, mask = cv2.findHomography(src, dst, cv2.RANSAC, _RANSAC_REPROJ)
    if h is None or mask is None:
        raise _escalate("RANSAC found no homography", matches=len(matches),
                        min_inlier_ratio=min_inlier_ratio)
    inliers = int(mask.sum())
    ratio = inliers / len(mask)
    if ratio < min_inlier_ratio:
        raise _escalate("inlier ratio below floor", matches=len(matches),
                        inliers=inliers, inlier_ratio=round(ratio, 4),
                        min_inlier_ratio=min_inlier_ratio)

    ecc = ecc_translation = None
    warp = np.float32([[1, 0, h[0, 2]], [0, 1, h[1, 2]]])
    try:
        cc, warp = cv2.findTransformECC(gray_a, gray_b, warp,
                                        cv2.MOTION_TRANSLATION, _ECC_CRITERIA)
        ecc = round(float(cc), 4)
        ecc_translation = [round(float(warp[0, 2]), 4), round(float(warp[1, 2]), 4)]
    except cv2.error:
        pass  # documented degradation: RANSAC homography stands, ecc stays null

    return {"homography": [[round(float(v), 6) for v in row] for row in h],
            "matches": len(matches), "inliers": inliers,
            "inlier_ratio": round(ratio, 4),
            "translation": [round(float(h[0, 2]), 4), round(float(h[1, 2]), 4)],
            "ecc": ecc, "ecc_translation": ecc_translation,
            "size_a": [int(gray_a.shape[1]), int(gray_a.shape[0])],
            "size_b": [int(gray_b.shape[1]), int(gray_b.shape[0])]}
