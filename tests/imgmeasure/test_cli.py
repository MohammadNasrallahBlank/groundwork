import json
import os
import subprocess

import numpy as np


def run_cli(*args, cwd=None):
    env = {**os.environ}
    return subprocess.run(["uv", "run", "groundwork", "imgmeasure", *args],
                          capture_output=True, text=True, env=env, cwd=cwd)


def test_register_round_trip(save_gray, textured, shift):
    base = textured()
    a = save_gray("a.png", base)
    b = save_gray("b.png", shift(base, 12.0, -7.0))
    p = run_cli("register", "--image-a", str(a), "--image-b", str(b))
    assert p.returncode == 0, p.stdout
    data = json.loads(p.stdout)["data"]
    dx, dy = data["translation"]
    assert abs(dx - 12.0) < 1.0 and abs(dy + 7.0) < 1.0


def test_register_blank_exits_4(save_gray):
    blank = np.full((200, 200), 255, dtype=np.uint8)
    a = save_gray("wa.png", blank)
    b = save_gray("wb.png", blank)
    p = run_cli("register", "--image-a", str(a), "--image-b", str(b))
    assert p.returncode == 4, p.stdout
    assert json.loads(p.stdout)["error"]["code"] == "UNRELIABLE_REGISTRATION"


def test_calibrate_round_trip(save_gray, marker_canvas):
    img = save_gray("m.png", marker_canvas(side=120))
    p = run_cli("calibrate", "--image", str(img), "--marker-mm", "60")
    assert p.returncode == 0, p.stdout
    assert json.loads(p.stdout)["data"]["mm_per_px"] > 0


def test_count_round_trip(save_gray):
    img = np.full((100, 100), 230, dtype=np.uint8)
    img[10:30, 10:30] = 10
    img[50:90, 50:90] = 10
    p = run_cli("count", "--image", str(save_gray("c.png", img)))
    assert p.returncode == 0, p.stdout
    assert json.loads(p.stdout)["data"]["count"] == 2


def test_diffmask_writes_artifact(save_gray, textured, shift, tmp_path):
    base = textured()
    changed = shift(base, 6.0, 3.0)
    changed[200:240, 300:360] = 0
    a = save_gray("da.png", base)
    b = save_gray("db.png", changed)
    p = run_cli("diffmask", "--image-a", str(a), "--image-b", str(b),
                "--name", "cli-case", "--root", str(tmp_path), cwd=str(tmp_path))
    assert p.returncode == 0, p.stdout
    data = json.loads(p.stdout)["data"]
    assert (tmp_path / ".groundwork" / "imgmeasure" / "cli-case-mask.png").exists()
    assert data["regions"]


def test_missing_image_exits_2(tmp_path):
    p = run_cli("count", "--image", str(tmp_path / "nope.png"))
    assert p.returncode == 2
    assert json.loads(p.stdout)["error"]["code"] == "NO_IMAGE"


def test_self_test():
    p = run_cli("self-test")
    assert p.returncode == 0, p.stdout
    assert json.loads(p.stdout)["data"]["self_test"] == "pass"
