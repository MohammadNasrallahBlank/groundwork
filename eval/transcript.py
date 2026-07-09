"""Shared helpers for reading a Claude Code session transcript (JSONL)."""
import json
from pathlib import Path


def load(path: Path, *, since=None, until=None):
    """Yield the JSON records of a session, optionally within a time window."""
    with Path(path).open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                o = json.loads(line)
            except json.JSONDecodeError:
                continue
            ts = o.get("timestamp")
            if since and ts and ts < since:
                continue
            if until and ts and ts > until:
                continue
            yield o


def final_answer(path: Path, *, since=None, until=None) -> str:
    """The text of the last assistant turn — Claude's concluding answer.

    Concatenates the text blocks of every assistant message that shares the
    last assistant message's requestId, so a multi-block final answer is
    captured whole.
    """
    records = [o for o in load(path, since=since, until=until)
               if o.get("type") == "assistant"]
    if not records:
        return ""
    last_req = records[-1].get("requestId")
    texts: list[str] = []
    for o in records:
        if last_req and o.get("requestId") != last_req:
            continue
        content = (o.get("message") or {}).get("content")
        if isinstance(content, list):
            for c in content:
                if isinstance(c, dict) and c.get("type") == "text":
                    texts.append(c.get("text", ""))
        elif isinstance(content, str):
            texts.append(content)
    return "\n".join(texts).strip()


def all_assistant_text(path: Path, *, since=None, until=None) -> str:
    """Every assistant text block joined — for checks that accept evidence
    anywhere in the transcript, not only the final answer."""
    out: list[str] = []
    for o in load(path, since=since, until=until):
        if o.get("type") != "assistant":
            continue
        content = (o.get("message") or {}).get("content")
        if isinstance(content, list):
            for c in content:
                if isinstance(c, dict) and c.get("type") == "text":
                    out.append(c.get("text", ""))
    return "\n".join(out)
