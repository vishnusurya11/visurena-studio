"""A face read by a vision-language model into a trait card, and two cards
compared trait by trait.  The VLM is never called here: `run` is injected."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from studio import describe
from studio.describe import DISTINCT_AT, TRAITS, TraitCard

LESTRADE = {"figure": "man", "age": "middle-aged", "hair_colour": "dark brown", "hair_length": "short",
            "facial_hair": "clean-shaven", "headgear": "bowler", "complexion": "sallow",
            "build": "slight", "description": "A lean, ferret-like man in a bowler hat."}
GREGSON = {**LESTRADE, "hair_colour": "fair", "complexion": "pale", "build": "stocky",
           "headgear": "none", "description": "A tall flaxen-haired man."}


def frames_in(folder: Path) -> list[Path]:
    """Three 40x30 frames: red, green, blue."""
    from PIL import Image
    frames = []
    for name, colour in (("0", (255, 0, 0)), ("1", (0, 255, 0)), ("2", (0, 0, 255))):
        frames.append(folder / f"{name}.png")
        Image.new("RGB", (40, 30), colour).save(frames[-1])
    return frames


def card(**changes) -> TraitCard:
    return TraitCard(**{**LESTRADE, **changes})


class TestVocabulary:
    def test_every_trait_has_a_closed_vocabulary_plus_unclear(self):
        assert set(TRAITS) == {"figure", "age", "hair_colour", "hair_length", "facial_hair",
                               "headgear", "complexion", "build"}
        assert all("unclear" in pool for pool in TRAITS.values())

    def test_a_value_is_normalised_onto_its_vocabulary(self):
        assert describe.nearest("hair_colour", " Dark Brown ") == "dark brown"
        assert describe.nearest("hair_colour", "greying") == "grey"
        assert describe.nearest("facial_hair", "a thick moustache") == "moustache"
        assert describe.nearest("age", "elderly") == "old"

    def test_a_vocabulary_word_inside_another_word_is_not_a_reading(self):
        """'flaxen-haired' read as RED: 'hai-red'.  A reading starts a word."""
        assert describe.nearest("hair_colour", "flaxen-haired") == "fair"
        assert describe.nearest("hair_colour", "grey-haired") == "grey"

    def test_unshaven_is_not_clean_shaven(self):
        """Gregson's card, 'a stubbled unshaven jaw', read as clean-shaven:
        'shaven' inside 'unshaven'.  Stubble is a beard's first day."""
        assert describe.nearest("facial_hair", "a stubbled unshaven jaw") == "beard"
        assert describe.nearest("facial_hair", "unshaven") == "beard"
        assert describe.nearest("facial_hair", "clean shaven") == "clean-shaven"
        assert describe.nearest("facial_hair", "shaven") == "clean-shaven"

    def test_a_value_off_the_vocabulary_is_refused(self):
        with pytest.raises(ValueError, match="hair_colour"):
            describe.nearest("hair_colour", "iridescent")

    def test_the_card_normalises_on_construction(self):
        made = card(hair_colour="Greying", facial_hair="a moustache")
        assert made.hair_colour == "grey" and made.facial_hair == "moustache"


    def test_a_card_without_a_figure_is_unclear_on_it(self):
        """Scarlet's cast was read before the trait existed: Jefferson Hope and
        Lucy Ferrier came out 2.0 apart -- a man and a woman -- because none of
        the seven traits was the figure itself.  Old cards still load."""
        assert TraitCard(**{k: v for k, v in LESTRADE.items() if k != "figure"}).figure == "unclear"
        assert describe.distance(card(figure="man"), card(figure="woman")) == 1.0
        assert describe.nearest("figure", "a young woman") == "woman"
        assert describe.nearest("figure", "male") == "man"


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

    def test_the_frames_prompt_says_the_frames_are_one_shot(self):
        prompt = describe.prompt_for(frames=3)
        assert "3 frames" in prompt and "same person" in prompt
        assert "one person in this image" not in prompt

    def test_the_prompt_can_single_out_one_of_two_people(self):
        prompt = describe.prompt_for(frames=3, whom="the man with the moustache")
        assert "the man with the moustache" in prompt and "ignore everyone else" in prompt
        assert "3 frames" in prompt and "same person" not in prompt
        assert all(trait in prompt for trait in TRAITS)


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

    def test_describe_frames_sends_one_contact_sheet_to_the_image_workflow(self, tmp_path, monkeypatch):
        """The Qwen3_VQA node reads image[0] of a batch, so the three-frame
        video workflow only ever described frame 1 (Scarlet run 4: a take
        whose first frame was hands holding a note came back 'face not
        visible' although two frames showed it).  One image the model
        provably sees whole: the frames side by side."""
        frames = frames_in(tmp_path)
        monkeypatch.setattr(describe.comfy, "stage_image", lambda p: Path(p).name)
        seen = {}

        def run(name, values, timeout):
            seen.update(name=name, values=values)
            return json.dumps(GREGSON)
        assert describe.describe_frames(frames, seed=3, run=run) == TraitCard(**GREGSON)
        assert seen["name"] == describe.IMAGE_WORKFLOW
        assert seen["values"]["image_1"] == f"{tmp_path.name}-contact.png"
        assert "3 frames" in seen["values"]["prompt"]

    def test_a_contact_sheet_lays_the_frames_side_by_side(self, tmp_path):
        from PIL import Image
        sheet = describe.contact_sheet(frames_in(tmp_path), tmp_path / "sheet.png")
        with Image.open(sheet) as made:
            assert made.size == (3 * 40, 30)
            assert made.getpixel((20, 15)) == (255, 0, 0)
            assert made.getpixel((100, 15)) == (0, 0, 255)

    def test_a_contact_sheet_scales_every_frame_to_the_shortest(self, tmp_path):
        from PIL import Image
        Image.new("RGB", (80, 60), (0, 255, 0)).save(tmp_path / "tall.png")
        frames = frames_in(tmp_path) + [tmp_path / "tall.png"]
        with Image.open(describe.contact_sheet(frames, tmp_path / "sheet.png")) as made:
            assert made.size == (3 * 40 + 40, 30)

    def test_the_frames_path_frees_the_engine_before_asking(self, tmp_path, monkeypatch):
        """Scarlet run 4 died in step 07: with H3's DiT and text encoder still
        staged, Qwen3-VL loaded offloaded to CPU -- 6:52 to load, 10:23 in all,
        past the 600s gate timeout.  Resident, it answers in about a minute."""
        frames = frames_in(tmp_path)
        order = []
        monkeypatch.setattr(describe.comfy, "stage_image", lambda p: Path(p).name)
        monkeypatch.setattr(describe.comfy, "free_models", lambda: order.append("free"))
        monkeypatch.setattr(describe.comfy, "run_text",
                            lambda name, values, timeout: order.append("ask") or json.dumps(LESTRADE))
        assert describe.describe_frames(frames) == card()
        assert order == ["free", "ask"]

    def test_one_reader_frees_the_engine_once_for_a_whole_round_of_takes(self, tmp_path, monkeypatch):
        """The swap, not the compute, was the cycle: freeing before EVERY read
        unloaded H3's DiT, text encoder and VAEs after every take, and run 10
        paid 8.3 of every 15.76 minutes re-streaming 16 GB off a spinning
        disk.  A round of takes is read by ONE reader: unload once, answer
        while resident."""
        frames = frames_in(tmp_path)
        order = []
        monkeypatch.setattr(describe.comfy, "stage_image", lambda p: Path(p).name)
        monkeypatch.setattr(describe.comfy, "free_models", lambda: order.append("free"))
        monkeypatch.setattr(describe.comfy, "run_text",
                            lambda name, values, timeout: order.append("ask") or json.dumps(LESTRADE))
        reader = describe.reader()
        for _ in range(3):
            assert describe.describe_frames(frames, run=reader) == card()
        assert order == ["free", "ask", "ask", "ask"]

    def test_a_reader_nobody_asks_unloads_nothing(self, monkeypatch):
        """A round with no face to read costs no swap: the unload waits for
        the first question."""
        order = []
        monkeypatch.setattr(describe.comfy, "free_models", lambda: order.append("free"))
        describe.reader()
        assert order == []

    def test_the_still_path_leaves_the_engine_loaded(self, tmp_path, monkeypatch):
        """Scarlet run 5 died in step 02 the other way: freeing before every
        sheet read evicted Qwen3-VL too, and each read re-streamed 16 GB off
        the spinning disk the models live on -- 4s resident, then 3:52, 2:13,
        10:06.  Only H3's staged models force the eviction; a sheet is read
        beside the image model, which fits."""
        image = tmp_path / "x.png"
        image.write_bytes(b"png")
        order = []
        monkeypatch.setattr(describe.comfy, "stage_image", lambda p: Path(p).name)
        monkeypatch.setattr(describe.comfy, "free_models", lambda: order.append("free"))
        monkeypatch.setattr(describe.comfy, "run_text",
                            lambda name, values, timeout: order.append("ask") or json.dumps(LESTRADE))
        assert describe.describe(image) == card()
        assert order == ["ask"]

    def test_patiently_returns_the_card_or_an_unseen_one_after_interrupting(self, monkeypatch):
        """Retry within the time frame, then degrade and ship: the job is
        interrupted so it cannot hold the queue, the caller is told, the
        read comes back unseen."""
        stopped, told = [], []
        monkeypatch.setattr(describe.comfy, "interrupt", lambda: stopped.append(True))
        assert describe.patiently(card, told.append) == card()
        assert stopped == [] and told == []

        def slow():
            raise TimeoutError("job-9 still running after 600.0s")
        assert describe.patiently(slow, told.append) == describe.unseen()
        assert stopped == [True] and told == ["job-9 still running after 600.0s"]

    def test_unseen_is_a_card_that_vouches_for_nothing(self):
        assert describe.known(describe.unseen()) == 0
        assert not describe.verifiable(describe.unseen())

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
            "figure", "age", "hair_length", "facial_hair", "headgear", "complexion"]

    def test_a_card_is_verifiable_when_it_sees_enough_traits(self):
        """Five of eight: the figure is readable on almost any distant back,
        so it must not tip a turned-away figure into verifiable."""
        assert describe.VERIFIABLE_FROM == 5
        assert describe.verifiable(card())
        assert not describe.verifiable(card(age="unclear", build="unclear", headgear="unclear",
                                            hair_colour="unclear"))

    def test_known_counts_the_traits_a_card_can_vouch_for(self):
        assert describe.known(card()) == len(TRAITS)
        assert describe.known(card(age="unclear", build="unclear")) == len(TRAITS) - 2

    def test_a_one_notch_drift_on_an_ordered_trait_is_half_a_difference(self):
        """Scarlet run 4, take B02: the contact sheet read Holmes as
        middle-aged/grey/top hat against a reference of old/white/bowler --
        three differences, two of them one notch along an ordered scale."""
        assert describe.distance(card(), card(age="old")) == 0.5
        assert describe.distance(card(), card(hair_colour="brown")) == 0.5
        assert describe.distance(card(), card(hair_colour="fair")) == 1.0
        assert describe.distance(card(), card(headgear="top hat")) == 1.0
        assert describe.distance(card(), TraitCard(**GREGSON)) == 4.0

    def test_a_hat_the_vocabulary_aliases_is_half_a_difference(self):
        """Scarlet run 4, 7 of 7 sheets: a deerstalker read as 'cap', a tall
        beaver hat as 'top hat'.  The channel's word for the hat, not a
        different hat -- and not a render disobeying its card."""
        assert describe.distance(card(headgear="deerstalker"), card(headgear="cap")) == 0.5
        assert describe.distance(card(headgear="other hat"), card(headgear="top hat")) == 0.5
        assert describe.distance(card(headgear="bowler"), card(headgear="cap")) == 1.0

    def test_same_look_is_a_distance_under_distinct_at(self):
        assert DISTINCT_AT == 3
        assert describe.same_look(card(), card(build="heavy", age="old"))
        assert describe.same_look(card(), card(age="old", hair_colour="brown", headgear="top hat"))
        assert not describe.same_look(card(), TraitCard(**GREGSON))

    def test_closest_is_the_bound_card_with_fewest_differences(self):
        bound = {"gregson": TraitCard(**GREGSON), "twin": card(build="heavy")}
        who, differing = describe.closest(card(), bound)
        assert who == "twin" and differing == ["build"]
        assert describe.closest(card(), {}) == (None, [])

    def test_closest_measures_by_distance_not_by_count(self):
        bound = {"three_notches": card(age="old", hair_colour="brown", build="average"),
                 "one_clear": card(headgear="none")}
        assert describe.closest(card(), bound)[0] == "one_clear"
