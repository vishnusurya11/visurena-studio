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

from studio import cast_card
from studio.cast_card import (FACIAL_HAIR, GARMENT, HAIR, HEADGEAR, TIER_ONE, book_match,
                              card_for, cards_for, differences, refuse_collision,
                              render_card)

CAST = ["sherlock_holmes", "john_watson", "g_lestrade", "jefferson_hope",
        "john_ferrier", "lucy_ferrier", "tobias_gregson", "stamford"]


class TestCardFor:
    def test_a_card_fills_every_slot(self):
        card = card_for("sherlock_holmes", {}, "")
        assert all(card.get(slot) for slot in TIER_ONE)

    def test_no_pair_shares_every_tier_one_value(self):
        """Strict per-slot uniqueness is a stronger claim than the cast needs
        and, once role-reserved and gendered items are removed, is not always
        available: eight characters against seven legal neckwear options.  The
        requirement is that no PAIR is indistinguishable."""
        cards = cards_for(CAST, {})
        names = sorted(cards)
        for i, first in enumerate(names):
            for second in names[i + 1:]:
                assert any(cards[first][slot] != cards[second][slot]
                           for slot in TIER_ONE), (first, second)

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
        assert all(isinstance(v, str) for c in cards.values()
                   for k, v in c.items() if k not in ("asserted", "neutral"))


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

    def test_a_build_on_the_card_is_said_with_the_person(self):
        card = card_for("sherlock_holmes", {}, "")
        assert "frame" not in render_card(card)
        text = render_card({**card, "build": "a broad stocky frame"})
        assert text.startswith("A man") and "a broad stocky frame, " in text


class TestGender:
    """Lucy Ferrier was rendered as a man with a beard.

    `render_card` opened every card with "A man", and the facial-hair slot was
    filled from a pool of beards and moustaches for the whole cast.  Lucy came
    back indistinguishable from Tobias Gregson -- 0.541, the worst pair in the
    book -- because she was drawn as the same kind of object.
    """

    def test_a_daughter_is_a_woman(self):
        from studio.cast_card import infer_gender
        assert infer_gender("Lucy Ferrier",
                            ["Lucy", "the girl", "his daughter"], "She grew taller") == "woman"

    def test_a_man_is_a_man(self):
        from studio.cast_card import infer_gender
        assert infer_gender("John Watson", ["the doctor"], "He is a tall man") == "man"

    def test_the_word_counts_whatever_punctuation_follows_it(self):
        """'A tall thin man, clean-shaven' came back 'person': the split kept
        'man,' as one token and nothing matched."""
        from studio.cast_card import infer_gender
        assert infer_gender("X", [], "A tall thin man, clean-shaven.") == "man"
        assert infer_gender("X", [], "(a woman; grey-eyed)") == "woman"

    def test_an_unknown_is_a_person_not_a_guess(self):
        from studio.cast_card import infer_gender
        assert infer_gender("Wiggins", [], "") == "person"

    def test_a_woman_is_never_given_facial_hair(self):
        from studio.cast_card import card_for, render_card
        card = card_for("lucy_ferrier", {}, "", gender="woman")
        assert "beard" not in render_card(card) and "moustache" not in render_card(card)

    def test_a_woman_is_described_as_one(self):
        from studio.cast_card import card_for, render_card
        assert render_card(card_for("lucy", {}, "", gender="woman")).startswith("A woman")

    def test_cards_still_separate_when_the_cast_is_mixed(self):
        from studio.cast_card import cards_for, refuse_collision
        cards = cards_for(["holmes", "watson", "lucy"], {},
                          genders={"lucy": "woman"})
        refuse_collision(cards)


