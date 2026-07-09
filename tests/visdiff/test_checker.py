from pathlib import Path

import pytest

from groundwork.core.runner import ToolError
from groundwork.tools.visdiff import store
from groundwork.tools.visdiff.capture import browser_available
from groundwork.tools.visdiff.checker import approve, run_check, set_baseline

FIX = Path("tests/fixtures/visdiff").resolve()

requires_browser = pytest.mark.skipif(
    not browser_available(),
    reason="chromium not installed (run: groundwork visdiff install-browser)")


@pytest.fixture(autouse=True)
def _isolated_store(tmp_path, monkeypatch):
    monkeypatch.setenv("GROUNDWORK_DATA_DIR", str(tmp_path / "data"))


def test_check_without_baseline_escalates(tmp_path):
    with pytest.raises(ToolError) as ei:
        run_check("nobase", (FIX / "page.html").as_uri(), tmp_path,
                  viewport=(640, 480), full_page=False, masks=(), timeout_s=30,
                  min_ssim=0.995, max_diff_ratio=0.001)
    assert ei.value.code == "NO_BASELINE" and ei.value.exit_code == 4


@requires_browser
def test_same_page_passes(tmp_path):
    url = (FIX / "page.html").as_uri()
    set_baseline("home", url, tmp_path, viewport=(640, 480), full_page=False,
                 masks=(), timeout_s=30)
    out = run_check("home", url, tmp_path, viewport=(640, 480), full_page=False,
                    masks=(), timeout_s=30, min_ssim=0.995, max_diff_ratio=0.001)
    assert out["passed"] is True and "_exit_override" not in out
    assert out["regions"] == []
    assert "\\" not in out["actual_path"] and "\\" not in out["composite_path"]


@requires_browser
def test_changed_page_fails_with_regions_and_artifacts(tmp_path):
    set_baseline("home", (FIX / "page.html").as_uri(), tmp_path,
                 viewport=(640, 480), full_page=False, masks=(), timeout_s=30)
    out = run_check("home", (FIX / "changed.html").as_uri(), tmp_path,
                    viewport=(640, 480), full_page=False, masks=(), timeout_s=30,
                    min_ssim=0.995, max_diff_ratio=0.001)
    assert out["passed"] is False and out["_exit_override"] == 1
    assert len(out["regions"]) >= 1
    assert Path(out["composite_path"]).exists()
    assert Path(out["actual_path"]).exists()


@requires_browser
def test_masked_volatile_region_passes(tmp_path):
    # page vs changed differ in BOTH .card and #volatile; masking #volatile
    # still fails (card changed), but masking is proven by the volatile region
    # not appearing among the diff regions' pixels.
    url_a = (FIX / "page.html").as_uri()
    url_b = (FIX / "changed.html").as_uri()
    set_baseline("m", url_a, tmp_path, viewport=(640, 480), full_page=False,
                 masks=("#volatile",), timeout_s=30)
    out = run_check("m", url_b, tmp_path, viewport=(640, 480), full_page=False,
                    masks=("#volatile",), timeout_s=30,
                    min_ssim=0.995, max_diff_ratio=0.001)
    # volatile box lives at y≈248..288 (third block); card at y≈152..232.
    # All regions must sit above the volatile band.
    assert all(r["bbox"][3] <= 248 for r in out["regions"])


@requires_browser
def test_approve_promotes_last_actual(tmp_path):
    url_a = (FIX / "page.html").as_uri()
    url_b = (FIX / "changed.html").as_uri()
    set_baseline("home", url_a, tmp_path, viewport=(640, 480), full_page=False,
                 masks=(), timeout_s=30)
    run_check("home", url_b, tmp_path, viewport=(640, 480), full_page=False,
              masks=(), timeout_s=30, min_ssim=0.995, max_diff_ratio=0.001)
    approved = approve("home", tmp_path)
    assert approved["platform_key"] == store.platform_key()
    out = run_check("home", url_b, tmp_path, viewport=(640, 480), full_page=False,
                    masks=(), timeout_s=30, min_ssim=0.995, max_diff_ratio=0.001)
    assert out["passed"] is True


def test_approve_without_prior_check_errors(tmp_path):
    with pytest.raises(ToolError) as ei:
        approve("never-checked", tmp_path)
    assert ei.value.code == "NO_CAPTURE" and ei.value.exit_code == 1
