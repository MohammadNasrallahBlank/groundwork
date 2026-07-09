from groundwork.tools.depsurface.diffsurface import diff_snapshots, flatten


def make(version, sig, with_new=False):
    mods = {"pkg": {"doc": None, "exports": None, "attributes": {},
                    "classes": {"C": {"doc": None, "bases": [],
                                       "methods": {"m": {"sig": sig, "doc": None}},
                                       "attributes": {}}},
                    "functions": {"f": {"sig": "(x: int) -> int", "doc": None}},
                    "aliases": {"A": "pkg.sub.A"}}}
    if with_new:
        mods["pkg"]["functions"]["g"] = {"sig": "() -> None", "doc": None}
    return {"package": "pkg", "version": version, "language": "python",
            "modules": mods}


def test_flatten_paths_and_descriptors():
    flat = flatten(make("1", "(self) -> None"))
    assert flat["pkg.f"] == "function (x: int) -> int"
    assert flat["pkg.C"] == "class()"
    assert flat["pkg.C.m"] == "method (self) -> None"
    assert flat["pkg.A"] == "alias -> pkg.sub.A"


def test_diff_added_removed_changed():
    a = make("1", "(self) -> None")
    b = make("2", "(self, fast: bool = False) -> None", with_new=True)
    d = diff_snapshots(a, b)
    assert d["added"] == ["pkg.g"]
    assert d["removed"] == []
    assert d["changed"] == [{"symbol": "pkg.C.m",
                             "before": "method (self) -> None",
                             "after": "method (self, fast: bool = False) -> None"}]


def test_diff_identical_is_empty():
    a = make("1", "(self) -> None")
    d = diff_snapshots(a, a)
    assert d == {"added": [], "removed": [], "changed": []}
