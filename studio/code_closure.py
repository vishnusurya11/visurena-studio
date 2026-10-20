"""The studio modules a piece of code runs: the import closure a verdict cache pins.

A cache that serves a verdict from the bytes must pin every line that made the verdict.
A typed file list drifts (package H skeptic, retro 2026-10-20: take_content's three files left
out look_table, panel_dq and people_count, all imported inside functions), so the list is
derived: every `studio` import of a file, lazy ones too, followed to a fixed point.
Only the source is parsed; nothing is imported or run.
"""
from __future__ import annotations

import ast
from pathlib import Path


def module_file(root: Path, dotted: str) -> str | None:
    """`studio.x` as its repo-relative file (a package by its __init__), or None when no file is it."""
    rel = dotted.replace(".", "/")
    for candidate in (f"{rel}.py", f"{rel}/__init__.py"):
        if (Path(root) / candidate).is_file():
            return candidate
    return None


def named(node: ast.AST) -> list[str]:
    """The dotted modules one import statement may name (`from studio import x` names studio.x)."""
    if isinstance(node, ast.Import):
        return [a.name for a in node.names]
    if isinstance(node, ast.ImportFrom) and node.module and not node.level:
        return [node.module] + [f"{node.module}.{a.name}" for a in node.names]
    return []


def imports(root: Path, rel: str) -> set[str]:
    """The studio files `rel` imports anywhere in its body, itself excluded."""
    tree = ast.parse((Path(root) / rel).read_text(encoding="utf-8"))
    dotted = {d for node in ast.walk(tree) for d in named(node) if d.startswith("studio.")}
    return {f for d in dotted if (f := module_file(root, d)) and f != rel}


def closure(root: Path, roots: tuple[str, ...]) -> tuple[str, ...]:
    """`roots` and every studio file they reach, sorted."""
    seen: set[str] = set()
    todo = list(roots)
    while todo:
        rel = todo.pop()
        if rel not in seen:
            seen.add(rel)
            todo.extend(imports(root, rel) - seen)
    return tuple(sorted(seen))
