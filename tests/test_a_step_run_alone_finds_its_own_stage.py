"""A step run on its own finds the stage its folder names, not the first stage
that happens to share its script name.

ep12, 2026-09-24: `scripts/episode/step_02_plan.py` resolved to the screenplay
stage, whose second step is also `step_02_plan`, and died importing
`studio.screenplay_run`. The folder says which stage a step belongs to.
"""
from types import SimpleNamespace

from studio import step_cli


def test_a_shared_script_name_resolves_by_its_folder():
    module = SimpleNamespace(__file__="D:/repo/scripts/episode/step_02_plan.py")
    assert step_cli.registry_stage_of(module) == "episode"


def test_the_other_owner_of_the_name_still_resolves_to_itself():
    module = SimpleNamespace(__file__="D:/repo/scripts/screenplay/step_02_plan.py")
    assert step_cli.registry_stage_of(module) == "screenplay"
