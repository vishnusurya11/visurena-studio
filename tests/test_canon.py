"""The look the world already knows a character by.

Scarlet run 7: the book is silent on Holmes's face (in 1887 nobody needed
telling), the portrait step honestly left age, hair, facial hair and headgear
empty, and the card INVENTED them from the rotation -- a walrus moustache, a
brown bowler, about forty.  Run 6 had given him white hair worn long.  Every
clip was conditioned on a man who is not Sherlock Holmes.  Silence in the
text is not licence when the audience already knows the face: the known look
outranks invention, and the book's own words outrank the known look.
"""
from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from studio import canon, cast_card
from studio.canon import Canon
from studio.distinguish import coarse

HOLMES = {"id": "sherlock_holmes", "name": "Sherlock Holmes", "aliases": ["Holmes"]}
STAMFORD = {"id": "stamford", "name": "Stamford", "aliases": ["young Stamford"]}
BOOK = {"title": "A Study in Scarlet", "author": "Arthur Conan Doyle"}
KNOWN = Canon(known=True, source="Paget's Strand illustrations; the canon",
              age="in his late twenties", hair="dark hair swept back",
              facial_hair="clean-shaven", complexion="a pale indoor complexion",
              build="tall and excessively lean")


class FakeLLM:
    def __init__(self, *answers):
        self.answers, self.prompts = list(answers), []

    def __call__(self, tier, prompt, schema, **kw):
        self.prompts.append(prompt)
        return self.answers.pop(0)


class TestCanon:
    def test_an_unknown_character_carries_no_traits(self):
        with pytest.raises(ValidationError, match="invention"):
            Canon(known=False, facial_hair="a full dark beard")

    def test_an_unknown_character_is_empty(self):
        assert Canon().known is False and Canon().facial_hair == ""


class TestPrompt:
    def test_the_prompt_names_the_character_the_book_and_the_closed_vocabulary(self):
        prompt = canon.prompt_for(HOLMES, BOOK)
        assert "Sherlock Holmes" in prompt and "A Study in Scarlet" in prompt
        assert "Arthur Conan Doyle" in prompt and "Holmes" in prompt
        for slot in canon.SLOTS:
            for phrase in cast_card.POOLS.get(slot, ()):
                assert phrase in prompt, (slot, phrase)

    def test_the_prompt_asks_for_the_look_at_the_time_of_this_book(self):
        prompt = canon.prompt_for(HOLMES, BOOK)
        assert "at the time of this book" in prompt.lower()
        assert "known" in prompt and "false" in prompt


BEARDED = KNOWN.model_copy(update={"facial_hair": "a short pointed beard", "headgear": "a black silk top hat"})
BARE = KNOWN.model_copy(update={"headgear": "bare head"})


class TestAgree:
    """Measured on Watson (2026-09-05, three asks): a short pointed beard,
    then nothing, then a thin waxed moustache -- the model was guessing, and
    one guess would have been asserted on every clip.  Holmes came back
    clean-shaven, dark, late twenties three times out of three.  Agreement
    is what knowledge looks like from outside; a slot the answers disagree
    on is left empty."""

    def test_a_slot_the_answers_agree_on_is_kept(self):
        agreed = canon.agree([KNOWN, BEARDED, KNOWN])
        assert agreed.facial_hair == "clean-shaven" and agreed.hair == "dark hair swept back"

    def test_a_slot_the_answers_disagree_on_is_left_empty(self):
        agreed = canon.agree([KNOWN, BEARDED, BARE])
        assert agreed.facial_hair == "clean-shaven"  # two of three
        assert agreed.headgear == ""  # empty, top hat, bare: no majority

    def test_agreement_is_by_reading_not_spelling(self):
        assert canon.agree([BARE, BARE.model_copy(update={"headgear": "a bare head"}), KNOWN]
                           ).headgear in ("bare head", "a bare head")

    def test_known_is_a_majority_too(self):
        assert canon.agree([KNOWN, Canon(), Canon()]) == Canon()
        assert canon.agree([KNOWN, KNOWN, Canon()]).known is True

    def test_build_and_source_come_from_the_first_answer_that_knows(self):
        agreed = canon.agree([Canon(), KNOWN, BEARDED])
        assert agreed.build == KNOWN.build and agreed.source == KNOWN.source


class TestTier:
    def test_the_canon_is_asked_of_its_own_thinking_tier(self):
        from studio.llm import resolve_tier
        resolved = resolve_tier(canon.TIER)
        assert canon.TIER == "canon"
        assert resolved["params"].get("reasoning_effort") == "high"


class TestAsk:
    def test_the_model_is_asked_three_times_and_the_agreement_kept(self, monkeypatch):
        fake = FakeLLM(KNOWN, BEARDED, KNOWN)
        monkeypatch.setattr(canon.llm, "structured", fake)
        assert canon.ask(HOLMES, BOOK) == KNOWN
        assert len(fake.prompts) == canon.ASKS == 3

    def test_a_refused_answer_counts_as_not_knowing(self, monkeypatch):
        calls = []

        def refuse(tier, prompt, schema, **kw):
            calls.append(prompt)
            raise ValueError("invention")
        monkeypatch.setattr(canon.llm, "structured", refuse)
        assert canon.ask(STAMFORD, BOOK) == Canon() and len(calls) == 3


