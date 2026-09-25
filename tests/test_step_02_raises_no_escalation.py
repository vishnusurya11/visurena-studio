"""Step 02 parks nobody: the word is gone from the module, the owner-gate
module is not imported, and the plan judge, its ladder and the two terminals
are wired in its place."""
from __future__ import annotations

import inspect

from scripts.episode import step_02_plan as step


def test_the_step_module_never_names_the_owner_gate():
    source = inspect.getsource(step)
    assert "Escalation" not in source
    assert "studio.escalate" not in source


def test_the_step_wires_the_judge_and_the_ladder():
    source = inspect.getsource(step)
    assert "judged_gate.clear(" in source
    assert "plan_ladder" in source and "plan_reader" in source


def test_the_step_names_the_gate_the_registry_retired():
    from studio import gate_policy
    policy = gate_policy.of("episode", step.GATE)
    assert policy.state == "auto" and policy.judge == "plan@1"
    assert policy.terminal == "keep_best" and policy.battery_terminal == "defer"
