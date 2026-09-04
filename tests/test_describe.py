"""A face read by a vision-language model into a trait card, and two cards
compared trait by trait.  The VLM is never called here: `run` is injected."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from studio import describe
from studio.describe import DISTINCT_AT, TRAITS, TraitCard

LESTRADE = {"age": "middle-aged", "hair_colour": "dark brown", "hair_length": "short",
            "facial_hair": "clean-shaven", "headgear": "bowler", "complexion": "sallow",
            "build": "slight", "description": "A lean, ferret-like man in a bowler hat."}
GREGSON = {**LESTRADE, "hair_colour": "fair", "complexion": "pale", "build": "stocky",
           "headgear": "none", "description": "A tall flaxen-haired man."}


def card(**changes) -> TraitCard:
    return TraitCard(**{**LESTRADE, **changes})


class TestVocabulary:
    def test_every_trait_has_a_closed_vocabulary_plus_unclear(self):
        assert set(TRAITS) == {"age", "hair_colour", "hair_length", "facial_hair",
                               "headgear", "complexion", "build"}
        assert all("unclear" in pool for pool in TRAITS.values())

    def test_a_value_is_normalised_onto_its_vocabulary(self):
        assert describe.nearest("hair_colour", " Dark Brown ") == "dark brown"
        assert describe.nearest("hair_colour", "greying") == "grey"
        assert describe.nearest("facial_hair", "a thick moustache") == "moustache"
        assert describe.nearest("age", "elderly") == "old"

    def test_a_value_off_the_vocabulary_is_refused(self):
        with pytest.raises(ValueError, match="hair_colour"):
            describe.nearest("hair_colour", "iridescent")

    def test_the_card_normalises_on_construction(self):
        made = card(hair_colour="Greying", facial_hair="a moustache")
        assert made.hair_colour == "grey" and made.facial_hair == "moustache"


class TestParse:
    def test_parses_the_json_object_out_of_prose(self):
        text = "Sure, here it is:\n```json\n" + json.dumps(LESTRADE) + "\n```\nDone."
        assert describe.parse_card(text) == card()

    def test_unwraps_the_list_of_strings_the_preview_node_reports(self):
        """PreviewAny prints the VQA node's output, a LIST of strings, as
        pretty JSON: the card is a JSON string inside a JSON list."""
        text = json.dumps([json.dumps(LESTRADE, indent=2)], indent=4)
        assert describe.parse_card(text) == card()

    def test_refuses_text_with_no_object(self):
        with pytest.raises(ValueError, match="no JSON"):
            describe.parse_card("I cannot see a person.")

    def test_the_prompt_names_every_trait_and_its_values(self):
        prompt = describe.prompt_for()
        assert all(trait in prompt for trait in TRAITS)
        assert "unclear" in prompt and "bowler" in prompt and "description" in prompt


class TestDescribe:
    def test_describe_stages_the_image_and_runs_the_caption_workflow(self, tmp_path, monkeypatch):
        image = tmp_path / "char-x.png"
        image.write_bytes(b"png")
        seen = {}
        monkeypatch.setattr(describe.comfy, "stage_image", lambda p: Path(p).name)

        def run(name, values, timeout):
            seen.update(name=name, values=values)
            return json.dumps(LESTRADE)
        found = describe.describe(image, seed=7, run=run)
        assert found == card()
        assert seen["name"] == describe.IMAGE_WORKFLOW
        assert seen["values"]["image_1"] == "char-x.png" and seen["values"]["seed"] == 7

    def test_describe_frames_sends_three_frames_to_the_video_workflow(self, tmp_path, monkeypatch):
        frames = [tmp_path / f"{i}.png" for i in range(3)]
        for f in frames:
            f.write_bytes(b"png")
        monkeypatch.setattr(describe.comfy, "stage_image", lambda p: Path(p).name)
        seen = {}

        def run(name, values, timeout):
            seen.update(name=name, values=values)
            return json.dumps(GREGSON)
        assert describe.describe_frames(frames, seed=3, run=run) == TraitCard(**GREGSON)
        assert seen["name"] == describe.VIDEO_WORKFLOW
        assert [seen["values"][f"frame_{i}"] for i in (1, 2, 3)] == ["0.png", "1.png", "2.png"]

    def test_describe_retries_once_on_unparseable_text(self, tmp_path, monkeypatch):
        image = tmp_path / "x.png"
        image.write_bytes(b"png")
        monkeypatch.setattr(describe.comfy, "stage_image", lambda p: Path(p).name)
        answers = iter(["no object here", json.dumps(LESTRADE)])
        seeds = []

        def run(name, values, timeout):
            seeds.append(values["seed"])
            return next(answers)
        assert describe.describe(image, seed=7, run=run) == card()
        assert seeds == [7, 8]


class TestCompare:
    def test_differences_names_the_traits_that_differ(self):
        assert describe.differences(card(), TraitCard(**GREGSON)) == [
            "hair_colour", "headgear", "complexion", "build"]

    def test_unclear_traits_are_not_compared(self):
        assert describe.differences(card(), card(hair_colour="unclear", build="heavy")) == ["build"]

    def test_shared_names_the_traits_both_see_alike(self):
        assert describe.shared(card(), card(hair_colour="unclear", build="heavy")) == [
            "age", "hair_length", "facial_hair", "headgear", "complexion"]

    def test_a_card_is_verifiable_when_it_sees_enough_traits(self):
        assert describe.verifiable(card())
        assert not describe.verifiable(card(age="unclear", build="unclear", headgear="unclear",
                                            hair_colour="unclear"))

    def test_known_counts_the_traits_a_card_can_vouch_for(self):
        assert describe.known(card()) == len(TRAITS)
        assert describe.known(card(age="unclear", build="unclear")) == len(TRAITS) - 2

    def test_same_look_is_fewer_than_distinct_at_differences(self):
        assert DISTINCT_AT == 3
        assert describe.same_look(card(), card(build="heavy", age="old"))
        assert not describe.same_look(card(), TraitCard(**GREGSON))

    def test_closest_is_the_bound_card_with_fewest_differences(self):
        bound = {"gregson": TraitCard(**GREGSON), "twin": card(build="heavy")}
        who, differing = describe.closest(card(), bound)
        assert who == "twin" and differing == ["build"]
        assert describe.closest(card(), {}) == (None, [])
