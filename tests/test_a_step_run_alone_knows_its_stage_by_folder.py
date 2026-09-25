"""A step module run as a script has no package name, so the CLI finds its stage
from the file.  A script NAME is not unique across stages (screenplay and episode
both have step_02_plan); the FOLDER names the stage, and the name-only search is
only a fallback for a module outside any stage folder."""
from __future__ import annotations

import types

from studio import step_cli


def _module(path: str):
    return types.SimpleNamespace(__file__=path, __name__="__main__")


def test_the_folder_decides_when_two_stages_share_a_script_name():
    assert step_cli.registry_stage_of(_module("D:/x/scripts/episode/step_02_plan.py")) == "episode"
    assert step_cli.registry_stage_of(_module("D:/x/scripts/screenplay/step_02_plan.py")) == "screenplay"


def test_a_unique_script_name_resolves_without_its_folder():
    assert step_cli.registry_stage_of(_module("D:/elsewhere/step_04_verdict.py")) == "refs"


def test_an_unregistered_script_is_refused():
    try:
        step_cli.registry_stage_of(_module("D:/x/scripts/episode/step_99_nothing.py"))
    except SystemExit as exc:
        assert "not a registered step" in str(exc)
    else:
        raise AssertionError("must refuse")
