"""The registry declares what every episode and refs step reads and writes
(`in:` / `out:` per step in stages.yaml, decision 2026-09-25, the Command
Center): one declaration, book-relative globs, `{unit}` templated.  A stage
written before the keys existed declares nothing and answers with an empty
list; the department's deliverable is its last step's first output."""
from __future__ import annotations

import pytest

from studio import registry

DECLARING = ("episode", "refs")


def _every_step(stage: str) -> list[tuple[str, str]]:
    return [(stage, s["id"]) for s in registry.steps(stage)]


@pytest.mark.parametrize("stage,step_id", [p for s in DECLARING for p in _every_step(s)])
def test_every_episode_and_refs_step_declares_inputs_and_outputs(stage, step_id):
    ins, outs = registry.inputs_of(stage, step_id), registry.outputs_of(stage, step_id)
    assert ins and outs, f"{stage}/{step_id} declares nothing"
    for path in ins + outs:
        assert isinstance(path, str) and path == path.strip(), (stage, step_id, path)
        assert not path.startswith(("/", "\\")) and ":" not in path and ".." not in path, path
        assert "\\" not in path, f"{path}: posix only"


def test_the_unit_is_filled_in_when_given_and_kept_as_a_template_when_not():
    assert "episodes/{unit}/plan.json" in registry.outputs_of("episode", "02")
    assert "episodes/ep04/plan.json" in registry.outputs_of("episode", "02", unit="ep04")
    assert "episodes/ep04/plan.json" in registry.inputs_of("episode", "03", unit="ep04")
    assert not any("{unit}" in p for p in registry.inputs_of("episode", "09", unit="ep12"))


def test_a_book_level_file_is_declared_plain():
    assert "refs/refs.json" in registry.outputs_of("refs", "01")
    assert "refs/refs.json" in registry.inputs_of("episode", "01", unit="ep04")


def test_a_stage_written_before_the_keys_declares_nothing():
    assert registry.inputs_of("analysis", "01") == []
    assert registry.outputs_of("analysis", "06") == []
    assert registry.deliverable_of("analysis") is None


def test_an_unknown_step_is_refused_by_name():
    with pytest.raises(ValueError, match="99"):
        registry.inputs_of("episode", "99")


def test_the_deliverable_is_the_last_steps_first_output():
    assert registry.deliverable_of("episode") == "episodes/{unit}/manifest.json"
    assert registry.deliverable_of("episode", unit="ep04") == "episodes/ep04/manifest.json"
    assert registry.deliverable_of("refs") == "refs/verdict.json"


def test_every_existing_step_key_survives_beside_the_new_ones():
    for stage in DECLARING:
        for step in registry.steps(stage):
            assert {"id", "name", "script", "desc"} <= set(step), (stage, step["id"])
            assert isinstance(step["in"], list) and isinstance(step["out"], list)
