"""Reference-centrality ranking via a small, deterministic PageRank.

networkx is deliberately avoided: power iteration is a dozen lines, has no
dependency cost, and is trivially deterministic (sorted node order).
"""
from groundwork.tools.cartographer.extract import Reference, Symbol


def rank_symbols(symbols: list[Symbol], refs: list[Reference], *,
                 damping: float = 0.85, iters: int = 30) -> list[tuple[Symbol, float]]:
    if not symbols:
        return []
    nodes = sorted({s.qualified_name for s in symbols})
    index = {n: i for i, n in enumerate(nodes)}
    n = len(nodes)

    # References carry a BARE name (e.g. "format"), but node identity is the
    # dotted qualified_name (e.g. "Formatter.format") so that distinct scopes
    # stay distinct nodes. Map each bare name to every node index sharing it —
    # a bare reference is ambiguous when multiple symbols share a name, and the
    # honest coarse v1 rule is to add an edge to EVERY same-named symbol;
    # PageRank normalizes by out-degree so this doesn't distort scores.
    name_to_targets: dict[str, list[int]] = {}
    for s in symbols:
        name_to_targets.setdefault(s.name, []).append(index[s.qualified_name])

    # Out-edges: a referencing symbol contributes to the referenced name. We do
    # not know which symbol issued a reference precisely, so every symbol in the
    # referencing file points at the referenced name (coarse but stable v1 rule).
    by_file: dict[str, list[str]] = {}
    for s in symbols:
        by_file.setdefault(s.file, []).append(s.qualified_name)
    out: list[list[int]] = [[] for _ in range(n)]
    for r in refs:
        for target in name_to_targets.get(r.name, []):
            for src_qn in by_file.get(r.file, []):
                if index[src_qn] != target:
                    out[index[src_qn]].append(target)

    score = [1.0 / n] * n
    for _ in range(iters):
        nxt = [(1.0 - damping) / n] * n
        for i in range(n):
            if out[i]:
                share = damping * score[i] / len(out[i])
                for j in out[i]:
                    nxt[j] += share
            else:
                # dangling node distributes evenly (keeps mass conserved -> sum≈1)
                spread = damping * score[i] / n
                for j in range(n):
                    nxt[j] += spread
        score = nxt

    # setdefault keeps the FIRST symbol seen per qualified_name, so the returned
    # Symbol identity depends on the caller passing symbols in a stable order
    # (extract.py already sorts by (line, name) before returning, so fine).
    first_by_qn = {}
    for s in symbols:
        first_by_qn.setdefault(s.qualified_name, s)
    ranked = [(first_by_qn[qn], score[index[qn]]) for qn in nodes]
    ranked.sort(key=lambda pair: (-pair[1], pair[0].qualified_name))
    return ranked
