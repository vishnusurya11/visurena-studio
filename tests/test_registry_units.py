"""The registry is the org chart: every stage declares its unit of work and what it
requires, and the runners read both from stages.yaml instead of hard-coding them.

A stage written before these keys existed (analysis, screenplay, trailer) parses as
before: unit defaults to the book, requires to nothing."""
from __future__ import annotations

import re

import yaml

from studio import registry

ID = re.compile(r"^\d\d(_\d\d)*$")


def test_stage_names_are_the_yaml_in_file_order():
    with open(registry.PATH, encoding="utf-8") as fh:
        raw = yaml.safe_load(fh)["stages"]
    assert registry.stage_names() == list(raw)


def test_a_stage_without_the_new_keys_defaults_to_the_book():
    assert registry.unit_of("analysis") == ["book"]
    assert registry.requires_of("analysis") == []


def test_the_episode_stage_declares_its_grain_and_its_prerequisites():
    assert registry.unit_of("episode") == ["book", "chapter"]
    assert registry.requires_of("episode") == ["analysis/06", "refs/04"]


def test_refs_is_keyed_on_book_and_style_and_needs_the_profiles():
    assert registry.unit_of("refs") == ["book", "style"]
    assert registry.requires_of("refs") == ["analysis/05"]


def test_every_step_id_is_fixed_width_and_every_script_is_named_for_its_step():
    for name in registry.stage_names():
        for step in registry.steps(name):
            assert ID.match(step["id"]), (name, step["id"])
            assert step["script"] == f"step_{step['id']}_{step['name']}", (name, step["id"])
            for sub in step.get("substeps", []):
                assert ID.match(sub["id"]) and sub["id"].startswith(step["id"] + "_"), (name, sub["id"])


def test_an_unknown_stage_is_refused_by_name():
    try:
        registry.stage("bogus")
    except ValueError as exc:
        assert "bogus" in str(exc)
    else:
        raise AssertionError("an unknown stage must be refused")


def test_a_requirement_names_a_step_that_exists():
    for name in registry.stage_names():
        for req in registry.requires_of(name):
            stage, step_id = req.split("/")
            assert step_id in {s["id"] for s in registry.steps(stage)}, req
