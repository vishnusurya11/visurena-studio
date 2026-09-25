"""No step of the refs or episode line parks on a person (decision
2026-09-24-automate-the-taste-gates).  Every taste gate is a judge with a ladder
whose terminal rung signs `flagged`; the word Escalation may not appear in a
step module of either line, and every step module must import."""
from __future__ import annotations

import importlib
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
LINES = ("refs", "episode")
STEPS = sorted(p for line in LINES for p in (ROOT / "scripts" / line).glob("step_*.py"))


@pytest.mark.parametrize("path", STEPS, ids=[f"{p.parent.name}/{p.stem}" for p in STEPS])
def test_the_step_names_no_escalation(path: Path):
    text = path.read_text(encoding="utf-8")
    assert not re.search(r"\bEscalation\b", text), f"{path.relative_to(ROOT)} still parks"


@pytest.mark.parametrize("path", STEPS, ids=[f"{p.parent.name}/{p.stem}" for p in STEPS])
def test_the_step_imports(path: Path):
    module = importlib.import_module(f"scripts.{path.parent.name}.{path.stem}")
    assert module.STEP_ID and module.NAME


def test_both_lines_have_their_steps():
    assert sum(p.parent.name == "refs" for p in STEPS) == 4
    assert sum(p.parent.name == "episode" for p in STEPS) == 12
