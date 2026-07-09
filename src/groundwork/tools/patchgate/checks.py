"""Post-image syntax validation ladder, keyed by file extension. Pure."""
import json
from pathlib import PurePosixPath

# .py deliberately uses compile(): Python's own parser is the truth (precise
# line/offset, no error recovery). tree-sitter covers the rest of the
# cartographer language set; a grammar that fails to load degrades to pass.
_TS_LANGS = {".js": "javascript", ".ts": "typescript", ".tsx": "tsx",
             ".java": "java", ".kt": "kotlin"}


def _result(file: str, checked: bool, ok: bool, checker, error) -> dict:
    return {"file": file, "checked": checked, "ok": ok,
            "checker": checker, "error": error}


def _check_treesitter(file: str, source: str, lang: str) -> dict:
    try:
        from tree_sitter import Parser
        from tree_sitter_language_pack import get_language
        parser = Parser(get_language(lang))
    except Exception:
        # grammar unavailable on this platform: the gate must not become a wall
        return _result(file, False, True, None, None)
    tree = parser.parse(source.encode("utf-8"))
    if tree.root_node.has_error:
        return _result(file, True, False, "tree-sitter",
                       f"{lang} parse error (tree contains ERROR nodes)")
    return _result(file, True, True, "tree-sitter", None)


def check_content(path_like: str, source: str) -> dict:
    """Validate proposed file content by extension; unknown types pass."""
    file = PurePosixPath(path_like.replace("\\", "/")).as_posix()
    suffix = PurePosixPath(file).suffix.lower()
    if suffix == ".py":
        try:
            compile(source, file, "exec")
        except SyntaxError as e:
            return _result(file, True, False, "compile",
                           f"{e.msg} (line {e.lineno})")
        except ValueError as e:  # e.g. source with null bytes
            return _result(file, True, False, "compile", str(e))
        return _result(file, True, True, "compile", None)
    if suffix == ".json":
        try:
            json.loads(source)
        except json.JSONDecodeError as e:
            return _result(file, True, False, "json",
                           f"{e.msg} (line {e.lineno} col {e.colno})")
        return _result(file, True, True, "json", None)
    if suffix in _TS_LANGS:
        return _check_treesitter(file, source, _TS_LANGS[suffix])
    return _result(file, False, True, None, None)
