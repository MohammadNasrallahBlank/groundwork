from groundwork.tools.cartographer.extract import Symbol
from groundwork.tools.cartographer.render import estimate_tokens, render_text


def sym(name, file, kind="function", line=1):
    return Symbol(name, name, kind, line, "python", file)


def test_estimate_tokens_is_quarter_length():
    assert estimate_tokens("abcd") == 1
    assert estimate_tokens("a" * 40) == 10


def test_render_respects_budget_and_orders_by_rank():
    ranked = [(sym(f"s{i}", "a.py", line=i), 1.0 - i * 0.01) for i in range(50)]
    out = render_text(ranked, budget=40)
    assert out["est_tokens"] <= 40
    assert out["truncated"] is True
    assert out["symbols_shown"] < out["symbols_total"] == 50
    assert "s0" in out["map"]  # highest-ranked included
    assert "a.py" in out["map"]


def test_render_all_fits_not_truncated():
    ranked = [(sym("only", "a.py"), 1.0)]
    out = render_text(ranked, budget=10_000)
    assert out["truncated"] is False and out["symbols_shown"] == 1


def test_render_shows_at_least_one_symbol_even_if_over_budget():
    ranked = [(sym("verylongsymbolname", "some/deep/path/file.py", line=999), 1.0)]
    out = render_text(ranked, budget=1)
    assert out["symbols_shown"] == 1 and out["truncated"] is False
