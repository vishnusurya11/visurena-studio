"""Canned answers REFUSE (DESIGN 2.4, R3; 2026-10-21_ep02_proof P4).

A structured ask no recording answers gets its schema's REFUSING instance from the reviewed
table studio/rehearsal/canned_refusals.yaml.  This file fails when a schema reachable from an
`llm.structured` call site (or an alias of it, or a function it is handed to) has no row, when a
row's instance does not behave as the row says (validates, or is refused by the schema itself),
or when a row does not say why its answer refuses downstream."""
from __future__ import annotations

import ast
import importlib
from pathlib import Path

import pytest

from studio.rehearsal import fake_sdk

REPO = Path(__file__).resolve().parents[1]
TOPS = ("studio", "agents", "scripts")


def is_structured(node) -> bool:
    """`llm.structured`, or `x or llm.structured`."""
    if isinstance(node, ast.Attribute):
        return node.attr == "structured" and isinstance(node.value, ast.Name) and node.value.id == "llm"
    return isinstance(node, ast.BoolOp) and any(is_structured(v) for v in node.values)


def aliases(tree) -> set[str]:
    return {t.id for n in ast.walk(tree) if isinstance(n, ast.Assign) and is_structured(n.value)
            for t in n.targets if isinstance(t, ast.Name)}


def handoffs(tree, rel: str) -> list[str]:
    """`f(..., ask=llm.structured)`: the site, as the yaml's `handoffs` keys spell it."""
    return [f"{rel}:{n.arg}" for n in ast.walk(tree) if isinstance(n, ast.keyword) and is_structured(n.value)]


def schema_args(tree, names: set[str]) -> list[tuple[int, ast.AST]]:
    """(line, third argument) of every structured call in the tree."""
    return [(n.lineno, n.args[2]) for n in ast.walk(tree) if isinstance(n, ast.Call) and len(n.args) > 2
            and (is_structured(n.func) or (isinstance(n.func, ast.Name) and n.func.id in names))]


def module_of(rel: str) -> str:
    return rel[:-3].replace("/", ".")


def resolve(tree, rel: str, name: str):
    """The class a bare name means in this file: defined here, or imported from somewhere."""
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and any((a.asname or a.name) == name for a in node.names):
            real = next(a.name for a in node.names if (a.asname or a.name) == name)
            return getattr(importlib.import_module(node.module), real)
    return getattr(importlib.import_module(module_of(rel)), name)


def site_schemas() -> tuple[list, list[str], list[str]]:
    """(schema classes, dynamic sites, handoff sites) over every structured call in the code."""
    found, dynamic, handed = [], [], []
    for top in TOPS:
        for path in sorted((REPO / top).rglob("*.py")):
            text = path.read_text(encoding="utf-8")
            if "structured" not in text:
                continue
            rel, tree = path.relative_to(REPO).as_posix(), ast.parse(text)
            handed += handoffs(tree, rel)
            for _, arg in schema_args(tree, aliases(tree)):
                if isinstance(arg, ast.Name) and arg.id[:1].isupper():
                    found.append(resolve(tree, rel, arg.id))
                else:
                    dynamic.append(f"{rel}:{ast.unparse(arg)}")
    return found, dynamic, handed


def handed_schemas(table: dict) -> list:
    """The schema of every call the handed-to function makes through the handed name."""
    out = []
    for site, callee in (table.get("handoffs") or {}).items():
        name, tree = site.rsplit(":", 1)[1], ast.parse((REPO / callee).read_text(encoding="utf-8"))
        out += [resolve(tree, callee, a.id) for _, a in schema_args(tree, {name}) if isinstance(a, ast.Name)]
    return out


@pytest.fixture(scope="module")
def table() -> dict:
    return fake_sdk.canned_table()


def row_classes(table: dict) -> list:
    return [fake_sdk.schema_class(row["schema"]) for row in table["refusals"]]


def test_every_schema_a_structured_call_reaches_has_a_refusing_row(table):
    found, dynamic, handed = site_schemas()
    found += [fake_sdk.schema_class(s) for site in dynamic for s in table["dynamic"].get(site, [])]
    found += handed_schemas(table)
    have = row_classes(table)
    missing = sorted({f"{c.__module__}.{c.__qualname__}" for c in found if not any(c is h for h in have)})
    assert not missing, f"no canned refusal row for: {missing}"
    assert set(dynamic) <= set(table["dynamic"]), f"dynamic schema sites not in the yaml: {set(dynamic) - set(table['dynamic'])}"
    assert set(handed) <= set(table["handoffs"]), f"handed-off structured callers not in the yaml: {set(handed) - set(table['handoffs'])}"


def test_the_grep_sees_the_writer_parts_and_a_handed_off_caller(table):
    found, dynamic, handed = site_schemas()
    assert "agents/episode_writer.py:model" in dynamic and "scripts/episode/book_title.py:ask" in handed
    assert len(found) >= 35


def test_every_row_behaves_as_it_says_and_says_why_it_refuses(table):
    for row in table["refusals"]:
        cls = fake_sdk.schema_class(row["schema"])
        assert len(row.get("refuses", "")) >= 20, f"{row['schema']} does not say why it refuses"
        if row.get("validates", True):
            cls.model_validate(row["instance"])
        else:
            with pytest.raises(Exception):
                cls.model_validate(row["instance"])


def test_rows_are_one_per_schema_class(table):
    classes = row_classes(table)
    assert len({id(c) for c in classes}) == len(classes)


def test_the_brains_own_verdict_parks_when_canned(table):
    row = fake_sdk.canned_row({"title": "Verdict", "schema": fake_sdk.schema_class("studio.brain:Verdict").model_json_schema()})
    assert row["instance"]["response"] == "park"


def test_two_schemas_with_one_title_are_told_apart_by_their_schema(table):
    for spec in ("agents.ingest_validator:Verdict", "studio.brain:Verdict"):
        schema = fake_sdk.schema_class(spec).model_json_schema()
        assert fake_sdk.canned_row({"title": "Verdict", "schema": schema})["schema"] == spec
