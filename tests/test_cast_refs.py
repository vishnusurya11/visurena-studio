"""One character, one invariant caption, one state sentence per wardrobe state,
two pictures.  No model, no network, no credit."""
import json

import pytest

from studio import cast_refs
from studio.episode_spec import Setup

ROW = {"ref_id": "char-john_watson", "kind": "character", "entity_id": "john_watson",
       "name": "Dr. John Watson",
       "physical": "A man in his late twenties, as thin as a lath.",
       "wardrobe": {"outdoor": "wears the brown bowler hat squarely on his head",
                    "indoor": "is bare-headed and carries the brown bowler in his left hand"},
       "rel_path": "refs/characters/char-john_watson.png",
       "cards": {"outdoor": "refs/characters/char-john_watson_outdoor.png",
                 "indoor": "refs/characters/char-john_watson_indoor.png"},
       "identity": {"traits": {"headgear": "none"}}}


def a_book(tmp_path, rows=(ROW,), pictures=()):
    (tmp_path / "refs" / "characters").mkdir(parents=True)
    for name in pictures:
        (tmp_path / "refs" / "characters" / name).write_bytes(b"png")
    (tmp_path / "refs" / "refs.json").write_text(
        json.dumps({"book_id": "b", "palette": "p", "refs": list(rows)}), encoding="utf-8")
    return tmp_path


class TestTheSetupDeclaresItsWardrobeState:
    def test_the_two_states_are_the_two_sides_of_one_declared_fact(self):
        assert Setup(described="a lab").state == "indoor"
        assert Setup(described="a street", outdoors=True).state == "outdoor"

    def test_every_state_a_setup_can_be_in_has_a_card_slot(self):
        assert set(cast_refs.STATES) == {"indoor", "outdoor"}
        assert Setup(described="x", outdoors=True).state in cast_refs.STATES


class TestTheRow:
    def test_a_character_is_found_by_the_entity_id_the_plan_uses(self, tmp_path):
        book = a_book(tmp_path)
        assert cast_refs.row(book, "john_watson")["name"] == "Dr. John Watson"

    def test_a_character_the_book_never_bound_is_a_hard_error(self, tmp_path):
        with pytest.raises(KeyError):
            cast_refs.row(a_book(tmp_path), "stamford")

    def test_the_state_sentence_is_chosen_by_the_setups_state(self, tmp_path):
        row = cast_refs.row(a_book(tmp_path), "john_watson")
        assert cast_refs.wardrobe(row, "outdoor").startswith("wears the brown bowler")
        assert cast_refs.wardrobe(row, "indoor").startswith("is bare-headed")

    def test_an_undeclared_state_reads_as_silence_not_as_the_other_state(self, tmp_path):
        row = dict(cast_refs.row(a_book(tmp_path), "john_watson"), wardrobe={})
        assert cast_refs.wardrobe(row, "indoor") == ""


class TestTheTwoPictures:
    def test_the_bust_comes_first_and_the_state_card_second(self, tmp_path):
        book = a_book(tmp_path, pictures=("char-john_watson.png",
                                          "char-john_watson_indoor.png"))
        got = cast_refs.cast_sheets(book, "john_watson", "indoor")
        assert [p.name for p in got] == ["char-john_watson.png", "char-john_watson_indoor.png"]

    def test_a_character_with_no_card_yet_is_still_bound_by_his_bust(self, tmp_path):
        book = a_book(tmp_path, pictures=("char-john_watson.png",))
        assert [p.name for p in cast_refs.cast_sheets(book, "john_watson", "outdoor")] == \
               ["char-john_watson.png"]

    def test_two_faces_at_two_pictures_each_fit_the_eight_reference_slots(self, tmp_path):
        book = a_book(tmp_path, pictures=("char-john_watson.png",
                                          "char-john_watson_indoor.png"))
        refs = [p for _ in range(cast_refs.MAX_FACES)
                for p in cast_refs.cast_sheets(book, "john_watson", "indoor")]
        assert len(refs) + 2 <= cast_refs.REF_SLOTS      # + the plate and the strip


class TestTheSubjectLine:
    def test_the_invariant_caption_and_the_state_are_two_sentences_not_a_conditional(self, tmp_path):
        row = cast_refs.row(a_book(tmp_path), "john_watson")
        said = cast_refs.subject_text(row, "indoor")
        assert said.startswith("A man in his late twenties")
        assert said.endswith("in this scene he is bare-headed and carries the brown bowler "
                             "in his left hand.")
        assert "outdoors" not in said and "indoors" not in said
