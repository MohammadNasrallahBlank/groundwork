"""Generate the remaining complex-task fixtures for the full 22-tool A/B.

Deterministic. Creates data/code/image fixtures under eval/tasks/<id>/fixture/.
Git-based fixtures (gitwhy, bisector, covdiff) are built by per-task setup.py
run in the workdir at session time. Reuses eval/tasks/bigrepo for the code-intel
and guardrail tools.

    python eval/tasks/_gen_all.py
"""
import struct
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).parent


def w(rel: str, text: str) -> None:
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text.lstrip("\n"), encoding="utf-8", newline="\n")


def wb(rel: str, data: bytes) -> None:
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data)


# ---- datalens: a bigger, messier CSV --------------------------------------
def gen_datalensbig():
    import random
    rng = random.Random(42)
    regions = ["north", "south", "east", "west", "central"]
    rows = ["id,customer,amount,region,status"]
    for i in range(1, 301):
        amt = "" if i % 17 == 0 else f"{rng.uniform(10, 500):.2f}"
        if i == 150:
            amt = "8888888.00"                       # outlier
        region = rng.choice(regions)
        status = rng.choice(["paid", "pending", "refunded"])
        cust = f"cust_{rng.randint(1, 120)}"          # ~120 distinct customers
        rows.append(f"{i},{cust},{amt},{region},{status}")
    w("datalensbig/fixture/sales.csv", "\n".join(rows) + "\n")


# ---- scratchdb: two CSVs to join ------------------------------------------
def gen_scratchdb():
    customers = ["cid,name", "1,Acme", "2,Globex", "3,Initech", "4,Umbrella",
                 "5,Stark"]
    orders = ["oid,cid,total"]
    totals = {1: [900, 500], 2: [1200], 3: [300, 300, 300], 4: [50], 5: [100]}
    oid = 1
    for cid, ts in totals.items():
        for t in ts:
            orders.append(f"{oid},{cid},{t}")
            oid += 1
    w("scratchdb/fixture/customers.csv", "\n".join(customers) + "\n")
    w("scratchdb/fixture/orders.csv", "\n".join(orders) + "\n")


# ---- snipeval: a tricky snippet -------------------------------------------
def gen_snipeval():
    w("snipeval/fixture/snippet.py", '''
def build():
    out = []
    for i in range(5):
        out.append(lambda: i)          # classic late-binding closure gotcha
    return [f() for f in out]


print(build())
''')


# ---- propcheck: a function with a subtle property bug ---------------------
def gen_propcheck():
    w("propcheck/fixture/intervals.py", '''
def merge_intervals(intervals):
    """Merge overlapping [start, end] intervals. Has a subtle bug: it only
    merges when the next start is strictly LESS than the current end, so
    intervals that merely touch (next start == current end) are not merged."""
    if not intervals:
        return []
    xs = sorted(intervals)
    merged = [list(xs[0])]
    for s, e in xs[1:]:
        if s < merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], e)
        else:
            merged.append([s, e])
    return [tuple(m) for m in merged]
''')


# ---- mutcheck: code + a weak test -----------------------------------------
def gen_mutcheck():
    w("mutcheck/fixture/clamp.py", '''
def clamp(x, lo, hi):
    """Clamp x into [lo, hi]."""
    if x < lo:
        return lo
    if x > hi:
        return hi
    return x
''')
    w("mutcheck/fixture/test_clamp.py", '''
from clamp import clamp


def test_clamp_middle():
    assert clamp(5, 0, 10) == 5      # only tests the interior - boundaries
    assert clamp(-3, 0, 10) == 0     # and > hi are never tested, so a mutant
''')


# ---- verify (complex): a small lib with a subtle failing test -------------
def gen_verifybig():
    w("verifybig/fixture/stats.py", '''
def median(xs):
    """Median of a list. Bug: for even-length lists it returns the lower of
    the two middle values instead of their average."""
    s = sorted(xs)
    n = len(s)
    return s[n // 2] if n % 2 else s[n // 2 - 1]
''')
    w("verifybig/fixture/test_stats.py", '''
from stats import median


def test_odd():
    assert median([3, 1, 2]) == 2


def test_even():
    assert median([1, 2, 3, 4]) == 2.5     # fails: bug returns 2
''')


# ---- covdiff: lib + test, git built at setup ------------------------------
def gen_covdiff():
    w("covdiff/fixture/calc.py", '''
def add(a, b):
    return a + b


def subtract(a, b):
    return a - b


def divide(a, b):          # added later, NOT covered by the test suite
    if b == 0:
        raise ValueError("division by zero")
    return a / b
''')
    w("covdiff/fixture/test_calc.py", '''
from calc import add, subtract


def test_add():
    assert add(2, 3) == 5


def test_subtract():
    assert subtract(5, 2) == 3
''')


# ---- depsurface / patchgate / gates reuse bigrepo or tiny fixtures --------
def gen_gates():
    w("gatesbig/fixture/keep_me.txt", "important data - do not delete\n")
    w("gatesbig/fixture/README.md", "# sandbox repo\n")


