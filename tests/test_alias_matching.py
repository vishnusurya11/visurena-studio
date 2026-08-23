"""Aliases resolve by WORDS, never by letters.

Regression suite for the 2026-08-23 audit: `_match` used raw substring containment, so
"me" matched inside "medical", "men" inside "regiment" and "government", and the
narrator's one-letter alias "i" matched any form containing the letter i. 298 of this
book's 902 character references — a third — were assigned to the wrong person, silently
and with full confidence.
"""

from __future__ import annotations

from scripts.analysis import step_03_standardize as s03

REGISTRY = {
    "characters": [
        {"id": "john_watson", "name": "Dr. John Watson",
         "aliases": ["I", "me", "my friend", "the narrator"]},
        {"id": "informants", "name": "Street informants",
         "aliases": ["men", "the men", "our informant"]},
        {"id": "brigham_young", "name": "Brigham Young", "aliases": ["Young"]},
        {"id": "jefferson_hope", "name": "Jefferson Hope",
         "aliases": ["the cabman", "our prisoner"]},
    ],
    "locations": [
        {"id": "baker_street_221b", "name": "221B Baker Street",
         "aliases": ["the sitting-room", "our lodgings"]},
    ],
}


def _chars():
    return s03.build_alias_index(REGISTRY)[0]


def _locs():
    return s03.build_alias_index(REGISTRY)[1]


# --- what must still work ----------------------------------------------------------

def test_an_exact_alias_still_resolves():
    assert s03._match("I", _chars()) == "john_watson"
    assert s03._match("the cabman", _chars()) == "jefferson_hope"


def test_a_multi_word_alias_still_matches_inside_a_longer_form():
    assert s03._match("the sitting-room, 221B Baker Street",
                      _locs()) == "baker_street_221b"


def test_the_longest_matching_alias_wins():
    index = {"baker street": "street", "221b baker street": "house"}
    assert s03._match("we returned to 221B Baker Street", index) == "house"


# --- the letter-soup regressions ---------------------------------------------------

def test_me_does_not_match_inside_medical():
    assert s03._match("a medical board", _chars()) is None


def test_men_does_not_match_inside_regiment_or_government():
    assert s03._match("my regiment", _chars()) is None
    assert s03._match("a paternal government", _chars()) is None


def test_men_does_not_match_inside_women():
    assert s03._match("women", _chars()) is None


def test_the_narrators_one_letter_alias_does_not_swallow_the_alphabet():
    for form in ["a logician", "the writer", "Lefevre of Montpellier",
                 "private inquiry agencies", "a railway porter", "Von Bischoff"]:
        assert s03._match(form, _chars()) is None, form


def test_a_surname_does_not_match_the_same_word_used_plainly():
    assert s03._match("a young girl", _chars()) is None
    assert s03._match("Brigham Young", _chars()) == "brigham_young"


def test_a_one_word_alias_never_matches_by_containment():
    """The rule that kills the whole class: one word resolves only by being the form."""
    assert s03._match("men", _chars()) == "informants"      # it IS the form
    assert s03._match("the two men", _chars()) is None      # it merely contains it


def test_an_unmatched_form_stays_unmatched():
    """A walk-on with no canonical identity is a gap, and a gap is the honest answer."""
    assert s03._match("a slip-shod elderly woman", _chars()) is None
