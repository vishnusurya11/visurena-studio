"""Step 04 parks nobody: the word is gone from the module, the owner-gate
module is not imported, and the look judge, the sheet ladder and its keep-best
terminal are wired in its place under the registry's auto row."""
from __future__ import annotations

import inspect

from scripts.refs import step_04_verdict as step
from studio import gate_policy


def test_the_step_module_never_names_the_owner_gate():
    source = inspect.getsource(step)
    assert "Escalation" not in source
    assert "studio.escalate" not in source


def test_the_step_wires_the_judge_and_the_ladder():
    source = inspect.getsource(step)
    assert "judged_gate.clear(" in source
    assert "sheet_ladder" in source and "look.judge" in source and "keep_best" in source


def test_the_step_names_the_gate_the_registry_retired():
    policy = gate_policy.of("refs", step.GATE)
    assert policy.state == "auto" and policy.judge == "look@1"
    assert policy.terminal == "keep_best"
