import argparse
from pathlib import Path

from groundwork.core.cliparse import UsageParser
from groundwork.core.runner import ToolError, run_tool
from groundwork.tools.codemod.applier import apply_plan
from groundwork.tools.codemod.astgrep import LANG_GLOBS
from groundwork.tools.codemod.combyengine import comby_available
from groundwork.tools.codemod.planner import build_plan
from groundwork.tools.codemod.presets import PRESETS

TOOL, VERSION = "codemod", "0.1.0"
_ENGINES = ("ast-grep", "comby")


def handler(args: list[str]) -> dict:
    p = UsageParser(prog=f"groundwork {TOOL}", exit_on_error=False)
    sub = p.add_subparsers(dest="cmd", required=True)
    pl = sub.add_parser("plan")
    pl.add_argument("--engine", default="ast-grep")
    pl.add_argument("--pattern")
    pl.add_argument("--rewrite")
    pl.add_argument("--lang")
    pl.add_argument("--preset")
    pl.add_argument("--glob")
    pl.add_argument("--root", default=".")
    ap = sub.add_parser("apply")
    ap.add_argument("--plan", required=True)
    ap.add_argument("--root", default=".")
    ap.add_argument("--no-verify", action="store_true")
    sub.add_parser("presets")
    sub.add_parser("self-test")
    try:
        ns = p.parse_args(args)
    except argparse.ArgumentError as e:
        raise ToolError("USAGE", str(e), exit_code=2) from e

    if ns.cmd == "self-test":
        return _self_test()
    if ns.cmd == "presets":
        return {"presets": PRESETS,
                "engines": {"ast-grep": True, "preset": True,
                            "comby": comby_available()}}

    root = Path(ns.root).resolve()
    if not root.is_dir():
        raise ToolError("NO_ROOT", f"not a directory: {root.as_posix()}", exit_code=2)
    if ns.cmd == "apply":
        return apply_plan(root, ns.plan, no_verify=ns.no_verify)

    engine = "preset" if ns.preset else ns.engine
    if engine == "preset":
        if ns.pattern or ns.rewrite:
            raise ToolError("USAGE", "--preset does not take --pattern/--rewrite",
                            exit_code=2)
    elif engine not in _ENGINES:
        raise ToolError("USAGE", f"--engine must be one of {_ENGINES} "
                                 f"(or use --preset), got {engine!r}", exit_code=2)
    elif not ns.pattern or not ns.rewrite:
        raise ToolError("USAGE", f"--engine {engine} requires --pattern and --rewrite",
                        exit_code=2)
    elif engine == "ast-grep" and ns.lang not in LANG_GLOBS:
        raise ToolError("USAGE", f"--engine ast-grep requires --lang, one of "
                                 f"{sorted(LANG_GLOBS)}", exit_code=2)
    elif engine == "comby" and not ns.glob:
        raise ToolError("USAGE", "--engine comby requires --glob", exit_code=2)
    return build_plan(root, engine=engine, pattern=ns.pattern, rewrite=ns.rewrite,
                      lang=ns.lang, preset=ns.preset, glob=ns.glob)


def _self_test() -> dict:
    """In-memory engine round trips - no files, no git."""
    from groundwork.tools.codemod.astgrep import rewrite_source
    from groundwork.tools.codemod.presets import run_preset

    out, count = rewrite_source("print(1)\n", "python", "print($A)", "log($A)")
    fstr, _ = run_preset('x = "hi {}".format(n)\n', "py-fstringify")
    if count != 1 or out != "log(1)\n" or 'f"hi {n}"' not in fstr:
        raise ToolError("SELF_TEST", "engine round trip failed",
                        detail={"astgrep": out, "preset": fstr})
    return {"self_test": "pass"}


def main(args: list[str]) -> None:
    run_tool(TOOL, VERSION, handler, args)