class TestCanonsFor:
    def with_book(self, tmp_path):
        (tmp_path / "source").mkdir()
        (tmp_path / "source/book.json").write_text(json.dumps(BOOK), encoding="utf-8")
        return tmp_path

    def test_one_ask_per_character_kept_in_refs_canon_json(self, tmp_path, monkeypatch):
        book = self.with_book(tmp_path)
        fake = FakeLLM(*[KNOWN] * 3, *[Canon()] * 3)
        monkeypatch.setattr(canon.llm, "structured", fake)
        looks = canon.canons_for(book, {"sherlock_holmes": HOLMES, "stamford": STAMFORD})
        assert looks["sherlock_holmes"] == KNOWN and looks["stamford"] == Canon()
        kept = json.loads((book / "refs/canon.json").read_text(encoding="utf-8"))
        assert kept["sherlock_holmes"]["facial_hair"] == "clean-shaven"
        canon.canons_for(book, {"sherlock_holmes": HOLMES, "stamford": STAMFORD})
        assert len(fake.prompts) == 6  # cached: nothing asked again

    def test_a_book_without_source_metadata_asks_nothing(self, tmp_path, monkeypatch):
        fake = FakeLLM()
        monkeypatch.setattr(canon.llm, "structured", fake)
        looks = canon.canons_for(tmp_path, {"sherlock_holmes": HOLMES})
        assert looks == {"sherlock_holmes": Canon()} and fake.prompts == []


class TestKnownLook:
    def test_a_known_look_fills_the_card_slots_in_pool_phrases(self):
        look = canon.known_look(KNOWN)
        assert look["facial_hair"] == "clean-shaven"
        assert look["hair"] == "dark hair swept back"
        assert look["age"] == "in his late twenties"
        assert look["build"] == "tall and excessively lean"
        assert "headgear" not in look  # the tradition varies; left to the card

    def test_an_unknown_look_fills_nothing(self):
        assert canon.known_look(Canon()) == {}

    def test_a_phrase_off_the_pool_is_kept_when_the_reader_reads_it_whole(self):
        look = canon.known_look(Canon(known=True, hair="short brown hair", facial_hair="a moustache"))
        assert coarse("hair", look["hair"], "hair_colour") == "brown"
        assert coarse("facial_hair", look["facial_hair"]) == "moustache"

    def test_a_phrase_the_reader_cannot_read_states_nothing(self):
        assert canon.known_look(Canon(known=True, complexion="a frightened face")) == {}


class TestOnTheCard:
    """The whole point: Holmes's card, with the book silent, is clean-shaven
    and young, and those slots are OWED by the render -- not invented."""

    def test_the_known_look_fills_what_the_book_left_empty(self):
        cards = cast_card.cards_for(["sherlock_holmes"], {"sherlock_holmes": ""},
                                    stated={"sherlock_holmes": canon.known_look(KNOWN)},
                                    known={"sherlock_holmes"})
        card = cards["sherlock_holmes"]
        assert card["facial_hair"] == "clean-shaven" and card["age"] == "in his late twenties"
        assert {"facial_hair", "hair", "age", "complexion"} <= set(card["asserted"])

    def test_a_known_face_is_never_given_an_invented_beard_or_hair(self):
        """Watson: known, but the answers agreed on nothing but his age.  The
        rotation would hand him a full dark beard and thinning red hair --
        that is not a Watson nobody described, it is a different man.  A
        face the audience knows gets nothing ADDED by invention: clean-shaven
        and the plainest hair of his years."""
        agreed = {"age": "about thirty-five"}
        cards = cast_card.cards_for(["john_watson", "tobias_gregson"],
                                    {"john_watson": "", "tobias_gregson": ""},
                                    stated={"john_watson": agreed}, known={"john_watson"})
        watson, gregson = cards["john_watson"], cards["tobias_gregson"]
        assert watson["facial_hair"] == "clean-shaven"
        assert watson["hair"] == cast_card.BANDED["middle"]["hair"][0]
        assert gregson["facial_hair"] != "clean-shaven" or gregson["hair"] != watson["hair"]

    def test_a_known_face_owns_its_identity_slots(self):
        """Scarlet run 8: Lestrade's neutral clean-shaven and thinning red
        hair were 'movable if the pixels collide', the pixels collided with
        Watson, and the rung made him seventy, white-haired and bearded.  On
        a known face the neutral slots are the character's, as the book's
        words would be: the render OWES them, no rung moves them, and a
        sheet that draws grey on fair is refused rather than adopted."""
        cards = cast_card.cards_for(["john_watson"], {"john_watson": ""},
                                    stated={"john_watson": {"age": "in his late twenties"}},
                                    known={"john_watson"})
        assert {"facial_hair", "hair", "age"} <= set(cards["john_watson"]["asserted"])
        stranger = cast_card.cards_for(["stamford"], {"stamford": ""})["stamford"]
        assert "hair" not in stranger["asserted"]

    def test_a_stranger_is_still_invented_from_the_rotation(self):
        card = cast_card.cards_for(["stamford"], {"stamford": ""})["stamford"]
        assert card["facial_hair"] in cast_card.FACIAL_HAIR and card["hair"] in cast_card.HAIR


class TestMoveOffNeutral:
    def test_the_first_move_off_clean_shaven_is_a_moustache_not_a_beard(self):
        from studio.distinguish import _move
        moved = _move("facial_hair", "clean-shaven", {"facial_hair": "clean-shaven"}, set())
        assert "moustache" in moved