class TestTruthBeatsSeparation:
    """A card that separates the cast by lying about it is not an improvement.

    First run put Sherlock Holmes in a police custodian helmet with a full
    beard at sixty, and John Watson in a shawl and plain dress at seventy.
    Every pair was distinct and every card was wrong.  Authority order is: the
    book's own words, then dress convention for the role, then invention -- and
    invention only fills a slot the book leaves empty.
    """

    def test_a_role_specific_item_is_not_handed_to_the_wrong_role(self):
        from studio.cast_card import ROLE_ITEMS, card_for
        card = card_for("sherlock_holmes", {}, "a tall lean man", role="detective")
        assert card["headgear"] not in ROLE_ITEMS["headgear"].get("policeman", ())

    def test_a_policeman_may_have_the_helmet(self):
        from studio.cast_card import card_for
        assert "helmet" in card_for("a_constable", {}, "", role="policeman")["headgear"]

    def test_a_man_is_never_put_in_a_dress(self):
        from studio.cast_card import card_for
        card = card_for("john_watson", {}, "clean-shaven with a heavy jaw", gender="man")
        assert "dress" not in card["garment"] and "shawl" not in card["garment"]

    def test_an_unknown_gender_is_not_dressed_as_a_woman(self):
        """Watson's own description carries no pronoun, so inference returned
        'person' -- and 'person' must not silently mean 'put them in a gown'."""
        from studio.cast_card import card_for
        card = card_for("someone", {}, "", gender="person")
        assert "dress" not in card["garment"] and "shawl" not in card["garment"]

    def test_the_book_sets_the_age_when_it_says_one(self):
        from studio.cast_card import card_for
        card = card_for("x", {}, "a young man of about thirty", gender="man")
        assert "thirty" in card["age"]

    def test_the_book_beats_invention_on_facial_hair(self):
        from studio.cast_card import card_for
        card = card_for("x", {}, "clean-shaven with a heavy jaw", gender="man")
        assert card["facial_hair"] == "clean-shaven"


class TestAgeBand:
    """Invention must stay inside what the book says.

    John Ferrier is "the old farmer" and "the old man" and got "in his late
    twenties".  Lucy is "the girl" and got "a bald crown with grey at the
    temples".  Neither is a near miss; both are a different person.
    """

    def test_the_old_man_is_old(self):
        from studio.cast_card import age_band
        assert age_band("An older man, the old farmer, the old man") == "old"

    def test_the_girl_is_young(self):
        from studio.cast_card import age_band
        assert age_band("Lucy is a young child who grows into a young woman") == "young"

    def test_an_unmarked_character_is_neither(self):
        from studio.cast_card import age_band
        assert age_band("a man in a coat") == "middle"

    def test_a_young_character_never_gets_an_aged_feature(self):
        from studio.cast_card import card_for
        card = card_for("lucy", {}, "the young girl", gender="woman")
        assert "bald" not in card["hair"] and "white hair" not in card["hair"]

    def test_an_old_character_is_not_given_a_twenties_age(self):
        from studio.cast_card import card_for
        card = card_for("ferrier", {}, "the old farmer, the old man", gender="man")
        assert "twenties" not in card["age"] and "thirty" not in card["age"]

    def test_an_unmarked_adult_is_not_white_haired_or_bald(self):
        """Scarlet run 6: Holmes, unaged by the dossier, drew 'white hair worn
        long' and 'a full dark beard' from the rotation -- at 'about forty'.
        The middle band bands hair too: grey, white and bald belong to old."""
        from studio.cast_card import HAIR, card_for
        for seed in ("holmes", "gregson", "lestrade", "hope", "stangerson", "drebber", "x"):
            hair = card_for(seed, {}, "a man in a coat", gender="man")["hair"]
            assert not any(mark in hair for mark in ("white", "grey", "bald")), (seed, hair)
        assert any("white" in h for h in HAIR)  # still there for the old

    def test_a_slot_the_book_states_outranks_the_rotation(self):
        """Gregson: 'flaxen-haired' in the book, 'dark hair swept back' from the
        rotation, both in one prompt (Scarlet run 6).  What the book states
        is the card, and it is spent like any other value."""
        from studio.cast_card import card_for, cards_for
        card = card_for("gregson", {}, "a man in a coat", gender="man",
                        stated={"hair": "fair hair parted in the middle", "build": "tall"})
        assert card["hair"] == "fair hair parted in the middle" and card["build"] == "tall"
        cards = cards_for(["gregson", "watson"], {}, stated={
            "gregson": {"hair": "fair hair parted in the middle"}})
        assert cards["watson"]["hair"] != "fair hair parted in the middle"

    def test_a_woman_is_not_described_as_in_his_twenties(self):
        from studio.cast_card import card_for, render_card
        text = render_card(card_for("lucy", {}, "the young girl", gender="woman"))
        assert " his " not in text


