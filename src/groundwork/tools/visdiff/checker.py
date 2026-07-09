"""Orchestration: capture -> baseline -> diff -> verdict + artifacts."""
from pathlib import Path

from groundwork.core.envelope import EXIT_ESCALATE
from groundwork.core.runner import ToolError
from groundwork.tools.visdiff import store
from groundwork.tools.visdiff.capture import capture_png
from groundwork.tools.visdiff.diffengine import composite, diff_images


def _artifact_dir(root: Path, name: str) -> Path:
    d = root / ".groundwork" / "visdiff" / name
    d.mkdir(parents=True, exist_ok=True)
    return d


def set_baseline(name: str, url: str, root: Path, *, viewport: tuple[int, int],
                 full_page: bool, masks: tuple[str, ...], timeout_s: int) -> dict:
    """Capture the page now and store it as this platform's baseline."""
    key = store.platform_key()
    png, info = capture_png(url, viewport=viewport, full_page=full_page,
                            masks=masks, timeout_s=timeout_s)
    meta = {"url": url, "viewport": info["viewport"], "full_page": full_page,
            "masks": sorted(masks), "browser_version": info["browser_version"]}
    p = store.save_baseline(name, key, png, meta)
    return {"name": name, "platform_key": key, "baseline_path": p.as_posix(),
            "viewport": info["viewport"]}


def run_check(name: str, url: str, root: Path, *, viewport: tuple[int, int],
              full_page: bool, masks: tuple[str, ...], timeout_s: int,
              min_ssim: float, max_diff_ratio: float) -> dict:
    """Capture, diff against the stored baseline, write artifacts, verdict."""
    key = store.platform_key()
    found = store.load_baseline(name, key)
    if found is None:
        have = [b for b in store.list_baselines() if b["name"] == name]
        raise ToolError(
            "NO_BASELINE",
            f"no baseline '{name}' for platform key '{key}'; "
            f"run: groundwork visdiff baseline --name {name} --url <url>",
            exit_code=EXIT_ESCALATE,
            detail={"available": have[0]["keys"] if have else []})
    baseline_png, _meta = found
    actual_png, _info = capture_png(url, viewport=viewport, full_page=full_page,
                                    masks=masks, timeout_s=timeout_s)
    d = diff_images(baseline_png, actual_png)

    art = _artifact_dir(Path(root), name)
    actual_path = art / f"actual-{key}.png"
    actual_path.write_bytes(actual_png)
    composite_path = art / f"composite-{key}.png"
    composite_path.write_bytes(composite(baseline_png, actual_png, d["diff_png"]))

    passed = (not d["size_mismatch"] and d["ssim"] >= min_ssim
              and d["pixel_diff_ratio"] <= max_diff_ratio)
    out = {"name": name, "url": url, "platform_key": key, "passed": passed,
           "size_mismatch": d["size_mismatch"], "ssim": d["ssim"],
           "pixel_diff_count": d["pixel_diff_count"],
           "pixel_diff_ratio": d["pixel_diff_ratio"], "regions": d["regions"],
           "thresholds": {"min_ssim": min_ssim, "max_diff_ratio": max_diff_ratio},
           "actual_path": actual_path.as_posix(),
           "composite_path": composite_path.as_posix()}
    if not passed:
        out["_exit_override"] = 1
    return out


def approve(name: str, root: Path) -> dict:
    """Promote the last check's actual capture to the new baseline."""
    key = store.platform_key()
    actual = Path(root) / ".groundwork" / "visdiff" / name / f"actual-{key}.png"
    if not actual.exists():
        raise ToolError(
            "NO_CAPTURE",
            f"nothing to approve: no prior check artifact at {actual.as_posix()}; "
            f"run: groundwork visdiff check --name {name} --url <url>",
            exit_code=1)
    prior = store.load_baseline(name, key)
    meta = prior[1] if prior else {}
    meta["approved_from"] = actual.as_posix()
    p = store.save_baseline(name, key, actual.read_bytes(), meta)
    return {"name": name, "platform_key": key, "baseline_path": p.as_posix()}
