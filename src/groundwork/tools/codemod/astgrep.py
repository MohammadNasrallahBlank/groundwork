"""Engine 1: official ast-grep bindings, in-process, metavariable rewrites."""
import re

from ast_grep_py import SgRoot

LANG_GLOBS = {"python": "**/*.py", "javascript": "**/*.js",
              "typescript": "**/*.ts", "tsx": "**/*.tsx",
              "java": "**/*.java", "kotlin": "**/*.kt"}

_METAVAR = re.compile(r"\$([A-Z_][A-Z0-9_]*)")


def rewrite_source(source: str, lang: str, pattern: str, rewrite: str) -> tuple[str, int]:
    """Apply pattern -> rewrite across source; returns (new_source, match_count).

    $METAVAR names in `rewrite` are substituted from each match; an unmatched
    metavariable is left verbatim so the mistake is visible in the diff.
    """
    try:
        root = SgRoot(source, lang).root()
    except Exception as e:  # bindings raise on grammar-level failures
        raise ValueError(f"ast-grep could not parse source as {lang}: {e}") from e
    hits = root.find_all(pattern=pattern)
    if not hits:
        return source, 0
    edits = []
    for h in hits:
        def _sub(m, hit=h):
            got = hit.get_match(m.group(1))
            return got.text() if got is not None else m.group(0)
        edits.append(h.replace(_METAVAR.sub(_sub, rewrite)))
    return root.commit_edits(edits), len(hits)
