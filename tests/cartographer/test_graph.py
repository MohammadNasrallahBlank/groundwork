from groundwork.tools.cartographer.extract import Reference, Symbol
from groundwork.tools.cartographer.graph import rank_symbols


def sym(name, file="a.py", kind="function", line=1):
    return Symbol(name, name, kind, line, "python", file)


def test_more_referenced_symbol_ranks_higher():
    symbols = [sym("popular"), sym("caller1"), sym("caller2"), sym("lonely")]
    refs = [Reference("popular", 2, "a.py"), Reference("popular", 3, "a.py")]
    ranked = rank_symbols(symbols, refs)
    names = [s.name for s, _ in ranked]
    assert names[0] == "popular"
    assert names.index("popular") < names.index("lonely")


def test_rank_is_deterministic_and_scores_sum_reasonably():
    symbols = [sym("a"), sym("b"), sym("c")]
    refs = [Reference("a", 1, "x.py"), Reference("b", 1, "x.py")]
    r1 = rank_symbols(symbols, refs)
    r2 = rank_symbols(symbols, refs)
    assert [s.name for s, _ in r1] == [s.name for s, _ in r2]
    assert abs(sum(score for _, score in r1) - 1.0) < 1e-6


def test_empty_input():
    assert rank_symbols([], []) == []


def test_reference_matches_scoped_symbol_by_bare_name():
    # A method's qualified_name is dotted, but call sites reference the bare name.
    # The edge must still form, or centrality is meaningless for real code.
    caller = Symbol("run", "App.run", "method", 1, "python", "a.py")
    target = Symbol("format", "Formatter.format", "method", 5, "python", "a.py")
    lonely = Symbol("unused", "Formatter.unused", "method", 9, "python", "a.py")
    symbols = [caller, target, lonely]
    refs = [Reference("format", 2, "a.py"), Reference("format", 3, "a.py")]
    ranked = rank_symbols(symbols, refs)
    names = [s.qualified_name for s, _ in ranked]
    assert names[0] == "Formatter.format"   # referenced method ranks top
    assert names.index("Formatter.format") < names.index("Formatter.unused")
