"""AST mutation engine: one canonical operator swap per mutable node, scoped
to changed lines. ast.unparse yields a valid throwaway mutant module."""
import ast
from dataclasses import dataclass

_CMP_SWAP = {ast.Lt: ast.LtE, ast.LtE: ast.Lt, ast.Gt: ast.GtE,
             ast.GtE: ast.Gt, ast.Eq: ast.NotEq, ast.NotEq: ast.Eq}
_BIN_SWAP = {ast.Add: ast.Sub, ast.Sub: ast.Add, ast.Mult: ast.Div,
             ast.Div: ast.Mult}
_BOOL_SWAP = {ast.And: ast.Or, ast.Or: ast.And}


@dataclass(frozen=True)
class Mutant:
    line: int
    description: str
    source: str


def _targets(tree: ast.AST, changed: set[int]) -> list[tuple]:
    """Ordered (node_index, lineno, description, kind) for mutable nodes on
    changed lines. node_index is the position in a stable ast.walk."""
    out = []
    for idx, node in enumerate(ast.walk(tree)):
        line = getattr(node, "lineno", None)
        if line is None or line not in changed:
            continue
        if isinstance(node, ast.Compare) and type(node.ops[0]) in _CMP_SWAP:
            a, b = type(node.ops[0]).__name__, _CMP_SWAP[type(node.ops[0])].__name__
            out.append((idx, line, f"{a}->{b}", "cmp"))
        elif isinstance(node, ast.BinOp) and type(node.op) in _BIN_SWAP:
            a, b = type(node.op).__name__, _BIN_SWAP[type(node.op)].__name__
            out.append((idx, line, f"{a}->{b}", "bin"))
        elif isinstance(node, ast.BoolOp) and type(node.op) in _BOOL_SWAP:
            a, b = type(node.op).__name__, _BOOL_SWAP[type(node.op)].__name__
            out.append((idx, line, f"{a}->{b}", "bool"))
        elif isinstance(node, ast.Constant) and isinstance(node.value, bool):
            out.append((idx, line, f"{node.value}->{not node.value}", "const"))
    return out


def mutation_points(source: str, changed_lines: set[int]) -> list[dict]:
    tree = ast.parse(source)
    return [{"line": ln, "description": desc}
            for (_i, ln, desc, _k) in _targets(tree, changed_lines)]


def _apply(source: str, target_idx: int, kind: str) -> str:
    tree = ast.parse(source)
    for idx, node in enumerate(ast.walk(tree)):
        if idx != target_idx:
            continue
        if kind == "cmp":
            node.ops[0] = _CMP_SWAP[type(node.ops[0])]()
        elif kind == "bin":
            node.op = _BIN_SWAP[type(node.op)]()
        elif kind == "bool":
            node.op = _BOOL_SWAP[type(node.op)]()
        elif kind == "const":
            node.value = not node.value
        break
    return ast.unparse(ast.fix_missing_locations(tree))


def iter_mutants(source: str, changed_lines: set[int]) -> list[Mutant]:
    """One mutant per mutable node on a changed line (full mutated module)."""
    tree = ast.parse(source)                      # SyntaxError (ValueError) on bad src
    targets = _targets(tree, changed_lines)
    mutants = []
    for idx, line, desc, kind in targets:
        mutated = _apply(source, idx, kind)
        mutants.append(Mutant(line=line, description=desc, source=mutated))
    return mutants