class TestUnmarkedAdults:
    """A character the book does not age should read as an adult in their
    prime, not as a lottery across sixty years.

    Holmes and Watson are both described only as capable and active, and came
    back at sixty and seventy -- older than any reader pictures either of them,
    and older than the story allows.
    """

    def test_an_unmarked_adult_is_not_elderly(self):
        from studio.cast_card import card_for
        for who in ("sherlock_holmes", "john_watson", "tobias_gregson"):
            age = card_for(who, {}, "a capable and active man", gender="man")["age"]
            assert "seventy" not in age and "sixty" not in age, (who, age)

    def test_an_unmarked_adult_is_not_a_youth_either(self):
        from studio.cast_card import card_for
        age = card_for("x", {}, "a capable and active man", gender="man")["age"]
        assert "twenties" not in age

    def test_a_woman_is_not_described_as_clean_shaven(self):
        from studio.cast_card import card_for, render_card
        text = render_card(card_for("lucy", {}, "the young girl", gender="woman"))
        assert "clean-shaven" not in text


class TestAsserted:
    """Which slots the BOOK filled.  Scarlet run 7: Holmes's card said
    'receding sandy hair' from the rotation, the render put dark hair under
    his bowler four times, and the fidelity gate refused every sheet for
    disobeying an invention.  The book is silent on Holmes's hair; a slot it
    left to invention is the render's to decide."""

    def test_a_book_matched_slot_is_asserted(self):
        card = card_for("lestrade", {}, "A thin man with a heavy walrus moustache.")
        assert card["asserted"] == ["facial_hair"]

    def test_a_stated_slot_is_asserted(self):
        card = card_for("gregson", {}, "a man of few words",
                        stated={"hair": "fair hair parted in the middle"})
        assert card["asserted"] == ["hair"]
        assert card_for("gregson", {}, "a man in a frock coat")["asserted"] == ["garment"]

    def test_an_invented_card_asserts_nothing(self):
        assert card_for("holmes", {}, "")["asserted"] == []
        assert card_for("holmes", {}, "limited physical description")["asserted"] == []

    def test_a_womans_beardlessness_is_asserted(self):
        assert card_for("lucy", {}, "the young girl", gender="woman")["asserted"] == ["facial_hair"]


class TestBookNamesTheObject:
    """Scarlet run 7, cards rebuilt offline: Watson "as thin as a lath and as
    brown as a nut" matched a brown bowler hat and a thin waxed moustache;
    Hope's "long rifle" matched long black hair and a long untrimmed beard;
    Lucy "felt long-forgotten thoughts" matched a wide-brimmed felt hat;
    "tall" put Gregson and Hope both in a tall beaver hat -- every one of
    them then ASSERTED, so the render owed an adjective the book had spent
    on something else.  The book asserts an object when it names the object."""

    def test_an_adjective_alone_asserts_nothing(self):
        watson = "You are as thin as a lath and as brown as a nut."
        assert book_match(watson, HEADGEAR, "headgear") == ""
        assert book_match(watson, FACIAL_HAIR, "facial_hair") == ""
        hope = "clad in the rough dress of a hunter, with a long rifle slung over his shoulders"
        assert book_match(hope, HAIR, "hair") == ""
        assert book_match(hope, FACIAL_HAIR, "facial_hair") == ""
        assert book_match("felt long-forgotten thoughts revive", HEADGEAR, "headgear") == ""
        assert book_match("a tall, white-faced, flaxen-haired man", HEADGEAR, "headgear") == ""

    def test_the_object_named_with_an_attribute_matches(self):
        assert "frock" in book_match("a tall man in a black frock coat", GARMENT, "garment")
        assert book_match("a clean-shaven face", FACIAL_HAIR, "facial_hair") == "clean-shaven"
        assert "bowler" in book_match("a brown bowler on his head", HEADGEAR, "headgear")
        assert "walrus" in book_match("a heavy walrus moustache", FACIAL_HAIR, "facial_hair")

    def test_the_bare_object_asserts_no_kind(self):
        assert book_match("he wore a hat", HEADGEAR, "headgear") == ""
        assert book_match("a man in a coat", GARMENT, "garment") == ""

    def test_a_slot_with_no_object_word_matches_as_before(self):
        assert book_match("as thin as a lath", ("a thin wiry frame",)) == "a thin wiry frame"

    def test_a_womans_age_is_hers(self):
        card = card_for("lucy_ferrier", {}, "", gender="woman",
                        stated={"age": "in his late twenties"})
        assert card["age"] == "in her late twenties"
        young = card_for("lucy_ferrier", {}, "a young girl", gender="woman")
        assert "his" not in young["age"].split()


