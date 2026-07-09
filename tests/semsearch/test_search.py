import pytest

from groundwork.tools.semsearch import _DEFAULT_MODEL
from groundwork.tools.semsearch.index import (build_index,
                                              loadable_extensions_available)
from groundwork.tools.semsearch.search import _similarity, search

requires_vec = pytest.mark.skipif(
    not loadable_extensions_available(),
    reason="Python built without loadable SQLite extensions (sqlite-vec unavailable)")


@pytest.fixture()
def indexed(tmp_path, code_chunks):
    # write each labelled chunk as its own file so symbols are findable
    for c in code_chunks:
        (tmp_path / f"{c['id']}.py").write_text(
            f"def {c['id']}_impl():\n    " + c["text"].replace("\n", "\n    ")
            + "\n", encoding="utf-8", newline="\n")
    build_index(tmp_path, _DEFAULT_MODEL)
    return tmp_path


def test_similarity_conversion_is_monotonic_and_bounded():
    assert _similarity(0.0) == pytest.approx(1.0)
    assert 0.0 <= _similarity(2.0) <= 1.0
    assert _similarity(0.5) > _similarity(1.5)


@requires_vec
def test_query_ranks_relevant_chunk_first(indexed, labelled_queries):
    hits = 0
    for q in labelled_queries:
        out = search(indexed, q["query"], k=3)
        if out["results"] and q["answer"] in out["results"][0]["file"]:
            hits += 1
    # the benchmarked model should nail most of the fixture from the index
    assert hits >= len(labelled_queries) * 3 // 4


@requires_vec
def test_low_confidence_is_flagged_not_hidden(indexed):
    out = search(indexed, "quantum chromodynamics lattice gauge theory", k=5,
                 min_score=0.99)   # nothing will clear this
    assert out["confident_results"] == 0
    assert all(r["low_confidence"] for r in out["results"])


@requires_vec
def test_results_carry_location_and_posix_paths(indexed):
    out = search(indexed, "retry logic", k=1)
    r = out["results"][0]
    assert set(r) >= {"file", "symbol", "start_line", "end_line", "score",
                      "low_confidence"}
    assert "\\" not in r["file"] and isinstance(r["start_line"], int)


@requires_vec
def test_model_mismatch_escalates(indexed):
    from groundwork.core.runner import ToolError
    from groundwork.tools.semsearch import search as search_mod
    with pytest.raises(ToolError) as ei:
        # force a different model name than the index was built with
        search_mod.search(indexed, "x", k=1,
                          _model_override="BAAI/bge-small-zh-v1.5")
    assert ei.value.code == "MODEL_MISMATCH" and ei.value.exit_code == 4
