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


# --- the bare-surname gap (2026-08-25) ---------------------------------------------
#
# The registry stores canonical names with titles ("Dr. John Watson") but prose says
# "Watson". `match_alias` correctly refuses — a one-word alias must match exactly — so
# 160 of 549 dialogue lines (29%) lost their speaker on the first real dossier run.
#
# The fallback must not reopen the 2026-08-23 hole. It is safe only because it is
# UNIQUENESS-CHECKED: a surname shared by two characters resolves to neither.

from studio import names

CAST = [
    {"id": "john_watson", "name": "Dr. John Watson", "aliases": ["I", "Dr. Watson"]},
    {"id": "sherlock_holmes", "name": "Sherlock Holmes", "aliases": ["my companion"]},
    {"id": "john_ferrier", "name": "John Ferrier", "aliases": []},
    {"id": "lucy_ferrier", "name": "Lucy Ferrier", "aliases": []},
]


def test_bare_surname_resolves_when_it_is_unique():
    index = names.build_surname_index(CAST)
    assert names.match_alias("Watson", index) == "john_watson"


def test_shared_surname_resolves_to_nobody():
    """Two Ferriers. Guessing between them would be worse than the gap."""
    index = names.build_surname_index(CAST)
    assert names.match_alias("Ferrier", index) is None


def test_full_name_without_the_title_resolves():
    index = names.build_surname_index(CAST)
    assert names.match_alias("John Watson", index) == "john_watson"


def test_surname_index_never_contains_a_title():
    index = names.build_surname_index(CAST)
    assert "dr" not in index and "mr" not in index


def test_surname_index_does_not_swallow_a_longer_phrase():
    """Still whole-word-exact for one-word keys: 'Watson' must not claim 'young Watson's
    landlady'. The rule that fixed the original bug is not relaxed here."""
    index = names.build_surname_index(CAST)
    assert names.match_alias("Watson's landlady", index) is None


def test_surname_index_is_only_a_fallback_not_a_replacement():
    """It carries surnames, not the alias vocabulary — callers try match_alias first."""
    index = names.build_surname_index(CAST)
    assert names.match_alias("my companion", index) is None
