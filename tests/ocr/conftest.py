"""Shared OCR test helper. Lives in conftest because tests/ is not an
importable package in this repo — cross-test-module imports do not resolve."""
import pytest
from PIL import Image, ImageDraw, ImageFont


def render_text_png(lines: list[str], size: int = 48) -> Image.Image:
    img = Image.new("RGB", (640, 80 * len(lines) + 40), (255, 255, 255))
    d = ImageDraw.Draw(img)
    font = ImageFont.load_default(size=size)
    for i, line in enumerate(lines):
        d.text((20, 20 + 80 * i), line, fill=(0, 0, 0), font=font)
    return img


@pytest.fixture()
def render_text():
    return render_text_png
