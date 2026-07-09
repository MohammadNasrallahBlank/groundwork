"""Dependency spike: prove which tree-sitter grammars load on this machine and
pin the query-capture API shape the rest of cartographer relies on.

Verified: tree-sitter==0.26.0, tree-sitter-language-pack==1.12.5. All 6 v1
grammars (python/javascript/typescript/tsx/java/kotlin) load cleanly here. The
query-capture API is Query(lang, src) + QueryCursor(q).captures(node) ->
dict[str, list[Node]].
"""
import pytest
from tree_sitter import Parser, Query, QueryCursor
from tree_sitter_language_pack import get_language

V1_LANGS = ["python", "javascript", "typescript", "tsx", "java", "kotlin"]


@pytest.mark.parametrize("name", V1_LANGS)
def test_grammar_loads(name):
    lang = get_language(name)  # raises if the grammar is unavailable
    assert lang is not None
    Parser(lang)  # constructing a parser proves the Language is usable


def test_query_capture_api_shape():
    # Pins the API Task 2 targets: Query(lang, src) + QueryCursor(q).captures(node)
    # returns dict[str, list[Node]]. Observed on this machine (tree-sitter 0.26.0):
    # {'name': [<Node type=identifier, start_point=(0, 4), end_point=(0, 5)>]}
    lang = get_language("python")
    parser = Parser(lang)
    tree = parser.parse(b"def f():\n    pass\n")
    q = Query(lang, "(function_definition name: (identifier) @name)")
    caps = QueryCursor(q).captures(tree.root_node)
    assert isinstance(caps, dict)
    assert [n.text.decode() for n in caps["name"]] == ["f"]
