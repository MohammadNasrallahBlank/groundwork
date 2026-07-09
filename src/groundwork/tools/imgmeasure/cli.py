import argparse
from pathlib import Path

from groundwork.core.cliparse import UsageParser
from groundwork.core.runner import ToolError, run_tool
from groundwork.tools.imgmeasure.analyze import count_components, profile_skeleton
from groundwork.tools.imgmeasure.calibrate import calibrate_scale
from groundwork.tools.imgmeasure.diffmask import diff_mask
from groundwork.tools.imgmeasure.imageio import load_gray
from groundwork.tools.imgmeasure.registration import register_arrays

TOOL, VERSION = "imgmeasure", "0.1.0"


def _add_threshold_args(sp) -> None:
    sp.add_argument("--threshold", default="otsu")
    sp.add_argument("--invert", action="store_true")


def handler(args: list[str]) -> dict:
    p = UsageParser(prog=f"groundwork {TOOL}", exit_on_error=False)
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("register")
    r.add_argument("--image-a", required=True)
    r.add_argument("--image-b", required=True)
    r.add_argument("--min-matches", type=int, default=15)
    r.add_argument("--min-inlier-ratio", type=float, default=0.5)
    c = sub.add_parser("calibrate")
    c.add_argument("--image", required=True)
    c.add_argument("--marker-mm", type=float, required=True)
    c.add_argument("--dict", default="4x4_50")
    n = sub.add_parser("count")
    n.add_argument("--image", required=True)
    n.add_argument("--min-area", type=int, default=8)
    _add_threshold_args(n)
    f = sub.add_parser("profile")
    f.add_argument("--image", required=True)
    _add_threshold_args(f)
    d = sub.add_parser("diffmask")
    d.add_argument("--image-a", required=True)
    d.add_argument("--image-b", required=True)
    d.add_argument("--name", default="diff")
    d.add_argument("--root", default=".")
    d.add_argument("--threshold", type=int, default=32)
    d.add_argument("--min-matches", type=int, default=15)
    d.add_argument("--min-inlier-ratio", type=float, default=0.5)
    sub.add_parser("self-test")
    try:
        ns = p.parse_args(args)
    except argparse.ArgumentError as e:
        raise ToolError("USAGE", str(e), exit_code=2) from e

    if ns.cmd == "self-test":
        return _self_test()
    if ns.cmd == "register":
        return register_arrays(load_gray(Path(ns.image_a)), load_gray(Path(ns.image_b)),
                               min_matches=ns.min_matches,
                               min_inlier_ratio=ns.min_inlier_ratio)
    if ns.cmd == "calibrate":
        return calibrate_scale(load_gray(Path(ns.image)), ns.marker_mm,
                               dict_name=ns.dict)
    if ns.cmd == "count":
        return count_components(load_gray(Path(ns.image)), threshold=ns.threshold,
                                invert=ns.invert, min_area=ns.min_area)
    if ns.cmd == "profile":
        return profile_skeleton(load_gray(Path(ns.image)), threshold=ns.threshold,
                                invert=ns.invert)
    root = Path(ns.root).resolve()
    if not root.is_dir():
        raise ToolError("NO_ROOT", f"not a directory: {root.as_posix()}", exit_code=2)
    return diff_mask(load_gray(Path(ns.image_a)), load_gray(Path(ns.image_b)),
                     root, ns.name, threshold=ns.threshold,
                     min_matches=ns.min_matches,
                     min_inlier_ratio=ns.min_inlier_ratio)


def _self_test() -> dict:
    """Synthetic register + count round trip - no files, no fixtures."""
    import cv2
    import numpy as np

    rng = np.random.default_rng(42)
    base = cv2.GaussianBlur((rng.random((300, 400)) * 255).astype(np.uint8),
                            (5, 5), 0)
    moved = cv2.warpAffine(base, np.float32([[1, 0, 8], [0, 1, -5]]), (400, 300))
    reg = register_arrays(base, moved)
    dx, dy = reg["translation"]
    shapes = np.full((100, 100), 230, dtype=np.uint8)
    shapes[10:30, 10:30] = 10
    counted = count_components(shapes)
    if abs(dx - 8) > 1 or abs(dy + 5) > 1 or counted["count"] != 1:
        raise ToolError("SELF_TEST", "measurement round trip out of tolerance",
                        detail={"translation": [dx, dy], "count": counted["count"]})
    return {"self_test": "pass"}


def main(args: list[str]) -> None:
    run_tool(TOOL, VERSION, handler, args)
