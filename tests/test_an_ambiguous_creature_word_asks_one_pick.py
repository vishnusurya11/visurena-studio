"""A bare creature word with >= 2 candidate machine cards takes ONE workhorse
pick (studio/stage_pick), rails and all: the schema refuses a pid outside the
candidates so llm.structured's re-ask ladder fires, and pick_machine double
checks whatever comes back -- fake or real.  `_structured` is the test seam;
zero network, zero spend."""
from __future__ import annotations

import pytest
from strands.types.exceptions import StructuredOutputException

from studio import stage_pick

CANDS = [{"pid": "fighting_machine", "name": "the Martian fighting-machine",
          "physical": "A walking engine. Higher than houses. Three jointed legs.",
          "aliases": ["tripod"]},
         {"pid": "handling_machine", "name": "the Martian handling-machine",
          "physical": "A crab-like machine. It digs and handles.", "aliases": ["crab"]}]


def test_the_fakes_pick_feeds_the_rename():
    def fake(tier, prompt, schema, retries=3):
        assert tier == "workhorse"
        assert "a Martian digging" in prompt and "handling_machine" in prompt
        assert "tripod" in prompt                 # the aliases travel in the candidates
        return stage_pick.MachinePick(pid="handling_machine")
    got = stage_pick.pick_machine("a Martian digging the pit", CANDS, term="martian",
                                  book_title="The War of the Worlds", _structured=fake)
    assert got == "handling_machine"


def test_a_pick_outside_the_candidates_refuses_even_from_a_fake():
    def fake(tier, prompt, schema, retries=3):
        return stage_pick.MachinePick(pid="thunder_child")
    with pytest.raises(StructuredOutputException, match="thunder_child"):
        stage_pick.pick_machine("a Martian digging", CANDS, _structured=fake)


def test_the_schema_itself_refuses_an_unknown_pid_for_the_re_ask_ladder():
    model = stage_pick.pick_model(["fighting_machine", "handling_machine"])
    with pytest.raises(Exception, match="candidates"):
        model(pid="thunder_child")
    assert model(pid="fighting_machine").pid == "fighting_machine"


def test_write_sheet_prompt_rides_the_same_seam():
    said = ("A glittering walking engine centered on a plain neutral ground, every "
            "leg joint and the brazen hood stated, no scene, no people, no text.")

    def fake(tier, prompt, schema, retries=3):
        assert tier == "workhorse"
        assert "reference-sheet prompt" in prompt and "ex one" in prompt
        return stage_pick.SheetPrompt(prompt=said)
    card = {"id": "x", "name": "the x", "kind": "machine",
            "profile": {"physical": "A walker.", "scale": "Huge."}}
    assert stage_pick.write_sheet_prompt(card, ["ex one", "ex two"], _structured=fake) == said


def test_a_sheet_prompt_under_forty_chars_is_unrepresentable():
    with pytest.raises(Exception):
        stage_pick.SheetPrompt(prompt="too short")
