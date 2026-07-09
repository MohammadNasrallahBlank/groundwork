"""Pins the cv2 numerics plan 09 targets (measured at authoring, 2026-07-08,
on this machine). A failure means the installed build behaves differently:
correct the PLAN and its code to the observed numbers — do not loosen blindly."""
import cv2
import numpy as np


def test_orb_ransac_recovers_translation(textured, shift):
    base = textured()
    moved = shift(base, 12.0, -7.0)
    orb = cv2.ORB_create(nfeatures=2000)
    ka, da = orb.detectAndCompute(base, None)
    kb, db = orb.detectAndCompute(moved, None)
    assert len(ka) > 500 and len(kb) > 500
    matches = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True).match(da, db)
    assert len(matches) > 100
    src = np.float32([ka[m.queryIdx].pt for m in matches]).reshape(-1, 1, 2)
    dst = np.float32([kb[m.trainIdx].pt for m in matches]).reshape(-1, 1, 2)
    h, mask = cv2.findHomography(src, dst, cv2.RANSAC, 3.0)
    assert float(mask.sum()) / len(mask) > 0.8
    assert abs(h[0, 2] - 12.0) < 1.0 and abs(h[1, 2] + 7.0) < 1.0


def test_ecc_refines_from_ransac_init_but_diverges_from_identity(textured, shift):
    base = textured()
    moved = shift(base, 12.0, -7.0)
    crit = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 100, 1e-6)
    # identity init diverges on noise textures — the documented reason the
    # pipeline seeds ECC from RANSAC:
    with np.testing.assert_raises(cv2.error):
        cv2.findTransformECC(base, moved, np.eye(2, 3, dtype=np.float32),
                             cv2.MOTION_TRANSLATION, crit)
    warp = np.float32([[1, 0, 12.1], [0, 1, -6.9]])
    cc, warp = cv2.findTransformECC(base, moved, warp, cv2.MOTION_TRANSLATION, crit)
    assert cc > 0.9
    assert abs(warp[0, 2] - 12.0) < 0.5 and abs(warp[1, 2] + 7.0) < 0.5


def test_aruco_generate_detect_round_trip(marker_canvas):
    canvas = marker_canvas(marker_id=7, side=120)
    d = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    corners, ids, _ = cv2.aruco.ArucoDetector(d).detectMarkers(canvas)
    assert ids is not None and ids.ravel().tolist() == [7]
    c = corners[0].reshape(4, 2)
    side = float(np.mean([np.linalg.norm(c[i] - c[(i + 1) % 4]) for i in range(4)]))
    assert abs(side - 120.0) < 3.0  # corner convention costs ~1 px


def test_skeleton_width_and_components_conventions():
    from scipy.ndimage import distance_transform_edt
    from skimage.morphology import skeletonize
    bar = np.zeros((100, 300), dtype=bool)
    bar[45:54, 20:280] = True  # 9 px tall, 260 px long
    sk = skeletonize(bar)
    assert 240 <= int(sk.sum()) <= 260          # endpoint erosion shortens a few px
    widths = 2 * distance_transform_edt(bar)[sk]
    assert abs(float(widths.mean()) - 9.0) <= 1.5   # 2*edt overshoots ~1 on odd widths
    n, _labels, stats, _cent = cv2.connectedComponentsWithStats(
        bar.astype(np.uint8) * 255, connectivity=8)
    assert n == 2                                # label 0 is the background
    assert stats[1, cv2.CC_STAT_AREA] == 9 * 260
