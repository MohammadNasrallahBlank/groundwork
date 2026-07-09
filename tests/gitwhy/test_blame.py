from groundwork.tools.gitwhy.blame import parse_porcelain, unique_commits

_PORC = """abc123 1 1 1
author Alice
author-mail <a@x>
author-time 1700000000
author-tz +0000
committer Alice
committer-mail <a@x>
committer-time 1700000000
committer-tz +0000
summary feat: first
filename mod.py
\tdef a():
def456 2 2 1
author Bob
author-mail <b@x>
author-time 1700001000
author-tz +0000
committer Bob
committer-mail <b@x>
committer-time 1700001000
committer-tz +0000
summary fix: second (#7)
filename mod.py
\t    return 2
"""


def test_parse_porcelain_extracts_per_line():
    lines = parse_porcelain(_PORC)
    assert len(lines) == 2
    assert lines[0]["sha"] == "abc123" and lines[0]["author"] == "Alice"
    assert lines[0]["summary"] == "feat: first"
    assert lines[1]["sha"] == "def456" and lines[1]["author"] == "Bob"
    assert lines[1]["author_time"] == 1700001000


def test_unique_commits_dedupes_by_sha():
    lines = parse_porcelain(_PORC) + parse_porcelain(_PORC)   # duplicated region
    commits = unique_commits(lines)
    assert len(commits) == 2 and {c["sha"] for c in commits} == {"abc123", "def456"}


def test_parse_empty_is_empty():
    assert parse_porcelain("") == []
