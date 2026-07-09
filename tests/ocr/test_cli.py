import json
import os
import subprocess

import pytest


def run_cli(*args, cache_dir):
    env = {**os.environ, "GROUNDWORK_CACHE_DIR": str(cache_dir)}
    return subprocess.run(["uv", "run", "groundwork", "ocr", *args],
                          capture_output=True, text=True, env=env)


@pytest.fixture()
def text_png(tmp_path, render_text):
    p = tmp_path / "t.png"
    render_text(["GROUNDWORK 42"]).save(p)
    return p


def test_read_emits_envelope_and_caches(text_png, tmp_path):
    c = tmp_path / "cache"
    p1 = run_cli("read", "--image", str(text_png), cache_dir=c)
    assert p1.returncode == 0, p1.stdout
    out1 = json.loads(p1.stdout)
    assert out1["ok"] and out1["meta"]["cache"] == "miss"
    assert any("GROUNDWORK" in i["text"].upper() for i in out1["data"]["items"])
    p2 = run_cli("read", "--image", str(text_png), cache_dir=c)
    out2 = json.loads(p2.stdout)
    assert out2["meta"]["cache"] == "hit"
    assert out2["data"] == out1["data"]


def test_region_flag_parses_and_filters(text_png, tmp_path):
    p = run_cli("read", "--image", str(text_png), "--region", "0,0,640,60",
                cache_dir=tmp_path / "c")
    assert p.returncode == 0, p.stdout
    assert json.loads(p.stdout)["data"]["region"] == [0, 0, 640, 60]


def test_bad_region_format_is_usage(text_png, tmp_path):
    p = run_cli("read", "--image", str(text_png), "--region", "banana",
                cache_dir=tmp_path / "c")
    assert p.returncode == 2
    assert json.loads(p.stdout)["error"]["code"] == "USAGE"


def test_missing_image_exits_2(tmp_path):
    p = run_cli("read", "--image", str(tmp_path / "nope.png"),
                cache_dir=tmp_path / "c")
    assert p.returncode == 2
    assert json.loads(p.stdout)["error"]["code"] == "NO_IMAGE"


def test_models_reports_bundled_onnx_and_tesseract(tmp_path):
    p = run_cli("models", cache_dir=tmp_path / "c")
    assert p.returncode == 0
    data = json.loads(p.stdout)["data"]
    assert data["rapidocr"]["available"] is True
    assert len(data["rapidocr"]["models"]) >= 3
    assert all("name" in m and "bytes" in m for m in data["rapidocr"]["models"])
    assert isinstance(data["tesseract"]["available"], bool)


def test_self_test(tmp_path):
    p = run_cli("self-test", cache_dir=tmp_path / "c")
    assert p.returncode == 0, p.stdout
    assert json.loads(p.stdout)["data"]["self_test"] == "pass"
