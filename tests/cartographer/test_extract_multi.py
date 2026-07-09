from pathlib import Path

import pytest

from groundwork.tools.cartographer.extract import extract
from groundwork.tools.cartographer.languages import load_spec

FIX = Path("tests/fixtures/cartomap_multi").resolve()

CASES = [
    ("java", "Sample.java", {"Sample", "add", "use"}, "add"),
    ("typescript", "sample.ts", {"Widget", "render", "build"}, "build"),
    ("javascript", "sample.js", {"Box", "open", "unlock"}, "unlock"),
    ("kotlin", "Sample.kt", {"Greeter", "greet", "build"}, "build"),
]


@pytest.mark.parametrize("lang,fname,want_symbols,want_ref", CASES)
def test_extract_language(lang, fname, want_symbols, want_ref):
    if load_spec(lang) is None:
        pytest.skip(f"{lang} grammar unavailable on this platform")
    path = FIX / fname
    symbols, refs = extract(path, path.read_bytes(), lang)
    assert want_symbols <= {s.name for s in symbols}
    assert want_ref in {r.name for r in refs}
