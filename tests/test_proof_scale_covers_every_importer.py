"""The time-constant scale for hang and cap scenarios (DESIGN 2.7; 2026-10-21_ep02_proof P4).

Under manifest.scale = k the listed constants are divided by k in their defining module, in
every module that imported one BY VALUE (`from studio.run_budget import EPISODE_CEILING_SECONDS`),
in every default argument bound to one at def time, and in the step_caps table.  This file greps
studio/ and scripts/episode/ and fails when a by-value use is missing from scale's tables.  What
a scaled run proves is that a mechanism fires at its cap, never the cap's value, never a time."""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

from studio import comfy, episode_run, repair_clock, run_budget, step_caps
from studio.rehearsal import fakes, scale

REPO = Path(__file__).resolve().parents[1]
SCANNED = ("studio", "scripts/episode")
HARNESS = "studio/rehearsal/"
"""The harness's own modules read the REAL constants by design (the time model compares against the
owner's real limit) and are never what a scaled rehearsal measures, so they are not scanned."""
STEP_CAPS_READS = frozenset({"wall_s", "step_wall_s", "table", "cap"})


def names() -> set[str]:
    return {n for consts in scale.CONSTANTS.values() for n in consts}


def module_of(path: Path) -> str:
    return path.relative_to(REPO).with_suffix("").as_posix().replace("/", ".")


def files():
    for top in SCANNED:
        yield from (p for p in sorted((REPO / top).rglob("*.py")) if not p.relative_to(REPO).as_posix().startswith(HARNESS))


def by_value_imports(tree) -> set[str]:
    """Module-level `from X import NAME` of a scaled constant."""
    return {a.asname or a.name for n in tree.body if isinstance(n, ast.ImportFrom)
            for a in n.names if a.name in names()}


def bound_defaults(tree, wanted: set[str]) -> set[tuple[str, str]]:
    """(function qualname, parameter) of every default naming a scaled constant (bare or dotted)."""
    out = set()

    def visit(node, prefix: str) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                args = child.args
                pos = (args.posonlyargs + args.args)[len(args.posonlyargs + args.args) - len(args.defaults):]
                pairs = list(zip(pos, args.defaults)) + [(a, d) for a, d in zip(args.kwonlyargs, args.kw_defaults) if d]
                out.update((prefix + child.name, a.arg) for a, d in pairs if named(d) in wanted)
                visit(child, prefix + child.name + ".")
            elif isinstance(child, ast.ClassDef):
                visit(child, prefix + child.name + ".")
    visit(tree, "")
    return out


def named(node) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    return node.attr if isinstance(node, ast.Attribute) else None


def evaluated(node):
    """The nodes evaluated when this expression runs (a lambda's body runs later, not at import)."""
    yield node
    for child in ast.iter_child_nodes(node):
        if not isinstance(child, ast.Lambda):
            yield from evaluated(child)


def reads_scaled(node) -> bool:
    """A scaled constant, or a step_caps wall read (`step_caps.wall_s(...)`)."""
    if named(node) in names():
        return True
    return (isinstance(node, ast.Attribute) and node.attr in STEP_CAPS_READS
            and isinstance(node.value, ast.Name) and node.value.id == "step_caps")


def module_level_captures(tree) -> set[str]:
    """Module-level names computed at import from a scaled constant or a step_caps wall."""
    out = set()
    for n in tree.body:
        if isinstance(n, (ast.Assign, ast.AnnAssign)) and n.value is not None and any(map(reads_scaled, evaluated(n.value))):
            targets = n.targets if isinstance(n, ast.Assign) else [n.target]
            out.update(t.id for t in targets if isinstance(t, ast.Name) and t.id not in names())
    return out


def test_every_by_value_importer_is_scaled():
    missing = []
    for path in files():
        mod, tree = module_of(path), ast.parse(path.read_text(encoding="utf-8"))
        for name in by_value_imports(tree):
            if name not in scale.IMPORTERS.get(mod, ()):
                missing.append(f"{mod} imports {name} by value")
    assert not missing, "\n".join(missing)


def test_every_default_bound_to_a_constant_is_scaled():
    missing = []
    for path in files():
        mod, tree = module_of(path), ast.parse(path.read_text(encoding="utf-8"))
        for qualname, param in bound_defaults(tree, names()):
            if param not in scale.DEFAULTS.get(mod, {}).get(qualname, ()):
                missing.append(f"{mod}.{qualname}({param}=...)")
    assert not missing, "\n".join(missing)


def test_no_module_captures_a_scaled_value_at_import():
    found = {module_of(p): c for p in files() if (c := module_level_captures(ast.parse(p.read_text(encoding="utf-8"))))}
    unlisted = {m: c for m, c in found.items() if not c <= set(scale.CAPTURES.get(m, {}))}
    assert not unlisted, f"module-level values computed from a scaled constant: {unlisted}"


def test_the_grep_sees_the_known_importers():
    assert "EPISODE_CEILING_SECONDS" in scale.IMPORTERS["scripts.episode.step_09_shoot"]
    assert ("stuck", "patience") in {(q, p) for q, ps in scale.DEFAULTS["studio.comfy"].items() for p in ps}


@pytest.fixture
def scaled(tmp_path):
    fakes.install({"scale": 60}, tmp_path)
    yield
    fakes.uninstall()


def test_a_scaled_rehearsal_divides_the_constants_their_importers_and_defaults(scaled):
    assert comfy.RESTART_SECONDS == 20.0 and comfy.QUEUE_SECONDS == 120.0
    assert run_budget.EPISODE_CEILING_SECONDS == 300 and episode_run.OWNER_LIMIT_SECONDS == 360
    assert comfy.stuck.__defaults__[0] == 0.5
    assert episode_run.EpisodeContext.__init__.__kwdefaults__["ceiling"] == 300
    assert repair_clock.cap_for.__defaults__[1] == 300


def test_a_wall_captured_at_import_is_recomputed_from_the_scaled_table(tmp_path):
    from studio import plan_ladder
    before = plan_ladder.CLIMB_WALL_S
    fakes.install({"scale": 60}, tmp_path)
    try:
        assert plan_ladder.CLIMB_WALL_S == before / 60
    finally:
        fakes.uninstall()
    assert plan_ladder.CLIMB_WALL_S == before


def test_the_cap_table_walls_are_scaled(tmp_path):
    before = step_caps.wall_s("takes")
    fakes.install({"scale": 60}, tmp_path)
    try:
        assert step_caps.wall_s("takes") == before / 60
    finally:
        fakes.uninstall()
    assert step_caps.wall_s("takes") == before and comfy.RESTART_SECONDS == 1200.0


def test_scale_one_changes_nothing(tmp_path):
    fakes.install({"scale": 1}, tmp_path)
    try:
        assert comfy.RESTART_SECONDS == 1200.0 and run_budget.OWNER_LIMIT_SECONDS == 6 * 3600
    finally:
        fakes.uninstall()


def test_the_list_is_printed_with_the_scale(tmp_path):
    lines = scale.listing(60)
    assert any("studio.comfy.RESTART_SECONDS 1200.0 -> 20.0" in x for x in lines)
