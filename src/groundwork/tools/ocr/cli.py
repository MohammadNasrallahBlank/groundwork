import argparse
import re
from pathlib import Path

from groundwork.core.cache import Cache, cache_key
from groundwork.core.cliparse import UsageParser
from groundwork.core.runner import ToolError, run_tool
from groundwork.tools.ocr import engines
from groundwork.tools.ocr.reader import read_image

TOOL, VERSION = "ocr", "0.1.0"


def _region(spec: str) -> tuple[int, int, int, int]:
    m = re.fullmatch(r"(\d+),(\d+),(\d+),(\d+)", spec)
    if not m:
        raise ToolError("USAGE",
                        f"--region must look like x0,y0,x1,y1 (ints), got {spec!r}",
                        exit_code=2)
    return tuple(int(g) for g in m.groups())  # type: ignore[return-value]


def handler(args: list[str]) -> dict:
    p = UsageParser(prog=f"groundwork {TOOL}", exit_on_error=False)
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("read")
    r.add_argument("--image", required=True)
    r.add_argument("--region")
    r.add_argument("--engine", default="auto")
    r.add_argument("--no-cache", action="store_true")
    sub.add_parser("models")
    sub.add_parser("self-test")
    try:
        ns = p.parse_args(args)
    except argparse.ArgumentError as e:
        raise ToolError("USAGE", str(e), exit_code=2) from e

    if ns.cmd == "self-test":
        return _self_test()
    if ns.cmd == "models":
        return _models()

    region = _region(ns.region) if ns.region else None
    image = Path(ns.image)
    if ns.no_cache:
        return read_image(image, engine=ns.engine, region=region)
    if not image.is_file():  # key hashing needs the file; keep NO_IMAGE first
        raise ToolError("NO_IMAGE", f"no such image: {image.as_posix()}", exit_code=2)
    cache = Cache()
    key = cache_key(TOOL, VERSION,
                    {"engine": ns.engine, "region": list(region) if region else None},
                    files=[image])
    hit = cache.get(key)
    if hit is not None:
        return {**hit, "_cache": "hit"}
    out = read_image(image, engine=ns.engine, region=region)
    cache.put(key, out)
    return {**out, "_cache": "miss"}


def _models() -> dict:
    rapid = {"available": engines.rapidocr_available(), "models": []}
    if rapid["available"]:
        import rapidocr_onnxruntime
        pkg = Path(rapidocr_onnxruntime.__file__).parent
        rapid["models"] = [{"name": m.name, "bytes": m.stat().st_size}
                           for m in sorted(pkg.rglob("*.onnx"))]
        rapid["note"] = "models ship inside the wheel; nothing downloads at runtime"
    tess = {"available": engines.tesseract_available()}
    return {"rapidocr": rapid, "tesseract": tess}


def _self_test() -> dict:
    """Render text with Pillow's default font, OCR it, assert we can read."""
    import tempfile

    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGB", (640, 120), (255, 255, 255))
    d = ImageDraw.Draw(img)
    d.text((20, 20), "GROUNDWORK 42", fill=(0, 0, 0),
           font=ImageFont.load_default(size=48))
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "selftest.png"
        img.save(p)
        out = read_image(p)
    texts = " ".join(i["text"] for i in out["items"]).upper()
    if "GROUNDWORK" not in texts:
        raise ToolError("SELF_TEST",
                        f"engine {out['engine']} could not read rendered text",
                        detail=texts)
    return {"self_test": "pass"}


def main(args: list[str]) -> None:
    run_tool(TOOL, VERSION, handler, args)
