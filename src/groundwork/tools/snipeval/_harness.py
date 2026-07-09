"""Run a snippet under the PROJECT interpreter; capture a trailing expr's repr.

Executed as: <project-python> _harness.py <code_file>
Reads the repr-output path from GROUNDWORK_SNIPEVAL_REPR_OUT (optional).
Stdlib-only and 3.x-portable: it must run under whatever Python the project has.
"""
import ast
import os
import sys

# Review-fixed: without this, sys.path[0] defaults to this script's own directory
# (groundwork's snipeval package dir), so a snippet's `import engine` (or any module
# name that happens to collide with a groundwork internal) silently imports
# GROUNDWORK's module instead, and project-local modules under the project root don't
# resolve. The engine runs this harness with cwd=root, so os.getcwd() IS the project
# root; restoring sys.path[0] to it gives snippets normal project-root import fidelity.
# The harness itself only needs stdlib, so it doesn't need its own dir on the path.
sys.path[0] = os.getcwd()

code_path = sys.argv[1]
with open(code_path, encoding="utf-8") as fh:
    src = fh.read()

tree = ast.parse(src, filename=code_path)
trailing = None
if tree.body and isinstance(tree.body[-1], ast.Expr):
    trailing = tree.body.pop()

namespace = {"__name__": "__main__", "__file__": code_path}
exec(compile(tree, code_path, "exec"), namespace)  # noqa: S102 — that is the tool's job

if trailing is not None:
    value = eval(  # noqa: S307 — evaluating the operator's own trailing expression
        compile(ast.Expression(trailing.value), code_path, "eval"), namespace)
    # Review-fixed: REPL convention suppresses None (e.g. a lone print() call, whose
    # trailing-expr value is None) instead of reporting the literal string "None".
    if value is not None:
        out = os.environ.get("GROUNDWORK_SNIPEVAL_REPR_OUT")
        if out:
            with open(out, "w", encoding="utf-8") as fh:
                fh.write(repr(value))
