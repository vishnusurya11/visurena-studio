"""The episode writer's Draft parts are served from a TARGET PLAN folded back into the parts the
writer asks for (DESIGN 2.3; 2026-10-21_ep02_proof P4): setups dict -> named list, each part its
PART_TABLE fields.  Jekyll ep01's delivered plan must come back out of the REAL
agents.episode_writer.write -> llm.structured -> llm._SdkStructuredCaller -> brain.ask_structured
path unchanged: every line of the writer's parsing, merging, cures and contract runs, and only
the transport is fake.  $0: no CLI, no network."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from agents import episode_writer
from studio import llm
from studio.episode_spec import Episode
from studio.rehearsal import fake_sdk, fakes

PLAN = Path(__file__).resolve().parent / "fixtures" / "proof" / "sdk_streams" / "jekyll_ep01_plan.json"
"""Copied from library/<jekyll>/episodes/ep01/plan.json (the delivered ep01, 2026-10-19)."""


@pytest.fixture
def plan() -> dict:
    return json.loads(PLAN.read_text(encoding="utf-8"))


@pytest.fixture
def served(tmp_path, plan):
    fakes.install({"writer_plan": str(PLAN)}, tmp_path)
    yield tmp_path
    fakes.uninstall()


def brief_of(plan: dict) -> dict:
    """The band the code sets the plan's own rate and grammar from (CODE_SET_FIELDS)."""
    return {"band": {"words_per_second": plan["words_per_second"], "grammar": plan["grammar"],
                     "motif": plan["motif"]}}


def test_the_plan_folds_into_the_parts_the_writer_asks_for(plan):
    parts = fake_sdk.draft_parts(plan)
    assert list(parts) == [m.__name__ for m in episode_writer.PART_MODELS]
    for (_, fields), model in zip(episode_writer.PART_TABLE, episode_writer.PART_MODELS):
        assert set(parts[model.__name__]) <= set(fields)
        model.model_validate(parts[model.__name__])
    names = [s["name"] for s in parts["PartFrame"]["setups"]]
    assert names == list(plan["setups"])


def test_ep01_round_trips_through_the_real_writer_unchanged(served, plan):
    usage: dict = {}
    got = episode_writer.write(brief_of(plan), usage=usage)
    assert got.model_dump() == Episode.model_validate(plan).model_dump()
    labels = [json.loads(x)["label"] for x in (served / "sdk_log.jsonl").read_text(encoding="utf-8").splitlines()]
    assert labels == ["substituted"] * episode_writer.PARTS
    assert usage["input_tokens"] > 0 and usage["tier"] == episode_writer.TIER


def test_the_writer_tier_is_on_the_sdk_caller(served):
    assert isinstance(llm._caller_for(episode_writer.TIER), llm._SdkStructuredCaller)


def test_a_part_the_plan_lacks_is_canned_and_the_contract_refuses_it(tmp_path, plan):
    del plan["lines"]
    thin = tmp_path / "thin.json"
    thin.write_text(json.dumps(plan), encoding="utf-8")
    fakes.install({"writer_plan": str(thin)}, tmp_path)
    try:
        with pytest.raises(ValueError):
            episode_writer.write(brief_of(plan))
    finally:
        fakes.uninstall()
    labels = [json.loads(x)["label"] for x in (tmp_path / "sdk_log.jsonl").read_text(encoding="utf-8").splitlines()]
    assert "canned" in labels
