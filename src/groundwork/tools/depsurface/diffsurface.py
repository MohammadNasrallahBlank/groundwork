"""Flatten snapshots to symbol->descriptor maps; diff = set algebra over them."""


def flatten(snapshot: dict) -> dict[str, str]:
    flat: dict[str, str] = {}
    for mpath, mod in snapshot["modules"].items():
        for name, fn in mod["functions"].items():
            flat[f"{mpath}.{name}"] = f"function {fn['sig']}"
        for name, attr in mod["attributes"].items():
            flat[f"{mpath}.{name}"] = f"attribute {attr['annotation'] or ''}".rstrip()
        for name, target in mod["aliases"].items():
            flat[f"{mpath}.{name}"] = f"alias -> {target}"
        for name, cls in mod["classes"].items():
            cpath = f"{mpath}.{name}"
            flat[cpath] = f"class({', '.join(cls['bases'])})"
            for mname, fn in cls["methods"].items():
                flat[f"{cpath}.{mname}"] = f"method {fn['sig']}"
            for aname, attr in cls["attributes"].items():
                flat[f"{cpath}.{aname}"] = f"attribute {attr['annotation'] or ''}".rstrip()
    return flat


def diff_snapshots(a: dict, b: dict) -> dict:
    fa, fb = flatten(a), flatten(b)
    changed = sorted(k for k in fa.keys() & fb.keys() if fa[k] != fb[k])
    return {"added": sorted(fb.keys() - fa.keys()),
            "removed": sorted(fa.keys() - fb.keys()),
            "changed": [{"symbol": k, "before": fa[k], "after": fb[k]}
                        for k in changed]}
