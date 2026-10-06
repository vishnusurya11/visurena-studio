"""The fixer rung is a saved workflow the brain runs under an allow rule
(decision 2026-10-06, "Where workflows sit").  Its shape is checked here the
way the Workflow tool checks it: `meta` is the first statement and a pure
literal, the name is `fix-parked`, the three phases are declared and used,
and nothing in it breaks resume (Date.now, Math.random, dynamic import)."""
from __future__ import annotations

import re
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / ".claude" / "workflows" / "fix-parked.js"
PHASES = ("Fix", "Refute", "Land")


def _code() -> str:
    return SCRIPT.read_text(encoding="utf-8")


def _statements(code: str) -> str:
    return "\n".join(line for line in code.splitlines() if line.strip() and not line.strip().startswith("//"))


def test_meta_is_the_first_statement_and_names_the_workflow():
    first = _statements(_code()).splitlines()[0]
    assert first.startswith("export const meta = {"), first
    meta = _code().split("}\n", 1)[0] if "phases" in _code().split("}\n", 1)[0] else _code().split("\n}\n", 1)[0]
    assert re.search(r"name:\s*'fix-parked'", meta)
    assert re.search(r"description:\s*'[^']{10,}'", meta)
    assert not re.search(r"\$\{|\.\.\.|\w+\(", meta.replace("export const meta = {", "")), "meta is a pure literal"


def test_the_three_phases_are_declared_and_used():
    code = _code()
    for title in PHASES:
        assert re.search(rf"title:\s*'{title}'", code), f"meta.phases lacks {title}"
        assert re.search(rf"phase\('{title}'\)|phase:\s*'{title}'", code), f"{title} is never run"


def test_nothing_in_the_script_breaks_resume():
    code = _code()
    for banned in ("Date.now", "Math.random", "import(", "new Date()", "require("):
        assert banned not in code, banned


def test_only_the_workflow_hooks_are_called_and_it_stays_short():
    code = _code()
    assert len(code.splitlines()) <= 80
    assert "isolation: 'worktree'" in code or "isolation:'worktree'" in code
    assert "pipeline(" in code and "parallel(" in code and "agent(" in code
    assert "uv run --no-sync pytest -q" in code
    for forbidden in ("library/", "gates.yaml", "models.yaml"):
        assert forbidden in code, f"the fix agent must be told never to touch {forbidden}"
    assert re.search(r"return\s*\{\s*landed", code)
