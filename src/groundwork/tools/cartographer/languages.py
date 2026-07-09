"""Language registry: extension detection + per-language tree-sitter queries.

A grammar that fails to load makes its language unsupported (degradation),
never an error — load_spec returns None and callers skip those files.
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_EXT = {".py": "python", ".js": "javascript", ".jsx": "javascript",
        ".ts": "typescript", ".tsx": "tsx", ".java": "java",
        ".kt": "kotlin", ".kts": "kotlin"}

# def_query captures @func/@class/@method with a nested @name; ref_query captures
# @ref identifiers used in calls/type positions. Node-type names are grammar-
# specific and MUST be verified against the installed grammar at build time.
#
# Verified 2026-07-08 against tree-sitter-language-pack 1.12.5 (python grammar):
# Python's grammar has no distinct "method" node type — a method is just a
# function_definition nested in a class body, so its def_query only produces
# @func/@class captures (never @method). extract.py's pairing logic upgrades a
# @func-captured definition to kind "method" when it is nested inside a
# @class-captured node — see extract._kind_for(). This was confirmed by printing
# the real captures dict against tests/fixtures/cartomap/pkg/util.py: both
# `helper` (top-level) and `format` (nested in class Formatter) come back under
# the "func" capture key; only the nesting distinguishes them.
#
# Verified 2026-07-08 against tree-sitter-language-pack 1.12.5 (javascript,
# typescript, java, kotlin grammars) using tests/fixtures/cartomap_multi/*: the
# node-type names below were written from memory before this verification pass
# and turned out to be EXACTLY RIGHT for this grammar version — no corrections
# were needed. Confirmed by walking the real parse trees
# (`Parser(get_language(lang)).parse(src).root_node` and its `.children`):
#   javascript/typescript: class_declaration's name child is a type_identifier
#     in typescript, identifier in javascript; method_definition's name child
#     is property_identifier in both; function_declaration's name child is
#     identifier in both; call_expression's callee is identifier (plain call)
#     or member_expression.property (property_identifier) for a method call.
#   java: class_declaration/interface_declaration name is identifier;
#     method_declaration name is identifier; a call is method_invocation with
#     an identifier name child.
#   kotlin: class_declaration has a bare type_identifier child (no `name:`
#     field in this grammar); function_declaration has a bare simple_identifier
#     child; a call is call_expression with a bare simple_identifier child
#     (the grammar exposes no field names here, hence the queries below match
#     by direct child type rather than by field).
# All four extract correctly with sane kinds: class methods (Sample.add,
# Widget.render, Box.open, Greeter.greet) come back "method" because their
# immediate enclosing captured def is @class; top-level functions (build,
# unlock) come back "function". See tests/cartographer/test_extract_multi.py.
_DEF_QUERIES = {
    "python": """
(function_definition name: (identifier) @name) @func
(class_definition name: (identifier) @name) @class
""",
    "javascript": """
(function_declaration name: (identifier) @name) @func
(class_declaration name: (identifier) @name) @class
(method_definition name: (property_identifier) @name) @method
""",
    "typescript": """
(function_declaration name: (identifier) @name) @func
(class_declaration name: (type_identifier) @name) @class
(method_definition name: (property_identifier) @name) @method
(interface_declaration name: (type_identifier) @name) @class
""",
    "java": """
(class_declaration name: (identifier) @name) @class
(interface_declaration name: (identifier) @name) @class
(method_declaration name: (identifier) @name) @method
""",
    "kotlin": """
(class_declaration (type_identifier) @name) @class
(function_declaration (simple_identifier) @name) @func
""",
}
_DEF_QUERIES["tsx"] = _DEF_QUERIES["typescript"]

_REF_QUERIES = {
    "python": "(call function: [(identifier) @ref (attribute attribute: (identifier) @ref)])",
    "javascript": "(call_expression function: [(identifier) @ref (member_expression property: (property_identifier) @ref)])",
    "java": "(method_invocation name: (identifier) @ref)",
    "kotlin": "(call_expression (simple_identifier) @ref)",
}
_REF_QUERIES["typescript"] = _REF_QUERIES["javascript"]
_REF_QUERIES["tsx"] = _REF_QUERIES["javascript"]


@dataclass(frozen=True)
class LanguageSpec:
    name: str
    language: Any          # tree_sitter.Language
    def_query: str
    ref_query: str


def detect_language(path: Path) -> str | None:
    return _EXT.get(path.suffix.lower())


_CACHE: dict[str, LanguageSpec | None] = {}


def load_spec(lang: str) -> LanguageSpec | None:
    if lang in _CACHE:
        return _CACHE[lang]
    spec: LanguageSpec | None = None
    if lang in _DEF_QUERIES:
        try:
            from tree_sitter_language_pack import get_language
            spec = LanguageSpec(lang, get_language(lang),
                                _DEF_QUERIES[lang], _REF_QUERIES.get(lang, ""))
        except Exception:  # grammar unavailable on this platform -> degrade
            spec = None
    _CACHE[lang] = spec
    if spec is not None:
        LANGUAGES[lang] = spec
    return spec


#: Populated on demand as load_spec() resolves each language (never eagerly
#: imports every grammar at module import time). After at least one load_spec
#: / available_languages() call for a given language, its entry is present
#: here iff the grammar is available on this platform (degradation-aware).
LANGUAGES: dict[str, LanguageSpec] = {}


def available_languages() -> list[str]:
    return sorted(name for name in _DEF_QUERIES if load_spec(name) is not None)