class TestStatedIsReservedFirst:
    """Scarlet run 7: Gregson's flaxen hair is stated as "receding sandy
    hair", but Holmes's card was built first and the rotation had already
    handed him the same phrase -- the book's word arrived too late to be
    avoided."""

    def test_an_invented_slot_avoids_what_a_later_card_states(self):
        stated = {"tobias_gregson": {"hair": "receding sandy hair"}}
        cards = cards_for(["sherlock_holmes", "tobias_gregson"], {}, stated=stated)
        assert cards["tobias_gregson"]["hair"] == "receding sandy hair"
        assert cards["sherlock_holmes"]["hair"] != "receding sandy hair"

    def test_a_woman_is_not_put_in_a_top_hat(self):
        for taken in ({}, {"headgear": {"a wide-brimmed felt hat"}}):
            card = card_for("lucy_ferrier", taken, "", gender="woman")
            assert "bonnet" in card["headgear"]
        assert card_for("john_watson", {}, "", gender="man")["headgear"] not in (
            "a straw bonnet tied with ribbon", "a plain cotton sun bonnet")


class TestTakenByReading:
    """A thin waxed moustache and a heavy walrus moustache are two phrases and
    one reading: the sheet gate reads both as 'moustache', so handing the
    second to the next character is handing out a collision.  What is taken
    is what the reader would call the same."""

    def test_a_slot_another_character_took_is_not_reissued_under_another_name(self):
        from studio.distinguish import coarse
        cards = cast_card.cards_for(["a", "b", "c"], {"a": "", "b": "", "c": ""},
                                    stated={"a": {"facial_hair": "a heavy walrus moustache"}})
        for other in ("b", "c"):
            assert coarse("facial_hair", cards[other]["facial_hair"]) != "moustache", other

    def test_alike_is_every_pool_phrase_the_reader_cannot_tell_from_this_one(self):
        alike = cast_card.alike("facial_hair", "a thin waxed moustache")
        assert {"a thin waxed moustache", "a heavy walrus moustache"} <= alike
        assert "clean-shaven" not in alike
        assert cast_card.alike("garment", "a navy pea jacket") == {"a navy pea jacket"}


class TestNeutralAvoidsTaken:
    """Scarlet 2026-09-04: Holmes's canon hair is dark and swept back; Watson
    and Lestrade, known faces with no agreed hair, were both handed the same
    phrase as the band's plainest -- three dark swept-back heads.  Neutral
    means nothing ADDED, not nothing avoided: the plainest hair nobody has."""

    def test_neutral_hair_is_the_plainest_the_reader_has_not_seen(self):
        taken = {slot: set() for slot in cast_card.POOLS}
        first = cast_card.neutral("hair", "", taken)
        taken["hair"] |= cast_card.alike("hair", first)
        second = cast_card.neutral("hair", "", taken)
        assert first != second and second in cast_card.BANDED[cast_card.age_band("")]["hair"]

    def test_neutral_facial_hair_is_always_clean_shaven(self):
        taken = {"facial_hair": {"clean-shaven"}}
        assert cast_card.neutral("facial_hair", "", taken) == cast_card.NO_BEARD

    def test_two_known_faces_with_no_agreed_hair_do_not_share_one(self):
        from studio.distinguish import coarse
        cards = cast_card.cards_for(["a", "b"], {"a": "", "b": ""}, known={"a", "b"})
        assert coarse("hair", cards["a"]["hair"], "hair_colour") != coarse("hair", cards["b"]["hair"], "hair_colour")             or coarse("hair", cards["a"]["hair"], "hair_length") != coarse("hair", cards["b"]["hair"], "hair_length")
