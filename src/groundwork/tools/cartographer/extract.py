"""Parse one file with tree-sitter; emit Symbol and Reference records."""
from dataclasses import dataclass
from pathlib import Path

from tree_sitter import Node, Parser, Query, QueryCursor

from groundwork.core.runner import ToolError
from groundwork.tools.cartographer.languages import load_spec

_KIND = {"func": "function", "class": "class", "method": "method"}


@dataclass(frozen=True)
class Symbol:
    name: str
    qualified_name: str
    kind: str
    line: int
    lang: str
    file: str


@dataclass(frozen=True)
class Reference:
    name: str
    line: int
    file: str


def _captures(language, query_src: str, root: Node) -> dict[str, list[Node]]:
    if not query_src.strip():
        return {}
    return QueryCursor(Query(language, query_src)).captures(root)


def _contains(outer: Node, inner: Node) -> bool:
    return outer.start_byte <= inner.start_byte and inner.end_byte <= outer.end_byte


def _enclosing_chain(
    name_node: Node, def_nodes: list[tuple[str, Node]]
) -> list[tuple[str, Node]]:
    """All captured def nodes whose range contains name_node, innermost first.

    The first entry is the name's own def node (the smallest enclosing def);
    each subsequent entry is a strictly larger enclosing def, out to the
    outermost (e.g. module-level) definition. Empty if no captured def
    contains this name at all.
    """
    containing = [(k, dn) for (k, dn) in def_nodes if _contains(dn, name_node)]
    containing.sort(key=lambda kd: kd[1].end_byte - kd[1].start_byte)
    return containing


def _kind_for(own_key: str, immediate_parent_key: str | None) -> str:
    """Classify a symbol from its own capture key and its IMMEDIATE enclosing def.

    A definition captured as @class is always "class". Otherwise (a
    function-ish def — @func, or an explicit @method from grammars with a
    distinct method node type) it is "method" IFF its immediate enclosing
    captured definition (the next entry in the chain, not just any ancestor)
    is a @class node; otherwise it is "function".

    This correctly distinguishes a real method (immediate parent = class)
    from a closure nested inside a method (immediate parent = the method's
    own @func/@method node — not a @class), even though the closure is still
    transitively contained in the class. Some grammars (Python, Kotlin as
    registered here) have no distinct method node type: a method is just a
    function/def node nested in a class body, so the def_query only ever
    captures it as @func — this is why the "func"/"method" cases share the
    same immediate-parent rule rather than the key alone deciding the kind.
    """
    if own_key == "class":
        return "class"
    return "method" if immediate_parent_key == "class" else "function"


def _qualified_name(name: str, ancestors: list[tuple[str, Node]], own_name: dict[int, str]) -> str:
    """Dot-join the enclosing def names (outermost first) with this symbol's name."""
    outer = [own_name[id(dn)] for (_k, dn) in reversed(ancestors)]
    return ".".join([*outer, name])


def extract(path: Path, source: bytes, lang: str) -> tuple[list[Symbol], list[Reference]]:
    spec = load_spec(lang)
    if spec is None:
        return [], []  # unsupported language: not an error, just no symbols

    tree = Parser(spec.language).parse(source)
    root = tree.root_node
    file_posix = path.as_posix()

    symbols: list[Symbol] = []
    def_caps = _captures(spec.language, spec.def_query, root)
    # @func/@class/@method mark each definition node; @name its identifier. Pair
    # each @name with the full chain of enclosing captured definitions (its own
    # def node, then each strictly larger enclosing def) to derive both its kind
    # (from the IMMEDIATE parent, not just any ancestor — see _kind_for) and its
    # dotted qualified_name (from the chain of enclosing def names).
    name_nodes = def_caps.get("name", [])
    def_nodes = [(k, n) for k in _KIND for n in def_caps.get(k, [])]

    chains = {id(nn): _enclosing_chain(nn, def_nodes) for nn in name_nodes}
    # Every captured @name is, by construction of the query, the identifier of
    # exactly one captured def node — its own chain[0]. Map that def node
    # (by identity) back to its name text so ancestors can be named too.
    own_name: dict[int, str] = {
        id(chain[0][1]): nn.text.decode("utf-8", "replace")
        for nn in name_nodes
        if (chain := chains[id(nn)])
    }

    for name_node in name_nodes:
        chain = chains[id(name_node)]
        if not chain:
            continue
        own_key, _own_node = chain[0]
        ancestors = chain[1:]
        immediate_parent_key = ancestors[0][0] if ancestors else None
        kind = _kind_for(own_key, immediate_parent_key)
        nm = name_node.text.decode("utf-8", "replace")
        qualified_name = _qualified_name(nm, ancestors, own_name)
        symbols.append(Symbol(nm, qualified_name, kind, name_node.start_point[0] + 1, lang, file_posix))

    refs: list[Reference] = []
    for ref_node in _captures(spec.language, spec.ref_query, root).get("ref", []):
        refs.append(Reference(ref_node.text.decode("utf-8", "replace"),
                              ref_node.start_point[0] + 1, file_posix))

    if root.has_error and not symbols:
        raise ToolError("PARSE_ERROR", f"could not parse {file_posix} as {lang}")
    symbols.sort(key=lambda s: (s.line, s.name))
    refs.sort(key=lambda r: (r.line, r.name))
    return symbols, refs
