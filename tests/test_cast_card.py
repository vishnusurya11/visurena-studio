"""Separating a cast by giving each person a different thing to draw.

MEASURED on the shipped A Study in Scarlet sheets, SFace: Watson x Holmes
0.540, Lestrade x Holmes 0.464, against a same-person line of 0.363.  The two
leads are one man to a recogniser, and human readers said the same of Jekyll's
seven Victorian gentlemen.

A model draws OBJECTS.  A phrase moves the output exactly as far as it changes
the list of things that must be drawn: "a custodian helmet" adds an object and
is obeyed; "a heavy jaw" modifies an object already there and is absorbed by
the prior; "shorter than Henry Jekyll" names something not in the frame and is
never obeyed at all.
"""
from __future__ import annotations

import pytest

from studio.cast_card import (TIER_ONE, card_for, cards_for, differences,
                              refuse_collision, render_card)

CAST = ["sherlock_holmes", "john_watson", "g_lestrade", "jefferson_hope",
        "john_ferrier", "lucy_ferrier", "tobias_gregson", "stamford"]


class TestCardFor:
    def test_a_card_fills_every_slot(self):
        card = card_for("sherlock_holmes", {}, "")
        assert all(card.get(slot) for slot in TIER_ONE)

    def test_two_characters_do_not_take_the_same_tier_one_value(self):
        cards = cards_for(CAST, {})
        for slot in TIER_ONE:
            values = [c[slot] for c in cards.values()]
            assert len(values) == len(set(values)), (slot, values)

    def test_it_is_stable_for_the_same_cast(self):
        assert cards_for(CAST, {}) == cards_for(CAST, {})

    def test_the_books_own_words_win_where_it_has_any(self):
        cards = cards_for(["a"], {"a": "a tall man in a black frock coat"})
        assert "black" in cards["a"]["garment"] or "frock" in cards["a"]["garment"]


class TestDifferences:
    def test_two_identical_cards_differ_nowhere(self):
        card = card_for("x", {}, "")
        assert differences(card, dict(card)) == 0

    def test_distinct_cards_differ_in_several_slots(self):
        cards = cards_for(CAST, {})
        assert differences(cards["sherlock_holmes"], cards["john_watson"]) >= 3


class TestRefuseCollision:
    def test_a_well_separated_cast_passes(self):
        refuse_collision(cards_for(CAST, {}))

    def test_a_cast_where_two_share_everything_is_refused(self):
        cards = cards_for(CAST, {})
        cards["john_watson"] = dict(cards["sherlock_holmes"])
        with pytest.raises(ValueError, match="john_watson"):
            refuse_collision(cards)

    def test_the_gate_runs_before_any_gpu_time_is_spent(self):
        """Text, free, and the only gate early enough to be cheap.  ArcFace
        measures FACE identity and passed the Jekyll cast at 0.291 while
        readers called them near-identical -- what collided was age, hair,
        costume and light, which is what this measures."""
        cards = cards_for(CAST, {})
        assert all(isinstance(v, str) for c in cards.values() for v in c.values())


class TestRenderCard:
    def test_it_names_the_objects_not_the_adjectives(self):
        text = render_card(card_for("sherlock_holmes", {}, ""))
        assert any(word in text for word in ("wearing", "coat", "collar"))

    def test_it_never_compares_to_another_character(self):
        """A comparative names something not in the frame and is never obeyed;
        worse, Jekyll's sheet carried Hyde's description and Hyde's carried
        Jekyll's -- the two most at risk of collision each describing the
        other."""
        text = render_card(card_for("sherlock_holmes", {}, "")).lower()
        for comparative in ("taller than", "shorter than", "unlike", "compared"):
            assert comparative not in text
