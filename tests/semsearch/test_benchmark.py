"""THE benchmark. Runs candidate models over the labelled fixture, prints
MRR@10 + latency, and asserts the chosen default clears a quality bar. When
this runs, read the printed table and set _DEFAULT_MODEL/_MIN_SCORE in
src/groundwork/tools/semsearch/__init__.py to the winner, then re-run."""
import time

import numpy as np

_CANDIDATES = [
    "BAAI/bge-small-en-v1.5",
    "sentence-transformers/all-MiniLM-L6-v2",
    "snowflake/snowflake-arctic-embed-xs",
]


def _cos(a, b):
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def _mrr_and_latency(model_name, chunks, queries):
    from fastembed import TextEmbedding
    m = TextEmbedding(model_name=model_name)
    ids = [c["id"] for c in chunks]
    embs = list(m.embed([c["text"] for c in chunks]))
    rr = []
    t0 = time.perf_counter()
    q_embs = list(m.query_embed([q["query"] for q in queries]))
    latency_ms = (time.perf_counter() - t0) * 1000 / len(queries)
    for q, qe in zip(queries, q_embs):
        ranked = sorted(zip(ids, [_cos(qe, e) for e in embs]),
                        key=lambda x: -x[1])
        rank = [i for i, (cid, _) in enumerate(ranked, 1) if cid == q["answer"]][0]
        rr.append(1.0 / rank)
    return sum(rr) / len(rr), latency_ms


def test_benchmark_selects_a_capable_model(code_chunks, labelled_queries):
    from groundwork.tools.semsearch import _DEFAULT_MODEL
    results = {}
    for name in _CANDIDATES:
        try:
            mrr, lat = _mrr_and_latency(name, code_chunks, labelled_queries)
        except Exception as e:  # a model that won't fetch/run is disqualified
            print(f"\n{name}: UNAVAILABLE ({type(e).__name__})")
            continue
        results[name] = (mrr, lat)
        print(f"\n{name}: MRR@10={mrr:.3f}  query_latency={lat:.1f}ms")
    assert results, "no candidate model ran"
    best = max(results, key=lambda k: results[k][0])
    print(f"\nBEST: {best} (MRR {results[best][0]:.3f})")
    assert _DEFAULT_MODEL in results
    assert results[_DEFAULT_MODEL][0] >= 0.80, \
        f"{_DEFAULT_MODEL} MRR {results[_DEFAULT_MODEL][0]:.3f} below 0.80 bar"
    assert results[_DEFAULT_MODEL][0] >= results[best][0] - 1e-9, \
        f"{_DEFAULT_MODEL} is not the benchmark winner ({best} is)"
