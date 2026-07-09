import ast

from groundwork.tools.mutcheck.mutate import iter_mutants, mutation_points


def test_comparison_swap_lt_to_lte():
    src = "def f(x):\n    return x < 10\n"
    muts = iter_mutants(src, {2})
    assert len(muts) == 1
    m = muts[0]
    assert m.line == 2 and "Lt" in m.description and "LtE" in m.description
    assert "x <= 10" in m.source
    ast.parse(m.source)                     # mutant is valid Python


def test_arithmetic_and_bool_and_const_mutations():
    src = ("def g(a, b, flag):\n"
           "    total = a + b\n"           # Add -> Sub
           "    ok = flag and True\n"      # And -> Or, True -> False
           "    return total, ok\n")
    descs = {m.description for m in iter_mutants(src, {2, 3, 4})}
    assert any("Add" in d and "Sub" in d for d in descs)
    assert any("And" in d and "Or" in d for d in descs)
    assert any("True" in d and "False" in d for d in descs)


def test_only_changed_lines_are_mutated():
    src = "def f(x):\n    a = x < 1\n    b = x > 2\n    return a, b\n"
    muts = iter_mutants(src, {2})           # only line 2 changed
    assert len(muts) == 1 and muts[0].line == 2


def test_no_mutable_nodes_is_empty():
    src = "def f(x):\n    return x\n"
    assert iter_mutants(src, {2}) == []


def test_mutation_points_counts_without_generating():
    src = "def f(x):\n    return x < 1 or x > 9\n"
    pts = mutation_points(src, {2})
    # two comparisons + one bool-op on line 2
    assert len(pts) == 3 and all(p["line"] == 2 for p in pts)


def test_each_mutant_changes_exactly_one_node():
    src = "def f(x):\n    return (x < 1) and (x > 9)\n"
    muts = iter_mutants(src, {2})
    # one mutant flips Lt, another flips Gt, another flips And - each distinct
    sources = {m.source for m in muts}
    assert len(sources) == len(muts) >= 3
