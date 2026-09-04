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
        for slot, traits in distinguish.SLOT_TRAITS.items():
            for trait in traits:
                for phrase in cast_card.POOLS[slot]:
                    assert distinguish.coarse(slot, phrase, trait) in TRAITS[trait], (slot, phrase)

    def test_coarse_reads_the_card_the_way_the_model_will(self):
        assert distinguish.coarse("hair", "dark hair swept back") == "dark brown"
        assert distinguish.coarse("headgear", "a bare head") == "none"
        assert distinguish.coarse("age", "about seventy") == "old"
        assert distinguish.coarse("complexion", "a sun-darkened face") == "dark"

    def test_the_hair_phrase_reads_as_a_length_too(self):
        """Scarlet run 6: Lestrade's sheet shared hair_length with Hope on
        rungs 1 and 4, and the rung could not move it -- no slot read as a
        length, though every hair phrase carries one."""
        assert distinguish.coarse("hair", "close-cropped grey hair", "hair_length") == "short"
        assert distinguish.coarse("hair", "dark hair swept back", "hair_length") == "medium"
        assert distinguish.coarse("hair", "white hair worn long", "hair_length") == "long"
        assert distinguish.coarse("hair", "a bald crown with grey at the temples", "hair_length") == "bald"

    def test_expected_is_the_card_the_model_should_read_off_a_faithful_render(self):
        seen = distinguish.expected(CARD)
        assert seen.figure == "man" and seen.age == "middle-aged"
        assert seen.hair_colour == "dark brown" and seen.hair_length == "medium"
        assert seen.facial_hair == "clean-shaven" and seen.headgear == "bowler"
        assert seen.complexion == "sallow" and seen.build == "unclear"
        assert distinguish.expected({**CARD, "build": "a heavy stout frame"}).build == "heavy"
        assert distinguish.expected({**CARD, "gender": "person"}).figure == "unclear"

    def test_disobeyed_names_the_reliable_traits_the_render_ignored(self):
        """Scarlet run 4's seven sheets: complexion read 'fair' on seven
        different card phrases, build 'average' on all, age followed the
        hair colour -- the channel cannot express those.  Hair, facial hair
        and headgear it can (6-7 of 7, within a notch), so only they can be
        disobeyed; one notch is the same face at another distance."""
        assert distinguish.RELIABLE == ("hair_colour", "hair_length", "facial_hair", "headgear")
        faithful = distinguish.expected(CARD)
        assert distinguish.disobeyed(CARD, faithful) == []
        assert distinguish.disobeyed(CARD, faithful.model_copy(update={
            "complexion": "fair", "age": "old", "build": "heavy"})) == []
        assert distinguish.disobeyed(CARD, faithful.model_copy(update={"hair_colour": "brown"})) == []
        assert distinguish.disobeyed(CARD, faithful.model_copy(update={
            "facial_hair": "moustache", "headgear": "unclear", "hair_colour": "fair"})) == [
            "hair_colour", "facial_hair"]


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

    def test_a_shared_hair_length_moves_the_hair_phrase(self):
        new = distinguish.distinguish(CARD, ["hair_length"], SEEN)
        assert distinguish.coarse("hair", new["hair"], "hair_length") != "short"
        assert new["headgear"] == CARD["headgear"]

    def test_a_hair_phrase_moves_off_every_matched_reading_at_once(self):
        new = distinguish.distinguish(CARD, ["hair_colour", "hair_length"], SEEN)
        assert distinguish.coarse("hair", new["hair"], "hair_colour") != "dark brown"
        assert distinguish.coarse("hair", new["hair"], "hair_length") != "short"

    def test_a_trait_with_no_slot_is_left_alone(self):
        assert distinguish.distinguish(CARD, ["figure"], SEEN) == CARD

    def test_the_book_line_is_dropped_when_it_asserts_a_moved_trait(self):
        """The sheet prompt ends with the book's own sentence.  A card moved to
        'a full beard' that still ends 'with a heavy walrus moustache' tells
        the model two things, and it obeys whichever it likes."""
        told = {**CARD, "facial_hair": "a heavy walrus moustache",
                "book": "A thin man with a heavy walrus moustache and fair hair."}
        other = SEEN.model_copy(update={"facial_hair": "moustache"})
        moved = distinguish.distinguish(told, ["facial_hair"], other)
        assert moved["facial_hair"] != told["facial_hair"] and moved["book"] == ""
        assert "walrus" not in cast_card.render_card(moved)

    def test_the_book_line_stays_when_it_is_silent_on_the_moved_trait(self):
        told = {**CARD, "book": "A thin man with fair hair."}
        moved = distinguish.distinguish(told, ["headgear"], SEEN)
        assert moved["headgear"] != told["headgear"] and moved["book"] == told["book"]

    def test_the_rewrite_is_stable(self):
        once = distinguish.distinguish(CARD, ["hair_colour"], SEEN)
        assert once == distinguish.distinguish(CARD, ["hair_colour"], SEEN)


class TestOwed:
    """Scarlet run 7: Holmes's card said 'receding sandy hair' from the
    rotation, the render put dark hair under his bowler four times, and the
    gate refused every sheet -- the lead went unbound over an invention.
    A render owes the book, not the rotation."""
    INVENTED = {**CARD, "asserted": []}
    ASSERTED = {**CARD, "asserted": ["hair", "facial_hair", "headgear"]}
    DRAWN = SEEN.model_copy(update={"hair_colour": "dark brown", "hair_length": "short"})

    def test_only_an_asserted_slot_can_be_disobeyed(self):
        faithful = distinguish.expected(CARD)
        drifted = faithful.model_copy(update={"hair_colour": "fair", "facial_hair": "moustache"})
        assert distinguish.disobeyed(self.ASSERTED, drifted) == ["hair_colour", "facial_hair"]
        assert distinguish.disobeyed({**CARD, "asserted": ["facial_hair"]}, drifted) == ["facial_hair"]
        assert distinguish.disobeyed(self.INVENTED, drifted) == []

    def test_a_card_without_the_field_owes_every_reliable_trait(self):
        drifted = distinguish.expected(CARD).model_copy(update={"hair_colour": "fair"})
        assert distinguish.disobeyed(CARD, drifted) == ["hair_colour"]

    def test_adopt_moves_an_invented_slot_to_what_was_drawn(self):
        card = {**CARD, "hair": "receding sandy hair", "asserted": ["facial_hair"]}
        new = distinguish.adopt(card, self.DRAWN)
        assert new["hair"] == "dark hair swept back"  # the pool's one dark-brown phrase
        assert new["facial_hair"] == card["facial_hair"] and new["headgear"] == card["headgear"]
        exact = self.DRAWN.model_copy(update={"hair_colour": "grey", "hair_length": "bald"})
        assert distinguish.adopt(card, exact)["hair"] == "a bald crown with grey at the temples"

    def test_adopt_leaves_an_asserted_slot_and_an_unread_one_alone(self):
        card = {**CARD, "hair": "receding sandy hair", "asserted": ["hair"]}
        assert distinguish.adopt(card, self.DRAWN) == card
        blind = self.DRAWN.model_copy(update={"hair_colour": "unclear", "hair_length": "unclear"})
        assert distinguish.adopt({**card, "asserted": []}, blind) == {**card, "asserted": []}
