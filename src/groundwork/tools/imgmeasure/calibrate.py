"""ArUco fiducial scale calibration: detected marker side in px -> mm per px."""
import cv2
import numpy as np

from groundwork.core.runner import ToolError

_DICTS = {"4x4_50": cv2.aruco.DICT_4X4_50,
          "5x5_100": cv2.aruco.DICT_5X5_100,
          "6x6_250": cv2.aruco.DICT_6X6_250}


def calibrate_scale(gray: np.ndarray, marker_mm: float,
                    dict_name: str = "4x4_50") -> dict:
    if dict_name not in _DICTS:
        raise ToolError("USAGE", f"--dict must be one of {sorted(_DICTS)}, "
                                 f"got {dict_name!r}", exit_code=2)
    d = cv2.aruco.getPredefinedDictionary(_DICTS[dict_name])
    corners, ids, _rejected = cv2.aruco.ArucoDetector(d).detectMarkers(gray)
    if ids is None or len(ids) == 0:
        raise ToolError("NO_MARKER",
                        f"no {dict_name} ArUco marker found in the image")
    markers = []
    for marker_id, quad in sorted(zip(ids.ravel().tolist(), corners)):
        c = quad.reshape(4, 2)
        side = float(np.mean([np.linalg.norm(c[i] - c[(i + 1) % 4])
                              for i in range(4)]))
        markers.append({"id": int(marker_id), "side_px": round(side, 4)})
    mean_side = float(np.mean([m["side_px"] for m in markers]))
    return {"markers": markers, "marker_mm": marker_mm,
            "mm_per_px": round(marker_mm / mean_side, 6)}
