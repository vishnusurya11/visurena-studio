"""Every book has a look timeline (verdict S, fact 2: `wardrobe_by_chapter`
exists in 0 dossiers outside WotW).  The look-timeline writer reads the script
supervisor's `state_changes` and returns looks; code keeps a non-base look only
when its quote is found in the chapter at 0.85 (the G-SOURCE matcher), and
writes the table.  The model is a FakeModel: no test spends."""
from __future__ import annotations

import json

import pytest
from strands.types.exceptions import StructuredOutputException

from agents import look_timeline_writer as writer
from studio import look_timeline as lt
from tests.test_episode_writer import FakeModel

# The keys of a real dossier (analysis/characters/*.json): `appearances` is a COUNT and
# `first_chapter` the chapter (C2_verdict #6: a list typed here hid a crash).
CARD = {"id": "griffin", "name": "Griffin", "first_chapter": 1, "appearances": 3,
        "profile": {"physical": "Tall man, thin. Pale fair hair cut short. Clean-shaven.",
                    "physical_evolution": [{"chapter": 3, "change": "His face is bandaged."}]},
        "state_changes": [
            {"chapter": 3, "scene": 1, "subtype": "injury", "change": "He wraps his head in bandages.",
             "evidence": "his whole head was swathed in white bandages"},
            {"chapter": 2, "scene": 1, "subtype": "knowledge", "change": "He learns the price.",
             "evidence": "he asked what it would cost"}]}
CHAPTERS = {1: "The stranger came early in February.",
            2: "He asked what it would cost and paid.",
            3: "She saw that his whole head was swathed in white bandages and goggles."}


def draft(quote3: str = "his whole head was swathed in white bandages") -> dict:
    return {"looks": [
        {"look_id": "travel_coat", "start_chapter": 1, "top": "heavy dark overcoat, gloves",
         "headwear": "wide-brimmed felt hat", "quote": "", "quote_chapter": 1},
        {"look_id": "bandaged", "start_chapter": 3, "start_scene": 1, "headwear": "white bandages round the whole head",
         "top": "heavy dark overcoat, gloves", "quote": quote3, "quote_chapter": 3},
        {"look_id": "invented_cloak", "start_chapter": 2, "top": "a scarlet cloak",
         "quote": "he flung on a scarlet cloak", "quote_chapter": 2}]}


def test_a_look_whose_quote_is_in_the_chapter_is_kept_and_an_invented_one_dropped():
    looks = lt.looks_from_draft(writer.LookDraft.model_validate(draft()), CARD, CHAPTERS.get)
    assert sorted(looks.looks) == ["bandaged", "travel_coat"]
    assert looks.base == "travel_coat" and looks.look_id_at(3, 1) == "bandaged"
    assert looks.looks["bandaged"].source[0].quote.startswith("his whole head")


def test_the_body_carries_no_hair_and_the_markers_are_closed():
    looks = lt.looks_from_draft(writer.LookDraft.model_validate(draft()), CARD, CHAPTERS.get)
    assert "hair" not in looks.body and "Clean-shaven" not in looks.body
    assert looks.looks["travel_coat"].markers.headwear == "felt_hat"
    assert looks.looks["travel_coat"].markers.hair_colour == "fair"       # the body's, not restated


def test_the_prompt_carries_the_appearance_ledger_only():
    fake = FakeModel(draft())
    writer.write(lt.dossier_text(CARD), _agent=fake)
    assert "swathed in white bandages" in fake.prompts[0]
    assert "what it would cost" not in fake.prompts[0]


def test_one_schema_violation_is_retried():
    fake = FakeModel(StructuredOutputException("no structured output"), draft())
    assert writer.write(lt.dossier_text(CARD), _agent=fake).looks[0].look_id == "travel_coat"
    assert len(fake.prompts) == 2


def test_the_table_is_written_under_refs_and_merged(tmp_path):
    looks = lt.looks_from_draft(writer.LookDraft.model_validate(draft()), CARD, CHAPTERS.get)
    lt.write_looks(tmp_path, "griffin", looks)
    lt.write_looks(tmp_path, "kemp", looks)
    doc = json.loads((tmp_path / "refs" / "looks.json").read_text(encoding="utf-8"))
    assert sorted(doc["characters"]) == ["griffin", "kemp"]
    assert lt.load(tmp_path).look_id_at("griffin", 3) == "bandaged"


def test_a_book_with_no_table_loads_none(tmp_path):
    assert lt.load(tmp_path) is None


@pytest.mark.parametrize("bad", ["", "a bandage appeared"])
def test_a_non_base_look_without_a_found_quote_never_lands(bad):
    looks = lt.looks_from_draft(writer.LookDraft.model_validate(draft(quote3=bad)), CARD, CHAPTERS.get)
    assert "bandaged" not in looks.looks
