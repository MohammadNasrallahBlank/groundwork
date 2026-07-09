from groundwork.tools.gitwhy.refs import extract_refs


def test_plain_mention_is_non_closing():
    refs = extract_refs("see #42 for context")
    assert refs == [{"number": 42, "closing": False}]


def test_closing_keywords_mark_closing():
    for msg in ("Fixes #7", "closed #7", "Resolves #7", "fix #7"):
        assert extract_refs(msg) == [{"number": 7, "closing": True}], msg


def test_closing_wins_over_mention_when_deduped():
    refs = extract_refs("mentions #9 and later Fixes #9")
    assert refs == [{"number": 9, "closing": True}]


def test_multiple_refs_sorted():
    refs = extract_refs("Closes #12, also #3 and #30")
    assert [r["number"] for r in refs] == [3, 12, 30]


def test_bare_numbers_are_not_refs():
    assert extract_refs("bumped to version 5 in 2026") == []
