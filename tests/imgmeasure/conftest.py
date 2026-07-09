"""Synthetic-image fixtures. Seeded, no committed binaries."""
from pathlib import Path

import cv2
import numpy as np
import pytest


def _textured() -> np.ndarray:
    rng = np.random.default_rng(42)
    img = (rng.random((400, 600)) * 255).astype(np.uint8)
    return cv2.GaussianBlur(img, (5, 5), 0)


def _shift(img: np.ndarray, dx: float, dy: float) -> np.ndarray:
    m = np.float32([[1, 0, dx], [0, 1, dy]])
    return cv2.warpAffine(img, m, (img.shape[1], img.shape[0]))


def _marker_canvas(marker_id: int = 7, side: int = 120) -> np.ndarray:
    d = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    marker = cv2.aruco.generateImageMarker(d, marker_id, side)
    canvas = np.full((400, 400), 255, dtype=np.uint8)
    canvas[100:100 + side, 150:150 + side] = marker
    return canvas


@pytest.fixture()
def textured():
    return _textured


@pytest.fixture()
def shift():
    return _shift


@pytest.fixture()
def marker_canvas():
    return _marker_canvas


@pytest.fixture()
def save_gray(tmp_path):
    def _save(name: str, img: np.ndarray) -> Path:
        ok, buf = cv2.imencode(".png", img)
        assert ok
        p = tmp_path / name
        p.write_bytes(buf.tobytes())
        return p
    return _save
