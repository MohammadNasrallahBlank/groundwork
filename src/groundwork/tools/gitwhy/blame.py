"""Parse `git blame --porcelain` output into per-line commit attribution."""


def _looks_like_sha(s: str) -> bool:
    return len(s) >= 6 and all(c in "0123456789abcdef" for c in s.lower())


def parse_porcelain(text: str) -> list[dict]:
    """Per attributed line: {sha, author, author_time, summary}."""
    lines = []
    cur = None
    for raw in text.splitlines():
        if raw.startswith("\t"):                 # the code line ends a block
            if cur is not None:
                lines.append(cur)
                cur = None
            continue
        parts = raw.split(" ", 1)
        head = parts[0]
        # a header line starts a new block: "<hex> <orig> <final> [n]"
        if cur is None and _looks_like_sha(head) and len(raw.split()) >= 3:
            cur = {"sha": head, "author": None, "author_time": None,
                   "summary": None}
            continue
        if cur is None:
            continue
        val = parts[1] if len(parts) > 1 else ""
        if head == "author":
            cur["author"] = val
        elif head == "author-time":
            cur["author_time"] = int(val) if val.isdigit() else None
        elif head == "summary":
            cur["summary"] = val
    return lines


def unique_commits(lines: list[dict]) -> list[dict]:
    """Dedupe by sha, keeping the first-seen author/time/summary."""
    seen, out = set(), []
    for ln in lines:
        if ln["sha"] in seen:
            continue
        seen.add(ln["sha"])
        out.append({"sha": ln["sha"], "author": ln["author"],
                    "author_time": ln["author_time"], "summary": ln["summary"]})
    return out
