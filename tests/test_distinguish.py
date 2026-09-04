"""The distinguish rung: a sheet that read as an already-bound character gets
its card rewritten on exactly the traits that matched, with objects the
model will draw -- not another seed on the same words."""
from __future__ import annotations

from studio import cast_card, distinguish
from studio.describe import TRAITS, TraitCard

CARD = {"headgear": "a brown bowler hat", "facial_hair": "clean-shaven",
        "garment": "a charcoal frock coat", "neckwear": "a soft turned-down collar",
        "age": "about forty", "hair": "dark hair swept back",
        "complexion": "a sallow complexion", "gender": "man"}
SEEN = TraitCard(age="middle-aged", hair_colour="dark brown", hair_length="short",
                 facial_hair="clean-shaven", headgear="bowler", complexion="sallow",
                 build="slight")


class TestCoarse:
    def test_every_pool_phrase_lands_on_its_trait_vocabulary(self):
        for slot, trait in distinguish.SLOT_TRAIT.items():
            for phrase in cast_card.POOLS[slot]:
                assert distinguish.coarse(slot, phrase) in TRAITS[trait], (slot, phrase)

    def test_coarse_reads_the_card_the_way_the_model_will(self):
        assert distinguish.coarse("hair", "dark hair swept back") == "dark brown"
        assert distinguish.coarse("headgear", "a bare head") == "none"
        assert distinguish.coarse("age", "about seventy") == "old"
        assert distinguish.coarse("complexion", "a sun-darkened face") == "dark"


class TestRewrite:
    def test_matched_slots_move_off_the_other_characters_value(self):
        new = distinguish.distinguish(CARD, ["hair_colour", "headgear", "age"], SEEN)
        assert distinguish.coarse("hair", new["hair"]) != "dark brown"
        assert distinguish.coarse("headgear", new["headgear"]) != "bowler"
        assert distinguish.coarse("age", new["age"]) != "middle-aged"
        assert new["facial_hair"] == CARD["facial_hair"] and new["garment"] == CARD["garment"]

    def test_a_phrase_another_character_holds_is_not_chosen(self):
        taken = {"hair": {"receding sandy hair", "close-cropped grey hair"}}
        new = distinguish.distinguish(CARD, ["hair_colour"], SEEN, taken)
        assert new["hair"] not in taken["hair"]
        assert distinguish.coarse("hair", new["hair"]) != "dark brown"

    def test_build_becomes_a_phrase_the_sheet_prompt_carries(self):
        new = distinguish.distinguish(CARD, ["build"], SEEN)
        assert new["build"] and "slight" not in new["build"]
        assert new["build"] in cast_card.render_card(new)

    def test_a_trait_with_no_slot_is_left_alone(self):
        assert distinguish.distinguish(CARD, ["hair_length"], SEEN) == CARD

    def test_the_rewrite_is_stable(self):
        once = distinguish.distinguish(CARD, ["hair_colour"], SEEN)
        assert once == distinguish.distinguish(CARD, ["hair_colour"], SEEN)
