"""Walk a griffe static load into a compact, deterministic API surface."""
import ast
from pathlib import Path
from typing import Any

import griffe
from griffe import ParameterKind

from groundwork.core.runner import ToolError


def first_doc_line(obj: Any) -> str | None:
    doc = getattr(obj, "docstring", None)
    if doc is None or not doc.value.strip():
        return None
    return doc.value.strip().splitlines()[0]


def render_signature(func: Any) -> str:
    parts: list[str] = []
    positional_only_open = False
    keyword_only_marked = False
    for p in func.parameters:
        if p.kind is ParameterKind.positional_only:
            positional_only_open = True
        elif positional_only_open:
            parts.append("/")
            positional_only_open = False
        name = p.name
        is_var = p.kind in (ParameterKind.var_positional, ParameterKind.var_keyword)
        if p.kind is ParameterKind.var_positional:
            name = f"*{name}"
            keyword_only_marked = True
        elif p.kind is ParameterKind.var_keyword:
            name = f"**{name}"
        elif p.kind is ParameterKind.keyword_only and not keyword_only_marked:
            parts.append("*")
            keyword_only_marked = True
        rendered = name
        # griffe reports Parameter.default as the placeholder string '()' /
        # '{}' for *args/**kwargs (there is no real default for these kinds
        # in Python) — never render a default for them, even though the
        # annotation (if any) still renders normally.
        default = None if is_var else p.default
        if p.annotation is not None:
            rendered += f": {p.annotation}"
            if default is not None:
                rendered += f" = {default}"
        elif default is not None:
            rendered += f"={default}"
        parts.append(rendered)
    if positional_only_open:
        parts.append("/")
    ret = f" -> {func.returns}" if func.returns is not None else ""
    return f"({', '.join(parts)}){ret}"


def _parse_all(module: Any) -> list[str] | None:
    member = module.members.get("__all__")
    if member is None:
        return None
    try:
        value = ast.literal_eval(str(member.value))
    except (ValueError, SyntaxError):
        return None
    if isinstance(value, (list, tuple)) and all(isinstance(x, str) for x in value):
        return list(value)
    return None


def _is_public(name: str, exports: list[str] | None) -> bool:
    if exports is not None:
        return name in exports
    return not name.startswith("_")


def _function_entry(func: Any) -> dict[str, Any]:
    return {"sig": render_signature(func), "doc": first_doc_line(func)}


def _attribute_entry(attr: Any) -> dict[str, Any]:
    return {"annotation": str(attr.annotation) if attr.annotation is not None else None,
            "value": str(attr.value) if attr.value is not None else None}


def _class_entry(cls: Any) -> dict[str, Any]:
    methods, attributes = {}, {}
    for name, member in sorted(cls.members.items()):
        if name.startswith("_") or member.is_alias:
            continue
        if member.is_function:
            methods[name] = _function_entry(member)
        elif member.is_attribute:
            attributes[name] = _attribute_entry(member)
    return {"doc": first_doc_line(cls), "bases": [str(b) for b in cls.bases],
            "methods": methods, "attributes": attributes}


def _module_entry(module: Any) -> dict[str, Any]:
    exports = _parse_all(module)
    entry: dict[str, Any] = {"doc": first_doc_line(module), "exports": exports,
                             "attributes": {}, "classes": {},
                             "functions": {}, "aliases": {}}
    for name, member in sorted(module.members.items()):
        if name == "__all__" or not _is_public(name, exports):
            continue
        if member.is_alias:
            entry["aliases"][name] = member.target_path
        elif member.is_class:
            entry["classes"][name] = _class_entry(member)
        elif member.is_function:
            entry["functions"][name] = _function_entry(member)
        elif member.is_attribute:
            entry["attributes"][name] = _attribute_entry(member)
    return entry


def _walk(module: Any, out: dict[str, dict]) -> None:
    out[module.path] = _module_entry(module)
    for name, member in sorted(module.members.items()):
        if member.is_alias or not member.is_module or name.startswith("_"):
            continue
        _walk(member, out)


def extract_surface(package: str, site_packages: Path, version: str) -> dict[str, Any]:
    try:
        root = griffe.load(package, search_paths=[str(site_packages)],
                           allow_inspection=False)
    except (ModuleNotFoundError, ImportError) as e:
        raise ToolError("PACKAGE_NOT_FOUND",
                        f"package not installed in {site_packages.as_posix()}: {package}",
                        detail=str(e)) from e
    except griffe.GriffeError as e:  # griffe parse/loading failures on broken installs
        raise ToolError("EXTRACT_ERROR",
                        f"could not extract {package}: {type(e).__name__}",
                        detail=str(e)) from e
    # Anything else (AttributeError, TypeError, ...) is OUR bug, not a
    # third-party package problem — let it propagate so the runner reports
    # it honestly as INTERNAL rather than mislabeling it EXTRACT_ERROR.
    modules: dict[str, dict] = {}
    try:
        _walk(root, modules)
    except griffe.GriffeError as e:
        raise ToolError("EXTRACT_ERROR",
                        f"could not walk {package}: {type(e).__name__}",
                        detail=str(e)) from e
    return {"package": package, "version": version, "language": "python",
            "modules": modules}
