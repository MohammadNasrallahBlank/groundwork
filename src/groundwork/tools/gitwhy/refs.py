"""Extract typed PR/issue references (#<n>) from a commit message."""
import re

_REF = re.compile(r"#(\d+)")
_CLOSING = re.compile(
    r"\b(fix(?:es|ed)?|close(?:s|d)?|resolve(?:s|d)?)\b[\s:]*#(\d+)", re.I)


def extract_refs(message: str) -> list[dict]:
    """All #<n> refs, deduped; closing (Fixes/Closes/Resolves) wins over mention."""
    closing = {int(n) for _kw, n in _CLOSING.findall(message)}
    all_nums = {int(n) for n in _REF.findall(message)}
    return [{"number": n, "closing": n in closing} for n in sorted(all_nums)]