def gen_patchgate():
    w("patchgatebig/fixture/config.py", '''
"""App configuration."""
DEBUG = False
TIMEOUT = 30
API_KEY = ""          # set via environment, never hardcode
''')


# ---- recordstore / ledger / hello / skillgen: minimal ---------------------
def gen_minimal():
    w("recordstorebig/fixture/README.md", "# deploy log\n")
    w("ledgerbig/fixture/README.md", "# predictions\n")
    w("hellobig/fixture/README.md", "# health check\n")
    w("skillgenbig/fixture/README.md", "# toolset docs\n")


# ---- gitwhy / bisector: setup scripts that build a git repo ---------------
def gen_git_setups():
    w("gitwhybig/fixture/setup.py", '''
"""Build a git repo whose pricing.py changed for a specific reason."""
import subprocess, sys
from pathlib import Path


def g(*a):
    subprocess.run(["git", *a], cwd=".", check=True,
                   capture_output=True, text=True)


g("init", "-q")
g("config", "user.email", "t@t"); g("config", "user.name", "t")
steps = [
    ("def apply_discount(price, pct):\\n    return price * (1 - pct / 100)\\n",
     "add discount helper"),
    ("def apply_discount(price, pct):\\n    return price * (1 - pct / 100)\\n\\n"
     "def format_price(p):\\n    return f'${p:.2f}'\\n", "add price formatter"),
    ("def apply_discount(price, pct):\\n    pct = max(0, min(pct, 100))"
     "  # clamp: a negative pct was inflating prices (#42)\\n"
     "    return price * (1 - pct / 100)\\n\\n"
     "def format_price(p):\\n    return f'${p:.2f}'\\n",
     "clamp discount pct to avoid negative-percent price inflation (#42)"),
]
for src, msg in steps:
    Path("pricing.py").write_text(src, encoding="utf-8")
    g("add", "-A"); g("commit", "-qm", msg)
print("gitwhy repo ready")
''')
    w("bisectorbig/fixture/setup.py", '''
"""Build a git repo with a regression introduced mid-history."""
import subprocess
from pathlib import Path


def g(*a):
    subprocess.run(["git", *a], cwd=".", check=True,
                   capture_output=True, text=True)


g("init", "-q")
g("config", "user.email", "t@t"); g("config", "user.name", "t")
for i in range(7):
    # commit 4 flips a boundary from <= to < : an off-by-one regression
    op = "<" if i >= 4 else "<="
    Path("range.py").write_text(
        f"def in_range(x, lo, hi):\\n    return lo <= x and x {op} hi\\n",
        encoding="utf-8")
    Path("test_range.py").write_text(
        "from range import in_range\\n"
        "def test_upper_inclusive():\\n    assert in_range(10, 0, 10) is True\\n",
        encoding="utf-8")
    g("add", "-A"); g("commit", "-qm", f"work item {i}")
print("bisector repo ready")
''')


# ---- images: hand-built PNGs (no PIL dependency in the fixture) -----------
def _png(width, height, pixels):
    """pixels: list of (r,g,b) rows. Minimal PNG encoder."""
    def chunk(typ, data):
        c = typ + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c))
    raw = b""
    for row in pixels:
        raw += b"\x00" + b"".join(struct.pack("3B", *px) for px in row)
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


def gen_imgmeasure():
    # 300x120 white canvas with a blue bar 180px wide, 40px tall at (20,40)
    W, H = 300, 120
    rows = []
    for y in range(H):
        row = []
        for x in range(W):
            if 40 <= y < 80 and 20 <= x < 200:      # blue bar width = 180
                row.append((0, 90, 220))
            else:
                row.append((255, 255, 255))
        rows.append(row)
    wb("imgmeasurebig/fixture/chart.png", _png(W, H, rows))


def gen_visdiff():
    base = ('<!doctype html><html><head><style>'
            'body{{font-family:sans-serif;margin:40px}}'
            '.btn{{background:{color};color:#fff;padding:12px 24px;'
            'border-radius:6px;display:inline-block}}</style></head>'
            '<body><h1>Checkout</h1><p>Total: $42.00</p>'
            '<div class="btn">{label}</div></body></html>')
    w("visdiffbig/fixture/before.html", base.format(color="#2b7", label="Pay now"))
    w("visdiffbig/fixture/after.html", base.format(color="#c33", label="Pay now"))


def main():
    for fn in (gen_datalensbig, gen_scratchdb, gen_snipeval, gen_propcheck,
               gen_mutcheck, gen_verifybig, gen_covdiff, gen_gates,
               gen_patchgate, gen_minimal, gen_git_setups, gen_imgmeasure,
               gen_visdiff):
        fn()
        print("ok", fn.__name__)
    # ocr: reuse a text-bearing image via imgmeasure-style is hard; use a PNG
    # of the word by rendering blocks is overkill - instead ship a tiny text
    # receipt as an image is skipped; ocr task uses a generated PIL image at
    # setup (see registry ocrbig setup).
    print("done")


if __name__ == "__main__":
    sys.exit(main())
